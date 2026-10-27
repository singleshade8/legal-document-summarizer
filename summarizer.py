"""Core extractive summarisation engine (pure Python, works offline).

Pipeline
--------
1. detect_language()   - Unicode-script based (en / hi / ta / te / kn / ml / bn / gu / pa)
2. split_sentences()   - handles legal abbreviations (Sec., No., Cr.P.C., Hon'ble ...) and the
                         Devanagari danda "।"
3. rank_sentences()    - TF-IDF sentence vectors -> TextRank (PageRank on the similarity graph)
                         combined with legal cue words, position and legal-entity features
4. select + group      - redundancy filter, always keep the operative "order" sentence, then
                         group into Facts / Arguments / Findings / Order
"""
import math
import re
from collections import Counter, defaultdict

from lexicon import (
    ARGUMENT_CUES, FINDING_CUES, LANG_NAMES, ORDER_CUES, SCRIPT_RANGES,
    SECTION_TITLES, STOPWORDS,
)

PH = ""  # placeholder for protected full stops

# Map Indic digits to ASCII so numbers/dates are matched uniformly.
_DIGIT_MAP = {}
for _start in (0x0966, 0x09E6, 0x0A66, 0x0AE6, 0x0BE6, 0x0C66, 0x0CE6, 0x0D66):
    for _i in range(10):
        _DIGIT_MAP[_start + _i] = ord("0") + _i


def normalize_digits(text: str) -> str:
    return text.translate(_DIGIT_MAP)


# --------------------------------------------------------------------------- language
def detect_language(text: str) -> str:
    """Return a language code based on which script dominates the text."""
    sample = text[:30000]
    counts = Counter()
    latin = 0
    for ch in sample:
        cp = ord(ch)
        if (65 <= cp <= 90) or (97 <= cp <= 122):
            latin += 1
            continue
        if cp < 0x0900:
            continue
        for code, (lo, hi) in SCRIPT_RANGES.items():
            if lo <= cp <= hi:
                counts[code] += 1
                break
    if counts:
        code, n = counts.most_common(1)[0]
        # Court documents are often bilingual; Indic script wins if it is a real share.
        if n > latin * 0.3:
            return code
    return "en"


# --------------------------------------------------------------------------- sentences
_ABBR = (
    "Mr|Mrs|Ms|Dr|Smt|Shri|Sri|Sh|Kum|vs|v|No|Nos|Sec|Secs|Cr|Crl|Cri|Co|Ltd|Pvt|St|Ex|Exh|Dt|"
    "Addl|Dy|Asst|Jr|Sr|Rs|Art|Ors|Anr|Viz|etc|Ch|Vol|Hon|Mst|Prof|Col|Capt|Gen|Adv|Dist|Km|Cl|Sub"
)
_RE_ABBR = re.compile(rf"\b(?:{_ABBR})\.", re.I)
_RE_INITIAL = re.compile(r"\b([A-Z])\.(?=\s?[A-Z])")
_RE_DOTTED = re.compile(r"\b([A-Za-z]{1,3})\.(?=[A-Za-z]{1,3}\b)")
_RE_INDIC_ABBR = re.compile(r"(?<!\S)(?:ரூ|रु|रू)\.")
_RE_NUMBERED = re.compile(r"^\s*\(?(\d{1,3})[\.\)]\s+")
_RE_SPLIT = re.compile(r'(?<=[.!?।॥])\s+|(?<=[.!?।॥]["”’\)])\s+')
_TERMINAL = tuple(".!?।॥:\"”’)")


def _protect(par: str) -> str:
    par = _RE_NUMBERED.sub(lambda m: m.group(1) + PH + " ", par)
    par = _RE_ABBR.sub(lambda m: m.group(0)[:-1] + PH, par)
    par = _RE_INDIC_ABBR.sub(lambda m: m.group(0)[:-1] + PH, par)
    par = _RE_INITIAL.sub(lambda m: m.group(1) + PH, par)
    par = _RE_DOTTED.sub(lambda m: m.group(1) + PH, par)
    return par


def _paragraphs(text: str):
    """Re-join hard-wrapped lines (typical for PDF text) but keep headings separate."""
    lines = [l.strip() for l in text.replace("\r", "").split("\n")]
    lens = sorted(len(l) for l in lines if l)
    if not lens:
        return []
    ref = lens[int(len(lens) * 0.75)]
    paras, cur, prev = [], [], ""
    for line in lines:
        if not line:
            if cur:
                paras.append(" ".join(cur))
                cur = []
            prev = ""
            continue
        if cur and (prev.endswith(_TERMINAL) or len(prev) < 0.6 * ref):
            paras.append(" ".join(cur))
            cur = []
        cur.append(line)
        prev = line
    if cur:
        paras.append(" ".join(cur))
    return paras


def split_sentences(text: str):
    """Split a legal document into sentences. Returns a list of clean strings."""
    out = []
    for par in _paragraphs(text):
        for s in _RE_SPLIT.split(_protect(par)):
            s = s.replace(PH, ".").strip()
            s = re.sub(r"^\(?\d{1,3}[\.\)]\s+", "", s)  # drop paragraph numbering
            s = re.sub(r"\s+", " ", s)
            if len(s.split()) >= 5:
                out.append(s)
    return out


# --------------------------------------------------------------------------- features
_TOKEN_RE = re.compile(r"[^\s\.,;:!?()\[\]{}\"'“”‘’।॥\-–—/|]+")
_EN_SUFFIXES = ("ing", "edly", "ed", "es", "ly", "s")


def _stem(tok: str, lang: str) -> str:
    if lang == "en":
        for suf in _EN_SUFFIXES:
            if tok.endswith(suf) and len(tok) - len(suf) >= 4:
                return tok[: -len(suf)]
        return tok
    # Hindi / Tamil / other Indic: agglutinative or inflected -> use a fixed-length prefix
    return tok[:6] if len(tok) > 6 else tok


def tokenize(text: str, lang: str):
    stop = STOPWORDS.get(lang, set())
    out = []
    for t in _TOKEN_RE.findall(normalize_digits(text).lower()):
        if t in stop or len(t) < 2 or t.isdigit():
            continue
        out.append(_stem(t, lang))
    return out


def _cue_hits(sentence: str, cues, lang: str) -> int:
    s = sentence.lower()
    words = cues.get(lang, []) + (cues["en"] if lang != "en" else [])
    return sum(1 for w in words if w in s)


_RE_LEGAL_ENTITY = re.compile(
    r"(?:section|sec\.|धारा|பிரிவு|\bact\b|अधिनियम|சட்டம்|rs\.?\s?\d|₹|रु\.?\s?\d|ரூ\.?\s?\d|\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})",
    re.I,
)


def _tfidf(sent_tokens):
    n = len(sent_tokens)
    df = Counter()
    for toks in sent_tokens:
        df.update(set(toks))
    vecs, norms = [], []
    for toks in sent_tokens:
        tf = Counter(toks)
        v = {t: (1 + math.log(c)) * (math.log((n + 1) / (df[t] + 1)) + 1) for t, c in tf.items()}
        vecs.append(v)
        norms.append(math.sqrt(sum(w * w for w in v.values())) or 1.0)
    return vecs, norms, df


def _similarity_graph(vecs, norms, df):
    n = len(vecs)
    inv = defaultdict(list)
    for i, v in enumerate(vecs):
        for t, w in v.items():
            inv[t].append((i, w))
    adj = [defaultdict(float) for _ in range(n)]
    for t, plist in inv.items():
        if n > 50 and df[t] > 0.4 * n:  # near stop-words; skip to keep graph sparse
            continue
        for a in range(len(plist)):
            i, wi = plist[a]
            for b in range(a + 1, len(plist)):
                j, wj = plist[b]
                adj[i][j] += wi * wj
                adj[j][i] += wi * wj
    for i in range(n):
        for j in adj[i]:
            adj[i][j] /= norms[i] * norms[j]
    return adj


def _textrank(adj, damping=0.85, iters=40):
    n = len(adj)
    out_sum = [sum(a.values()) for a in adj]
    score = [1.0 / n] * n
    for _ in range(iters):
        new = []
        for i in range(n):
            s = sum(w / out_sum[j] * score[j] for j, w in adj[i].items() if out_sum[j] > 0)
            new.append((1 - damping) / n + damping * s)
        score = new
    return score


def _norm(values):
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [0.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def rank_sentences(sentences, lang):
    """Return (final_scores, adjacency). Higher score = more important."""
    n = len(sentences)
    tokens = [tokenize(s, lang) for s in sentences]
    vecs, norms, df = _tfidf(tokens)
    adj = _similarity_graph(vecs, norms, df)
    tr = _norm(_textrank(adj))

    cue = _norm([min(3, _cue_hits(s, ORDER_CUES, lang) + _cue_hits(s, FINDING_CUES, lang)) for s in sentences])
    ent = [1.0 if _RE_LEGAL_ENTITY.search(normalize_digits(s)) else 0.0 for s in sentences]

    pos = []
    for i in range(n):
        r = i / max(1, n - 1)
        pos.append(1.0 if r >= 0.88 else 0.7 if r <= 0.08 else 0.2)  # operative order + opening facts

    # length penalty: very short / very long sentences make poor summary lines
    ln = []
    for s in sentences:
        w = len(s.split())
        ln.append(1.0 if 10 <= w <= 45 else 0.5 if w < 10 else 0.6)

    final = [
        (0.45 * tr[i] + 0.25 * cue[i] + 0.15 * pos[i] + 0.15 * ent[i]) * ln[i]
        for i in range(n)
    ]
    return final, adj


def classify_sentence(sentence: str, lang: str, rel_pos: float = 1.0) -> str:
    """Facts / Arguments / Findings / Order. Order cues only count in the later part of the text."""
    o = _cue_hits(sentence, ORDER_CUES, lang) if rel_pos >= 0.55 else 0
    f = _cue_hits(sentence, FINDING_CUES, lang)
    a = _cue_hits(sentence, ARGUMENT_CUES, lang)
    best = max(("Findings", f), ("Order", o), ("Arguments", a), key=lambda x: x[1])  # ties -> Findings
    return best[0] if best[1] > 0 else "Facts"


# Explicit section headings are strong structural evidence. They are used only
# when they appear in the later part of the judgment on a standalone line.
_OPERATIVE_HEADING_RE = re.compile(
    r"(?im)^\\s*(?:"
    r"CONCLUSION\\s+(?:AND|&)\\s+DIRECTIONS?|"
    r"OPERATIVE\\s+(?:PART|PORTION|ORDER)|FINAL\\s+ORDER|"
    r"(?:GENERAL\\s+)?DIRECTIONS?|ORDER|CONCLUSION|DISPOSITION|"
    r"अंतिम\\s+आदेश|न्यायालय\\s+के\\s+निर्देश|निर्देश|आदेश|निष्कर्ष|"
    r"இறுதி\\s+உத்தரவு|உத்தரவு|வழிகாட்டுதல்கள்|முடிவு"
    r")\\s*[:\\-–—]?\\s*$"
)
_OPERATIVE_ACTION_RE = re.compile(
    r"\\b(?:shall|must|we direct|directed to|is directed|it is ordered|"
    r"hereby ordered|is hereby allowed|is hereby dismissed)\\b",
    re.I,
)


def _operative_start_index(text: str, sentence_count: int) -> int | None:
    """Find the first late standalone operative heading, if one is explicit."""
    if not text or sentence_count == 0:
        return None
    min_offset = int(len(text) * 0.35)
    for match in _OPERATIVE_HEADING_RE.finditer(text):
        if match.start() < min_offset:
            continue
        boundary = len(split_sentences(text[:match.start()]))
        if boundary < sentence_count:
            return boundary
    return None


# --------------------------------------------------------------------------- main API
def summarize(text: str, ratio: float = 0.25, min_sentences: int = 3, max_sentences: int = 15,
              lang: str | None = None):
    """Summarise `text`. Returns a dict with selected sentences grouped by section."""
    text = text.strip()
    lang = lang or detect_language(text)
    sentences = split_sentences(text)
    n = len(sentences)
    if n == 0:
        return {"lang": lang, "n_sentences": 0, "selected": [], "sections": []}

    k = max(min_sentences, min(max_sentences, round(ratio * n)))
    k = min(k, n)
    scores, adj = rank_sentences(sentences, lang) if n > 1 else ([1.0], [defaultdict(float)])

    # Prefer explicit late operative headings; fallback to a cue in the last quarter.
    forced_order = []
    operative_start = _operative_start_index(text, n)
    if operative_start is not None:
        operative_candidates = [
            i for i in range(operative_start, n)
            if _cue_hits(sentences[i], ORDER_CUES, lang)
            or (lang == "en" and _OPERATIVE_ACTION_RE.search(sentences[i]))
        ]
        if not operative_candidates:
            operative_candidates = [operative_start]
        # Preserve several operative directions when the requested summary budget allows it.
        budget = min(5, max(1, k))
        forced_order = sorted(
            operative_candidates, key=lambda i: scores[i], reverse=True
        )[:budget]
    else:
        tail_start = int(n * 0.75)
        cands = [(scores[i], i) for i in range(tail_start, n)
                 if _cue_hits(sentences[i], ORDER_CUES, lang)]
        if cands:
            forced_order = [max(cands)[1]]

    chosen = list(forced_order)
    for i in sorted(range(n), key=lambda x: scores[x], reverse=True):
        if len(chosen) >= k:
            break
        if i in chosen:
            continue
        if any(adj[i].get(j, 0) > 0.6 for j in chosen):  # redundant with a chosen sentence
            continue
        chosen.append(i)
    chosen.sort()

    grouped = {"Facts": [], "Arguments": [], "Findings": [], "Order": []}
    for i in chosen:
        grouped[classify_sentence(sentences[i], lang, i / n)].append(sentences[i])
    # Every explicitly prioritised operative line belongs in the Order section,
    # even if a generic findings cue would otherwise win classification.
    for forced_idx in forced_order:
        forced_sentence = sentences[forced_idx]
        for key in ("Facts", "Arguments", "Findings"):
            if forced_sentence in grouped[key]:
                grouped[key].remove(forced_sentence)
        if forced_sentence not in grouped["Order"]:
            grouped["Order"].append(forced_sentence)

    titles = SECTION_TITLES.get(lang, SECTION_TITLES["en"])
    sections = [
        {"key": key, "title": titles[key], "sentences": grouped[key]}
        for key in ("Facts", "Arguments", "Findings", "Order") if grouped[key]
    ]
    return {
        "lang": lang,
        "lang_name": LANG_NAMES.get(lang, lang),
        "n_sentences": n,
        "selected": [sentences[i] for i in chosen],
        "sections": sections,
    }
