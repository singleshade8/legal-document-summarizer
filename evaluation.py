"""Source-grounded checks for extractive legal summaries.

These checks are deterministic text matching, not legal reasoning or a validated
semantic factuality model. The scores measure traceability to extracted source
text and cue coverage only; they must never be labelled legal accuracy.
"""
from difflib import SequenceMatcher
import re
import unicodedata

from summarizer import split_sentences

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

_NEGATIONS = {
    "en": {"not", "no", "never", "neither", "without", "cannot", "denied", "refused"},
    "hi": {"नहीं", "नही", "नकारा", "अस्वीकार", "नहीं।"},
    "ta": {"இல்லை", "அல்ல", "மறுக்க", "மறுத்த", "இல்லாத"},
}

# These are broad retrieval cues, not a substitute for issue/holding annotation.
_COVERAGE_CUES = {
    "Material facts / background": {
        "en": ("complainant", "petitioner", "applicant", "respondent", "according to", "facts"),
        "hi": ("आवेदक", "परिवादी", "याचिकाकर्ता", "प्रतिवादी", "अभियोजन के अनुसार"),
        "ta": ("வாதி", "பிரதிவாதி", "மனுதாரர்", "எதிர்மனுதாரர்", "கூற்றுப்படி"),
    },
    "Legal provisions": {
        "en": ("section ", "article ", "act, ", "constitution", "rule "),
        "hi": ("धारा", "अनुच्छेद", "अधिनियम", "संविधान"),
        "ta": ("பிரிவு", "சட்டம்", "அரசியலமைப்பு"),
    },
    "Court reasoning / holding": {
        "en": ("the court held", "the court finds", "we hold", "we conclude", "the court observed", "this court is of the view"),
        "hi": ("न्यायालय ने माना", "न्यायालय का मत", "निष्कर्ष पर पहुँचा", "अदालत ने"),
        "ta": ("நீதிமன்றம் கண்டறிந்தது", "நீதிமன்றம் தீர்மானிக்கிறது", "முடிவுக்கு வந்தது"),
    },
    "Operative directions": {
        "en": ("we direct", "it is ordered", "is hereby allowed", "is hereby dismissed", "shall be", "is directed to", "the following directions"),
        "hi": ("निर्देश दिया जाता है", "आदेश दिया जाता है", "स्वीकार किया जाता है", "खारिज किया जाता है", "निर्देशित किया जाता है"),
        "ta": ("உத்தரவிடப்படுகிறது", "மனு ஏற்கப்படுகிறது", "தள்ளுபடி செய்யப்படுகிறது", "வழங்கப்பட வேண்டும்"),
    },
    "Procedural safeguards / qualifications": {
        "en": ("preliminary inquiry", "reasons in writing", "communicate the reasons", "within ", "subject to", "provided that", "exception"),
        "hi": ("प्रारंभिक जांच", "लिखित कारण", "कारणों से अवगत", "के अधीन", "अपवाद"),
        "ta": ("முன்னோட்ட விசாரணை", "எழுத்துப்பூர்வ காரணம்", "காரணங்களைத் தெரிவிக்க", "நிபந்தனை"),
    },
}


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(_normalise(text)))


def _negated(text: str, lang: str) -> bool:
    normal = _normalise(text)
    terms = _NEGATIONS.get(lang, set())
    return any(term in normal for term in terms)


def _candidate_score(claim: str, evidence: str) -> float:
    claim_n, evidence_n = _normalise(claim), _normalise(evidence)
    if not claim_n or not evidence_n:
        return 0.0
    char_ratio = SequenceMatcher(None, claim_n, evidence_n, autojunk=False).ratio()
    claim_tokens, evidence_tokens = _tokens(claim_n), _tokens(evidence_n)
    if not claim_tokens or not evidence_tokens:
        return char_ratio
    overlap = len(claim_tokens & evidence_tokens)
    recall = overlap / len(claim_tokens)
    precision = overlap / len(evidence_tokens)
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return 0.60 * char_ratio + 0.40 * f1


def evaluate_claims(source_text: str, claims: list[str], lang: str = "en") -> dict:
    """Classify each summary line by source-text matching and return defined metrics.

    Supported means a normalised exact source match. Partial support is a lexical
    similarity heuristic. Contradicted is emitted only for a near-identical
    source sentence with a polarity cue mismatch; all other weak matches are
    Not Verifiable. These labels are screening hints, not legal conclusions.
    """
    source_sentences = split_sentences(source_text)
    source_normal = _normalise(source_text)
    items = []
    for claim in claims:
        claim_n = _normalise(claim)
        exact = bool(claim_n and claim_n in source_normal)
        best_idx, best_score, best_sentence = None, 0.0, ""
        for idx, sentence in enumerate(source_sentences, start=1):
            score = _candidate_score(claim, sentence)
            if score > best_score:
                best_idx, best_score, best_sentence = idx, score, sentence

        if exact:
            status = "Supported"
            reason = "The summary line matches text in the extracted source."
            # Prefer the source sentence that contains the claim exactly.
            exact_idx = next(
                (i for i, sentence in enumerate(source_sentences, start=1)
                 if claim_n and claim_n in _normalise(sentence)),
                None,
            )
            if exact_idx is not None:
                best_idx = exact_idx
                best_sentence = source_sentences[exact_idx - 1]
            score = 1.0
        elif (best_score >= 0.76
              and _negated(claim, lang) != _negated(best_sentence, lang)):
            status = "Contradicted"
            reason = "A near-matching source sentence has a different negation signal; manual review is required."
            score = best_score
        elif best_score >= 0.58:
            status = "Partially Supported"
            reason = "There is lexical overlap with a source sentence, but exact support was not established."
            score = best_score
        else:
            status = "Not Verifiable"
            reason = "No sufficiently close source sentence was found by this text-matching check."
            score = best_score

        items.append({
            "claim": claim,
            "status": status,
            "evidence": best_sentence,
            "source_sentence_number": best_idx,
            "match_score": round(score, 3),
            "reason": reason,
        })

    total = len(items)
    counts = {label: sum(item["status"] == label for item in items)
              for label in ("Supported", "Partially Supported", "Contradicted", "Not Verifiable")}
    if total:
        weighted = counts["Supported"] + 0.5 * counts["Partially Supported"]
        support_percent = round(100 * weighted / total)
        exact_percent = round(100 * counts["Supported"] / total)
        reliability = "Heuristic screening only"
    else:
        support_percent = exact_percent = None
        reliability = "Unable to evaluate reliably"

    normal_source = _normalise(source_text)
    normal_summary = _normalise(" ".join(claims))
    coverage = []
    available = []
    covered = []
    for label, languages in _COVERAGE_CUES.items():
        cues = languages.get(lang, languages.get("en", ()))
        in_source = [cue for cue in cues if cue in normal_source]
        in_summary = [cue for cue in cues if cue in normal_summary]
        relevant = bool(in_source)
        is_covered = bool(in_summary)
        if relevant:
            available.append(label)
            if is_covered:
                covered.append(label)
        coverage.append({
            "category": label,
            "relevant_in_source": relevant,
            "present_in_summary": is_covered if relevant else None,
        })
    coverage_percent = round(100 * len(covered) / len(available)) if available else None

    return {
        "metric_name": "Claim-support text-match screening",
        "reliability": reliability,
        "claims_total": total,
        "claim_counts": counts,
        "claim_support_percent": support_percent,
        "exact_source_match_percent": exact_percent,
        "coverage_percent": coverage_percent,
        "coverage_basis": "Cue-based screening of categories detected in source text; not a completeness or legal-accuracy score.",
        "coverage": coverage,
        "claims": items,
        "metric_definition": (
            "Supported=normalised exact text match; Partially Supported=best lexical match >=0.58; "
            "Contradicted=near-match >=0.76 with a different negation signal; otherwise Not Verifiable. "
            "Support screening weights Supported=1, Partially Supported=0.5, other statuses=0. "
            "This is not semantic entailment, legal accuracy, or a validated benchmark."
        ),
    }
