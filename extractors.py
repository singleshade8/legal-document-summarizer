"""Read text out of uploaded PDF / DOCX / TXT files."""
import io


class ExtractionError(Exception):
    pass


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return data.decode("utf-8", errors="ignore")


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = [(p.extract_text() or "") for p in reader.pages]
        except Exception as exc:
            raise ExtractionError(f"Could not read the PDF ({exc}).")
        text = "\n".join(pages).strip()
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
            raise ExtractionError(f"Could not read the DOCX file ({exc}).")
        return "\n".join(p.text for p in d.paragraphs).strip()
    if name.endswith(".txt") or not name:
        return _decode(data).strip()
    raise ExtractionError("Unsupported file type. Please upload a PDF, DOCX or TXT file.")
