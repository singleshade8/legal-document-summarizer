"""Read text out of uploaded PDF / DOCX / TXT files."""
import io
import math
import re
from collections import Counter


class ExtractionError(Exception):
    pass


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data.decode("utf-8", errors="ignore")


def _line_key(line: str) -> str:
    """Normalise a line for repeated PDF header/footer detection."""
    return re.sub(r"\s+", " ", line).strip().casefold()


def _clean_repeated_page_margins(pages: list[str]) -> list[str]:
    """Remove repeating page-margin text without deleting ordinary body text.

    Only lines occurring in the first/last three non-empty lines of multiple
    pages are candidates. This conservative heuristic is intended for repeated
    case captions, running titles and page footers; it does not perform OCR or
    attempt to rewrite the judgment.
    """
    if len(pages) < 2:
        return pages

    margin_counts = Counter()
    for page in pages:
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        margin = lines[:3] + lines[-3:]
        # Count a line at most once per page.
        margin_counts.update(set(_line_key(line) for line in margin if len(_line_key(line)) >= 6))

    threshold = max(2, math.ceil(len(pages) * 0.25))
    repeated = {key for key, count in margin_counts.items() if count >= threshold}

    cleaned = []
    for page_index, page in enumerate(pages):
        kept = []
        for line in page.splitlines():
            key = _line_key(line)
            # Page numbers are layout artefacts when isolated on a line.
            if re.fullmatch(r"(?:page\s+)?\d{1,4}(?:\s+of\s+\d{1,4})?", key):
                continue
            # Keep the first-page occurrence for case/court metadata; suppress
            # duplicated running headers/footers from subsequent pages only.
            if page_index > 0 and key and key in repeated:
                continue
            kept.append(line)
        cleaned.append("\n".join(kept).strip())
    return cleaned


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [(p.extract_text() or "") for p in reader.pages]
        except Exception as exc:
            raise ExtractionError(f"Could not read the PDF ({exc}).") from exc
        pages = _clean_repeated_page_margins(pages)
        text = "\n\n".join(page for page in pages if page).strip()
        if len(text) < 50:
            raise ExtractionError(
                "This PDF has no selectable text (it looks like a scanned image). "
                "Run OCR first (e.g. Tesseract with eng+hin+tam) or paste the text."
            )
        return text
    if name.endswith(".docx"):
        import docx
        try:
            d = docx.Document(io.BytesIO(data))
        except Exception as exc:
            raise ExtractionError(f"Could not read the DOCX file ({exc}).") from exc
        return "\n".join(p.text for p in d.paragraphs).strip()
    if name.endswith(".txt") or not name:
        return _decode(data).strip()
    raise ExtractionError("Unsupported file type. Please upload a PDF, DOCX or TXT file.")
