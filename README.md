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

Run the tests: `python -m unittest discover -s tests -v`.

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

### Accuracy and privacy — read before relying on a result

This is a **prototype**, not a validated legal research system. Extractive summarisation selects text from the source
rather than freely generating new sentences, which can reduce unsupported paraphrases. It does **not** guarantee
accuracy: PDF text extraction, page headers/footers, sentence splitting, ranking, section classification, regex-based
metadata and cross-language translation can all omit, distort or misclassify legally important context.

The outcome field is a conservative heuristic. If it cannot identify explicit operative wording, it may be blank;
a blank is preferable to guessing. Any detected outcome, case metadata and summary must be checked against the original
judgment, especially before legal, filing or case-management use. The app does not currently have a validated,
benchmark-based accuracy percentage, so do not present a percentage as measured accuracy.

The source text is processed in the app, but when a user requests a different output language for their own document,
the summary may be sent to a third-party public translation service. Do not use cross-language translation for
confidential or sensitive documents unless that transfer is acceptable. This software is not legal advice.

### Operative-order selection

The summariser looks for a standalone late heading such as “Conclusion and Directions”, “Operative Portion” or “Final Order”. When found, it prioritises multiple direction-like sentences from that portion, subject to the summary budget. If no clear heading is found, it uses the existing cue-based fallback. This is a structural heuristic and cannot guarantee every direction or qualification is captured.

### Source traceability check

The summary result includes a `claim_check` object. Each selected summary line is checked against the extracted source and reports a screening label (`Supported`, `Partially Supported`, `Contradicted`, or `Not Verifiable`), the closest extracted source sentence, and a source-sentence number. For PDFs, a page number is shown only when the match points unambiguously to one page; ambiguous matches are left without a page number. DOCX/TXT extraction does not provide reliable page layout.

These labels are conservative string/lexical heuristics. A `Supported` result means that text is present in the extracted source; it does not prove that the line is correctly contextualised, legally significant, complete, or consistent with the final operative order. `Contradicted` is only a polarity-cue warning and can be wrong. Coverage checks are cue-based and do not establish completeness. Treat the panel as a review aid, not as a legal-accuracy percentage.

## 3. API

`POST /api/summarize` – multipart form: `file` **or** `text`, `ratio` (0.05–0.6, default 0.25), `out_lang` (`same|en|hi|ta`).
Returns `language`, `stats`, `key_info`, `sections`, `summary_text`, `translation`, and `claim_check` (heuristic source traceability).

## 4. Limitations (mention these in your report)
* Extractive: no paraphrasing; Hindi/Tamil stemming is a simple prefix heuristic, not a full morphological analyser.
* Scanned PDFs need OCR first (Tesseract `eng+hin+tam`) – detected but not performed.
* Key-detail extraction and outcome classification are rule-based heuristics. They may omit details or return no outcome; every result needs verification against the operative portion of the source.
* Repeated PDF margin text is filtered conservatively, but irregular layouts and scanned documents may still extract incorrectly.
* Cross-language translation uses third-party services for uncached user text; translated legal terminology must be verified by a qualified reader.
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
