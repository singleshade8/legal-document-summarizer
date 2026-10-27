"""Rule-based extraction of structured facts from a court order / judgment:
case number, court, parties, dates, statutory sections and the outcome."""
import re

from lexicon import ACTS, OUTCOME_PATTERNS
from summarizer import normalize_digits

_CASE_NO = re.compile(
    r"((?:\S+\s+){0,4}?(?:No\.?|Nos\.?|संख्या|क्रमांक|क्र\.|எண்\.?)\s*[:\-]?\s*\d+\s*(?:/|of)\s*\d{4})",
    re.I,
)
_DATE_NUM = re.compile(r"\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b")
_MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_DATE_TXT = re.compile(rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?{_MONTHS}[,\s]+\d{{4}}\b", re.I)
_SECTION = re.compile(
    r"(?:Sections?|Secs?\.?|u/s\.?|धारा(?:ओं)?|பிரிவு(?:கள்)?(?:ன்)?)\s*"
    r"(\d+[A-Z]?(?:\s*\(\w+\))*(?:\s*(?:,|and|&|/|और|तथा|एवं|व|மற்றும்)\s*\d+[A-Z]?(?:\s*\(\w+\))*)*)",
    re.I,
)
_VS_INLINE = re.compile(r"^(.{3,90}?)\s+(?:vs\.?|v\.|versus|बनाम)\s+(.{3,90})$", re.I)
_VS_ALONE = re.compile(r"^(?:vs\.?|v\.|versus|बनाम|எதிர்)$", re.I)
_ROLE_SPLIT = re.compile(r"\s*(?:\.{2,}|…+|-{2,}|_{2,})\s*")
_COURT = re.compile(r"court|न्यायालय|நீதிமன்ற", re.I)
_JUDGE = re.compile(r"judge|magistrate|munsif|न्यायाधीश|मजिस्ट्रेट|நீதிபதி|நடுவர்", re.I)


def _lines(text):
    return [l.strip() for l in text.replace("\r", "").split("\n") if l.strip()]


def _party(raw: str):
    parts = [p for p in _ROLE_SPLIT.split(raw.strip(" .:-")) if p]
    name = parts[0].strip() if parts else raw.strip()
    role = parts[1].strip() if len(parts) > 1 else ""
    return f"{name} ({role})" if role else name


def _case_numbers(lines):
    found = []
    for line in lines[:12]:
        if len(line) > 110:  # body sentences are not headers
            continue
        m = _CASE_NO.search(normalize_digits(line))
        if m:
            v = re.sub(r"\s+", " ", m.group(1)).strip()
            if v not in found:
                found.append(v)
    return found[:3]


def _parties(lines):
    head = lines[:40]
    for idx, line in enumerate(head):
        if _VS_ALONE.match(line) and 0 < idx < len(head) - 1:
            return [_party(head[idx - 1]), _party(head[idx + 1])]
        m = _VS_INLINE.match(line)
        if m:
            return [_party(m.group(1)), _party(m.group(2))]
    return []


def _court(lines):
    for line in lines[:12]:
        if _COURT.search(line) and len(line) < 140:
            return line.strip(" :-")
    return ""


def _judge(lines):
    for line in lines[:15]:
        m = re.match(r"(?:before|coram|presided by|समक्ष|முன்னிலை)\s*[:\-]\s*(.+)", line, re.I)
        if m:
            return m.group(1).strip()
    tail = lines[-8:]
    for idx in range(len(tail) - 1, -1, -1):
        if _JUDGE.search(tail[idx]) and len(tail[idx]) < 90:
            prev = tail[idx - 1] if idx > 0 and len(tail[idx - 1]) < 60 else ""
            return f"{prev}, {tail[idx]}".strip(", ")
    return ""


def _dates(text):
    t = normalize_digits(text)
    found = []
    for rx in (_DATE_NUM, _DATE_TXT):
        for m in rx.finditer(t):
            v = m.group(0)
            if v not in found:
                found.append(v)
    return found[:6]


def _act_near(text: str, start: int, end: int):
    window = text[max(0, start - 70): end + 90]
    best = None
    for name, pattern in ACTS:
        m = re.search(pattern, window, re.I)
        if m:
            dist = abs(m.start() - (start - max(0, start - 70)))
            if best is None or dist < best[0]:
                best = (dist, name)
    return best[1] if best else ""


def _sections(text):
    t = normalize_digits(text)
    found = []
    for m in _SECTION.finditer(t):
        nums = re.sub(r"\s*(?:,|and|&|/|और|तथा|एवं|व|மற்றும்)\s*", ", ", re.sub(r"\s+", " ", m.group(1))).strip()
        act = _act_near(t, m.start(), m.end())
        entry = f"Section {nums}" + (f" – {act}" if act else "")
        if entry not in found:
            found.append(entry)
    return found[:8]


def detect_outcome(text: str) -> str:
    """Return only an explicit outcome found near the end of the document.

    The result is a heuristic, not a legal conclusion. A false blank is safer
    than inferring acquittal/conviction from discussion of another case or from
    arguments quoted in the judgment.
    """
    # Outcomes usually appear in the operative portion. Searching only the final
    # 30% reduces accidental matches in facts, counsel submissions and citations.
    tail = text[int(len(text) * 0.70):]
    best = None
    for label, patterns in OUTCOME_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, tail, re.I):
                preceding = tail[max(0, match.start() - 60):match.start()].casefold()
                # Avoid classifying an expressly negated English outcome.
                if re.search(r"\b(?:not|never|no longer)\b(?:\W+\w+){0,4}\W*$", preceding):
                    continue
                # Common negation markers in Hindi and Tamil. Keep the check
                # local to the matched phrase so unrelated earlier text is ignored.
                if re.search(r"(?:नहीं|नही|नकारा गया)\s*(?:है\s*)?$", preceding[-24:]):
                    continue
                if re.search(r"(?:இல்லை|மறுக்கப்படவில்லை|அல்ல)\s*$", preceding[-24:]):
                    continue
                candidate = (match.start(), label)
                if best is None or candidate[0] > best[0]:
                    best = candidate
    return best[1] if best else ""


def extract_key_info(text: str) -> dict:
    lines = _lines(text)
    return {
        "case_numbers": _case_numbers(lines),
        "court": _court(lines),
        "parties": _parties(lines),
        "judge": _judge(lines),
        "dates": _dates(text),
        "sections": _sections(text),
        "outcome": detect_outcome(text),
    }
