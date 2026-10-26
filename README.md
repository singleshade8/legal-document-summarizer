# Nyaya Saar – Multilingual Legal Document Summarizer (District Court e-Services)

A working web application that summarises court judgments / orders written in **English, Hindi and Tamil**
and extracts the key legal details (case number, court, parties, dates, sections/Acts, outcome).
Summarisation runs **fully offline** – no API key, no model download.

## 1. Run it (2 minutes)

```bash
pip install -r requirements.txt        # Python 3.9+
python app.py                          # open http://localhost:5000
```
Click one of the three sample judgments, press **Summarise**. You can also paste text or upload PDF / DOCX / TXT.

Run the tests: `python -m unittest discover -s tests -v` (32 tests).

### Cross-language output (the *Output language* dropdown)
The summary of a document in its **own language always works offline**.

**The three sample judgments are pre-translated between all three languages** (English, Hindi, Tamil - 6 pairs,
stored in `translation_cache.json`), so the demo needs **no internet and no extra packages**.
(Rebuild with `python build_sample_cache.py`.)

For **your own documents** the app uses free online services, tried in turn: Google (gtx) -> Google via
`deep-translator` (if installed) -> three Lingva mirrors -> MyMemory. All use only the Python standard library.
To survive "too many requests" the app sends the whole summary in **one** request, spaces calls out, retries briefly,
falls back to the next service, and **saves every translation** to `translation_cache.json` so it is never requested
twice. If everything is busy you keep the original-language summary and see a "wait a minute and try again" notice.
Optional offline engine (`argostranslate`, see `install_offline_translation.py`) is fragile on some Windows /
Python 3.12 setups and is **not needed**.

### Download as PDF
After summarising, **Download PDF** opens the browser's print dialog with a clean report layout (title, key details,
summary, disclaimer). Choose **Save as PDF** as the destination. Hindi and Tamil print correctly because the browser
uses your system fonts. The file name is taken from the case number. The footer of the page shows the app version.

## 2. How it works

| Stage | File | Technique |
|---|---|---|
| Text extraction | `extractors.py` | pypdf (PDF), python-docx (DOCX), TXT with encoding fallback; scanned PDFs are detected and reported |
| Language detection | `summarizer.py` | Unicode-script counting (Latin / Devanagari / Tamil / other Indic) – robust for short and mixed court text |
| Sentence splitting | `summarizer.py` | Rule-based; protects legal abbreviations (Mr., Sec., No., Cr.P.C., N.I. Act, Hon'ble, ரூ., रु.), paragraph numbering, Devanagari danda `।` |
| Sentence ranking | `summarizer.py` | TF-IDF vectors -> cosine similarity graph -> **TextRank** (PageRank). Final score = 0.45 TextRank + 0.25 legal cue words + 0.15 position + 0.15 legal entities (sections, dates, amounts), with a sentence-length penalty |
| Selection | `summarizer.py` | Redundancy filter (similarity > 0.6 skipped); the best **operative-order sentence** from the last 25 % is always included; output kept in document order |
| Structuring | `summarizer.py` | Each sentence grouped into Facts / Arguments / Court's Findings / Order using multilingual cue words (position-aware) |
| Key details | `legal_info.py` | Regex + dictionaries: case no., court, parties (`vs` / बनाम / எதிர்), dates, "Section N" linked to the nearest known Act, outcome (Convicted, Dismissed, Bail granted, Decreed ...) |
| Localisation | `lexicon.py` | Section titles, labels and outcome names in English / Hindi / Tamil; Indic digits normalised |
| Translation | `translator.py` | Optional: Argos (offline) -> Google -> MyMemory, batching, retry/back-off, disk cache, graceful failure |
| Web app | `app.py`, `templates/index.html` | Flask JSON API (`POST /api/summarize`) + single-page UI |

Why extractive and rule-based? Court e-services need **traceable output**: every summary line is a verbatim
sentence from the judgment, so nothing can be hallucinated. It is also fast, private (documents never leave
the server) and runs on a low-cost server.

## 3. API

`POST /api/summarize` – multipart form: `file` **or** `text`, `ratio` (0.05–0.6, default 0.25), `out_lang` (`same|en|hi|ta`).
Returns `language`, `stats`, `key_info`, `sections`, `summary_text`, `translation`.

## 4. Limitations (mention these in your report)
* Extractive: no paraphrasing; Hindi/Tamil stemming is a simple prefix heuristic, not a full morphological analyser.
* Scanned PDFs need OCR first (Tesseract `eng+hin+tam`) – detected but not performed.
* Key-detail extraction is rule-based and tuned to common district-court formats; unusual layouts may be missed.
* Marathi shares the Devanagari script and is detected as "Hindi".
* Sample judgments are fictional.

## 5. Future work (for the report)
* Abstractive summaries with IndicBART / mT5 fine-tuned on Indian judgments; offline translation with IndicTrans2.
* OCR integration; more languages (Telugu, Kannada, Malayalam cue words); citation / precedent extraction.
* Evaluation: ROUGE against headnotes on an Indian legal summarisation dataset.
* Integration with the eCourts case-status service and user authentication.

## 6. Project layout
```
app.py  summarizer.py  legal_info.py  lexicon.py  extractors.py  translator.py  install_offline_translation.py  build_sample_cache.py  sample_translations_cross.py  translation_cache.json
templates/index.html   samples/*.txt   tests/test_all.py   requirements.txt
```
