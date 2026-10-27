"""Language data for the legal summarizer: stop-words, legal cue words, UI labels.

Supported out of the box: English (en), Hindi (hi), Tamil (ta).
Other Indic scripts are detected and summarised with language-independent
statistics (TF-IDF + TextRank) but without cue words / stop-words.
"""

LANG_NAMES = {
    "en": "English", "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
    "kn": "Kannada", "ml": "Malayalam", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi",
}

# Unicode ranges used for script based language detection.
SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),  # Devanagari (Hindi / Marathi)
    "bn": (0x0980, 0x09FF),
    "pa": (0x0A00, 0x0A7F),
    "gu": (0x0A80, 0x0AFF),
    "ta": (0x0B80, 0x0BFF),
    "te": (0x0C00, 0x0C7F),
    "kn": (0x0C80, 0x0CFF),
    "ml": (0x0D00, 0x0D7F),
}

STOPWORDS = {
    "en": set("""a an the and or but if of to in on at by for with from as is are was were be been being
    this that these those it its he she they them his her their we our you your i not no nor so
    such than then there here which who whom whose what when where while also any all each other
    has have had do does did shall will would may might can could said above below herein thereof
    hereby upon under before after between into over about against""".split()),
    "hi": set("""है हैं था थे थी का की के में से को और पर यह वह एक ने भी कि तो ही इस उस हो कर लिए द्वारा
    गया गई गये किया किये जो तथा एवं या नहीं रहा रही सकता अपने उन्होंने उनके इसके उसके अर्थात
    था। है। थीं होने करने वाले वाली लिये साथ बाद पहले तक अपना अपनी""".split()),
    "ta": set("""ஒரு இந்த அந்த என்று என மற்றும் ஆனால் அவர் அவர்கள் இது அது உள்ள இல்லை ஆகும் என்பது
    போது மேலும் இதன் அதன் ஆகிய என்ற இதை அதை அவரது அவரின் பின்னர் முன்னர் மூலம் குறித்து""".split()),
}

# Cue words are matched as substrings of the lower-cased sentence, so they also
# catch inflected forms (important for Hindi / Tamil morphology).
ORDER_CUES = {
    "en": ["ordered", "directed", "dismissed", "allowed", "disposed", "decreed", "convicted",
           "acquitted", "sentenced", "granted", "rejected", "is hereby", "accordingly",
           "in the result", "imprisonment", "fine of", "compensation"],
    "hi": ["निर्देश", "खारिज", "स्वीकार किया", "दोषी", "बरी", "सजा", "कारावास",
           "जुर्माना", "निराकृत", "डिक्री", "अतः", "अतएव", "प्रतिकर", "रिहा"],
    "ta": ["உத்தரவிட", "தள்ளுபடி", "தண்டனை", "விடுதலை", "தீர்ப்பாணை", "அபராத",
           "சிறை", "டிகிரி", "எனவே", "அனுமதிக்கப்ப", "செலவுத்தொகை", "இழப்பீடு"],
}
FINDING_CUES = {
    "en": ["held", "observed", "find that", "found that", "satisfied", "opined", "conclude",
           "in view of", "therefore", "thus", "proved", "established", "not proved", "view that"],
    "hi": ["पाया", "माना", "निष्कर्ष", "संतुष्ट", "प्रमाणित", "सिद्ध", "अभिनिर्धारित", "मत है"],
    "ta": ["கருத்தில்", "நிரூபி", "திருப்தி", "கண்டறி", "முடிவுக்கு", "ஏற்க", "கருதுகிறது"],
}
ARGUMENT_CUES = {
    "en": ["contended", "submitted", "argued", "learned counsel", "learned advocate",
           "it was further", "opposed the", "pleaded"],
    "hi": ["तर्क", "निवेदन", "अधिवक्ता", "लोक अभियोजक", "विरोध करते"],
    "ta": ["வாதிட", "தெரிவித்தார்", "வழக்கறிஞர்", "எதிர்வாதம்", "கூறினார்"],
}

SECTION_TITLES = {
    "en": {"Facts": "Background / Facts", "Arguments": "Arguments of the Parties",
           "Findings": "Court's Findings", "Order": "Order / Operative Portion"},
    "hi": {"Facts": "पृष्ठभूमि / तथ्य", "Arguments": "पक्षकारों के तर्क",
           "Findings": "न्यायालय के निष्कर्ष", "Order": "आदेश / निर्णय"},
    "ta": {"Facts": "பின்னணி / உண்மைகள்", "Arguments": "தரப்பினரின் வாதங்கள்",
           "Findings": "நீதிமன்றத்தின் கண்டறிதல்கள்", "Order": "உத்தரவு / தீர்ப்பு"},
}

SECTION_WORD = {"en": "Section", "hi": "धारा", "ta": "பிரிவு"}

INFO_LABELS = {
    "en": {"case_numbers": "Case number", "court": "Court", "parties": "Parties",
           "dates": "Dates mentioned", "sections": "Sections / Acts", "outcome": "Outcome",
           "judge": "Judicial officer"},
    "hi": {"case_numbers": "प्रकरण क्रमांक", "court": "न्यायालय", "parties": "पक्षकार",
           "dates": "उल्लिखित तिथियाँ", "sections": "धाराएँ / अधिनियम", "outcome": "परिणाम",
           "judge": "न्यायिक अधिकारी"},
    "ta": {"case_numbers": "வழக்கு எண்", "court": "நீதிமன்றம்", "parties": "தரப்பினர்",
           "dates": "குறிப்பிடப்பட்ட தேதிகள்", "sections": "பிரிவுகள் / சட்டங்கள்",
           "outcome": "முடிவு", "judge": "நீதித்துறை அலுவலர்"},
}

OUTCOME_TEXT = {
    "Dismissed": {"en": "Dismissed", "hi": "खारिज", "ta": "தள்ளுபடி"},
    "Allowed": {"en": "Allowed", "hi": "स्वीकार", "ta": "ஏற்கப்பட்டது"},
    "Decreed": {"en": "Decreed", "hi": "डिक्री पारित", "ta": "தீர்ப்பாணை வழங்கப்பட்டது"},
    "Convicted": {"en": "Convicted", "hi": "दोषसिद्ध", "ta": "குற்றவாளி எனத் தீர்ப்பு"},
    "Acquitted": {"en": "Acquitted", "hi": "दोषमुक्त", "ta": "விடுதலை"},
    "Bail granted": {"en": "Bail granted", "hi": "जमानत मंजूर", "ta": "ஜாமீன் வழங்கப்பட்டது"},
    "Bail rejected": {"en": "Bail rejected", "hi": "जमानत अस्वीकृत", "ta": "ஜாமீன் மறுக்கப்பட்டது"},
    "Disposed of": {"en": "Disposed of", "hi": "निराकृत", "ta": "முடித்து வைக்கப்பட்டது"},
}

# Regex fragments (case-insensitive) that signal each outcome, in any supported language.
# Outcome matching is deliberately conservative. These patterns are applied only to
# the final operative portion (see legal_info.detect_outcome), and a missing match
# is preferable to inventing an outcome.
OUTCOME_PATTERNS = {
    "Bail granted": [
        r"bail application\s+(?:is\s+)?(?:hereby\s+)?(?:allowed|granted)",
        r"regular bail\s+(?:is\s+)?(?:hereby\s+)?(?:allowed|granted)",
        r"released on bail",
        r"जमानत आवेदन.{0,30}(?:स्वीकार|मंजूर)",
        r"जमानत पर रिहा",
        r"ஜாமீன் மனு.{0,30}(?:ஏற்க|வழங்க)",
    ],
    "Bail rejected": [
        r"bail application\s+(?:is\s+)?(?:hereby\s+)?(?:rejected|dismissed|refused)",
        r"जमानत आवेदन.{0,30}(?:अस्वीकार|खारिज)",
        r"ஜாமீன் மனு.{0,30}(?:மறுக்க|தள்ளுபடி)",
    ],
    "Acquitted": [
        r"(?:the accused|accused)\s+(?:is|are|stands?)\s+(?:hereby\s+)?acquitted",
        r"दोषमुक्त किया जाता है",
        r"आरोपी को बरी किया जाता है",
        r"குற்றச்சாட்டுகளிலிருந்து விடுவிக்கப்படுகிறார்",
    ],
    "Convicted": [
        r"(?:the accused|accused)\s+(?:is|stands?)\s+(?:hereby\s+)?convicted",
        r"convicted for the offence",
        r"दोषसिद्ध ठहराया जाता है",
        r"दोषी करार दिया जाता है",
        r"குற்றவாளி எனத் தீர்ப்பளிக்கப்படுகிறார்",
    ],
    "Decreed": [
        r"(?:the )?suit is hereby decreed",
        r"(?:the )?suit is decreed",
        r"वाद (?:स्वीकार|डिक्री) किया जाता है",
        r"வழக்கு தீர்ப்பாணை வழங்கப்படுகிறது",
        r"தீர்ப்பாணை வழங்கப்பட்டு வழக்கு அனுமதிக்கப்படுகிறது",
        r"தீர்ப்பாணை வழங்கப்படுகிறது",
    ],
    "Dismissed": [
        r"(?:the )?(?:appeal|petition|application|complaint|suit)\s+(?:is|stands)\s+(?:hereby\s+)?dismissed",
        r"(?:the )?(?:appeal|petition|application) is dismissed",
        r"याचिका खारिज की जाती है",
        r"आवेदन खारिज किया जाता है",
        r"மனு தள்ளுபடி செய்யப்படுகிறது",
    ],
    "Allowed": [
        r"(?:the )?(?:appeal|petition|application)\s+(?:is|stands)\s+(?:hereby\s+)?(?:partly\s+)?allowed",
        r"आवेदन स्वीकार किया जाता है",
        r"याचिका स्वीकार की जाती है",
        r"மனு ஏற்கப்படுகிறது",
    ],
    "Disposed of": [
        r"(?:the )?(?:matter|petition|application|case)\s+(?:is|stands)\s+(?:hereby\s+)?disposed of",
        r"प्रकरण का निराकरण किया जाता है",
        r"வழக்கு முடித்து வைக்கப்படுகிறது",
    ],
}

# Known statutes -> canonical English name. Used to attach an Act to a "Section N" mention.
ACTS = [
    ("Indian Penal Code, 1860", r"indian penal code|\bI\.?P\.?C\b|भारतीय दण्ड संहिता|भारतीय दंड संहिता|இந்திய தண்டனைச் சட்டம்"),
    ("Code of Criminal Procedure, 1973", r"criminal procedure|\bCr\.?\s?P\.?\s?C\b|दण्ड प्रक्रिया संहिता|दंड प्रक्रिया संहिता|குற்றவியல் நடைமுறைச் சட்டம்"),
    ("Code of Civil Procedure, 1908", r"civil procedure|\bC\.?P\.?C\b|सिविल प्रक्रिया संहिता|உரிமையியல் நடைமுறைச் சட்டம்"),
    ("Negotiable Instruments Act, 1881", r"negotiable instruments|நெகோஷியபிள்|\bN\.?\s?I\.?\s?Act|परक्राम्य लिखत|செலுத்துச் சீட்டு"),
    ("Bharatiya Nyaya Sanhita, 2023", r"bharatiya nyaya sanhita|\bB\.?N\.?S\b(?!S)|भारतीय न्याय संहिता"),
    ("Bharatiya Nagarik Suraksha Sanhita, 2023", r"nagarik suraksha|\bBNSS\b|नागरिक सुरक्षा संहिता"),
    ("Indian Evidence Act, 1872", r"evidence act|साक्ष्य अधिनियम|இந்திய சாட்சிய சட்டம்"),
    ("Motor Vehicles Act, 1988", r"motor vehicles act|मोटर यान अधिनियम|மோட்டார் வாகன"),
    ("Indian Contract Act, 1872", r"contract act|संविदा अधिनियम|ஒப்பந்தச் சட்டம்"),
    ("Limitation Act, 1963", r"limitation act|परिसीमा अधिनियम|காலவரம்பு சட்டம்"),
    ("Transfer of Property Act, 1882", r"transfer of property|सम्पत्ति अंतरण|சொத்து மாற்று"),
    ("Hindu Marriage Act, 1955", r"hindu marriage act|हिन्दू विवाह अधिनियम|இந்து திருமணச் சட்டம்"),
    ("Protection of Women from Domestic Violence Act, 2005", r"domestic violence"),
    ("POCSO Act, 2012", r"pocso|protection of children from sexual"),
    ("NDPS Act, 1985", r"\bNDPS\b|narcotic drugs"),
    ("Specific Relief Act, 1963", r"specific relief"),
]
