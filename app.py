"""Flask web app: Multilingual Legal Document Summarizer for District Court e-Services."""
import os
import re

from flask import Flask, jsonify, render_template, request

from extractors import ExtractionError, extract_text
from legal_info import extract_key_info
from lexicon import INFO_LABELS, LANG_NAMES, OUTCOME_TEXT, SECTION_TITLES, SECTION_WORD
from summarizer import summarize
from translator import translate_sentences, translation_available

APP_VERSION = "1.3"
BASE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = {
    "english": ("English – Cheque dishonour (S.138 NI Act)", "sample_english.txt"),
    "hindi": ("हिन्दी – जमानत आवेदन (धारा 439)", "sample_hindi.txt"),
    "tamil": ("தமிழ் – பணம் மீட்பு வழக்கு", "sample_tamil.txt"),
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB uploads


def _info_rows(info: dict, lang: str):
    """Turn the key-info dict into labelled rows in the given language."""
    labels = INFO_LABELS.get(lang, INFO_LABELS["en"])
    rows = []
    for key in ("case_numbers", "court", "parties", "judge", "dates", "sections", "outcome"):
        val = info.get(key)
        if not val:
            continue
        if key == "outcome":
            val = OUTCOME_TEXT.get(val, {}).get(lang, val)
        elif key == "sections":
            word = SECTION_WORD.get(lang, "Section")
            val = "; ".join(re.sub(r"^Section ", word + " ", v) for v in val)
        elif isinstance(val, list):
            val = "; ".join(val) if key != "parties" else "  vs  ".join(val)
        rows.append({"label": labels[key], "value": val})
    return rows


def build_result(text: str, ratio: float = 0.25, out_lang: str = "same"):
    text = text.strip()
    res = summarize(text, ratio=ratio)
    lang = res["lang"]
    info = extract_key_info(text)

    words_in = len(text.split())
    summary_text = " ".join(res["selected"])
    words_out = len(summary_text.split())
    payload = {
        "language": {"code": lang, "name": LANG_NAMES.get(lang, lang)},
        "stats": {
            "sentences_total": res["n_sentences"],
            "sentences_selected": len(res["selected"]),
            "words_original": words_in,
            "words_summary": words_out,
            "reduction_percent": round(100 * (1 - words_out / words_in)) if words_in else 0,
        },
        "key_info": _info_rows(info, lang),
        "sections": res["sections"],
        "summary_text": summary_text,
        "translation": None,
    }

    if out_lang not in ("same", lang):
        # translate section by section so the structure survives
        flat = [s for sec in res["sections"] for s in sec["sentences"]]
        translated, err, provider = translate_sentences(flat, lang, out_lang)
        tr = {"target": out_lang, "target_name": LANG_NAMES.get(out_lang, out_lang), "error": err, "provider": provider}
        if translated is not None:
            it = iter(translated)
            titles = SECTION_TITLES.get(out_lang, SECTION_TITLES["en"])
            tr["sections"] = [
                {"key": sec["key"], "title": titles[sec["key"]], "sentences": [next(it) for _ in sec["sentences"]]}
                for sec in res["sections"]
            ]
            tr["key_info"] = _info_rows(info, out_lang)
            tr["summary_text"] = " ".join(translated)
        payload["translation"] = tr
    return payload


@app.get("/")
def index():
    return render_template("index.html", samples=[{"id": k, "label": v[0]} for k, v in SAMPLES.items()],
                           translation_ready=translation_available(), version=APP_VERSION)


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION, translation=translation_available())


@app.get("/api/samples/<name>")
def sample(name):
    if name not in SAMPLES:
        return jsonify(error="Unknown sample"), 404
    with open(os.path.join(BASE, "samples", SAMPLES[name][1]), encoding="utf-8") as fh:
        return jsonify(text=fh.read())


@app.post("/api/summarize")
def api_summarize():
    text = ""
    upload = request.files.get("file")
    try:
        if upload and upload.filename:
            text = extract_text(upload.filename, upload.read())
        else:
            text = request.form.get("text") or (request.get_json(silent=True) or {}).get("text", "")
    except ExtractionError as exc:
        return jsonify(error=str(exc)), 400

    if len(text.split()) < 30:
        return jsonify(error="Please provide a longer document (at least ~30 words)."), 400

    src = request.form if request.form else (request.get_json(silent=True) or {})
    try:
        ratio = min(0.6, max(0.05, float(src.get("ratio", 0.25))))
    except (TypeError, ValueError):
        ratio = 0.25
    out_lang = re.sub(r"[^a-z\-]", "", str(src.get("out_lang", "same")).lower()) or "same"
    return jsonify(build_result(text, ratio, out_lang))


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File too large (limit 10 MB)."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
