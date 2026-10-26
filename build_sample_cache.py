"""Builds translation_cache.json with ready-made translations of the three SAMPLE judgments,
so the demo's "Output language" dropdown works with no internet and no extra packages.

    python build_sample_cache.py        # (re)creates translation_cache.json next to the app

Covered: every sample into the other two languages (6 pairs).
Any other document / language pair uses the live services (see README) and is added to the same cache.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sample_translations_cross import HI_TA, TA_HI  # noqa: E402
from summarizer import split_sentences  # noqa: E402

EN_HI = [
    "न्यायिक मजिस्ट्रेट प्रथम श्रेणी का न्यायालय, कोयंबटूर",
    "मेसर्स श्री विनायगा ट्रेडर्स, जिसका प्रतिनिधित्व इसके स्वामी श्री के. सेल्वम करते हैं ....",
    "श्री आर. आनंद कुमार ....",
    "परिवादी ने अभियुक्त के विरुद्ध 4,50,000 रुपये के चेक के अनादरण के लिए परक्राम्य लिखत अधिनियम, 1881 की धारा 138 के अंतर्गत यह परिवाद प्रस्तुत किया है।",
    "परिवादी का मामला यह है कि अभियुक्त ने जनवरी से मार्च 2022 के बीच परिवादी की दुकान से 4,50,000 रुपये मूल्य का हार्डवेयर सामान खरीदा और साठ दिनों के भीतर राशि चुकाने का वादा किया।",
    "इस दायित्व के निर्वहन में अभियुक्त ने भारतीय स्टेट बैंक, रेस कोर्स रोड शाखा, कोयंबटूर पर आहरित दिनांक 10/06/2022 का चेक क्रमांक 004521 जारी किया।",
    "जब परिवादी ने 14/06/2022 को चेक संग्रहण के लिए प्रस्तुत किया, तो बैंक ने 16/06/2022 को \"अपर्याप्त निधि\" के पृष्ठांकन के साथ उसे बिना भुगतान लौटा दिया।",
    "परिवादी ने 28/06/2022 को वैधानिक विधिक नोटिस जारी कर प्राप्ति के पंद्रह दिनों के भीतर भुगतान की माँग की, और वह नोटिस 01/07/2022 को अभियुक्त को तामील हुआ।",
    "अभियुक्त ने न तो राशि का भुगतान किया और न ही कोई उत्तर भेजा, और परिवादी ने परिसीमा अवधि के भीतर 29/07/2022 को यह परिवाद दायर किया।",
    "परिवादी ने स्वयं को अभि.सा.-1 के रूप में परीक्षित कराया और प्रदर्श पी-1 से पी-9 चिह्नित कराए, जिनमें चेक, बैंक वापसी ज्ञापन, विधिक नोटिस और डाक पावती शामिल हैं।",
    "अभियुक्त के विद्वान अधिवक्ता ने तर्क दिया कि चेक केवल ऋण लेन-देन की प्रतिभूति के रूप में दिया गया था और चेक की तारीख को कोई वैधानिक रूप से प्रवर्तनीय ऋण विद्यमान नहीं था।",
    "अभियुक्त की ओर से यह भी निवेदन किया गया कि चालानों पर हस्ताक्षर उसके नहीं थे और परिवादी ने हस्ताक्षरित कोरे चेक का दुरुपयोग किया है।",
    "अभियुक्त ने स्वयं को बचाव साक्षी-1 के रूप में परीक्षित कराया, किंतु कथित ऋण लेन-देन या चेक के दुरुपयोग की दलील के समर्थन में कोई दस्तावेज प्रस्तुत नहीं किया।",
    "परिवादी के विद्वान अधिवक्ता ने तर्क दिया कि अभियुक्त ने चेक पर अपने हस्ताक्षर स्वीकार किए हैं, अतः अधिनियम की धारा 118 एवं 139 के अंतर्गत वैधानिक उपधारणा परिवादी के पक्ष में लागू होती है।",
    "इस न्यायालय ने मौखिक एवं दस्तावेजी साक्ष्य तथा दोनों पक्षों द्वारा किए गए निवेदनों पर विचार किया है।",
    "यह विवादित नहीं है कि चेक अभियुक्त के खाते का है और उस पर उसके हस्ताक्षर हैं, जिन्हें उसने प्रतिपरीक्षण के दौरान स्वीकार किया।",
    "हस्ताक्षर स्वीकार हो जाने पर न्यायालय यह उपधारणा करने के लिए बाध्य है कि चेक वैधानिक रूप से प्रवर्तनीय ऋण के लिए जारी किया गया था, और इस उपधारणा का खंडन करने का भार संभाव्यता की प्रबलता के आधार पर अभियुक्त पर आ जाता है।",
    "न्यायालय पाता है कि अभियुक्त ने उपधारणा का खंडन करने के लिए कोई विश्वसनीय साक्ष्य प्रस्तुत नहीं किया, और हस्ताक्षरित कोरे प्रतिभूति चेक की दलील पहली बार केवल प्रतिपरीक्षण के दौरान उठाई गई।",
    "न्यायालय यह भी पाता है कि परिवादी ने चेक के अनादरण, वैधानिक नोटिस की तामीली और निर्धारित अवधि में भुगतान करने में अभियुक्त की विफलता को सिद्ध कर दिया है।",
    "अतः परक्राम्य लिखत अधिनियम, 1881 की धारा 138 के अंतर्गत अपराध के सभी तत्व युक्तियुक्त संदेह से परे स्थापित होते हैं।",
    "तदनुसार, अभियुक्त श्री आर. आनंद कुमार को दोषी पाया जाता है और परक्राम्य लिखत अधिनियम, 1881 की धारा 138 के अंतर्गत दंडनीय अपराध के लिए दोषसिद्ध किया जाता है।",
    "यह मानते हुए कि अपराध वाणिज्यिक प्रकृति का है, अभियुक्त को छह माह के साधारण कारावास की सजा दी जाती है तथा दण्ड प्रक्रिया संहिता, 1973 की धारा 357(3) के अंतर्गत साठ दिनों के भीतर परिवादी को 5,00,000 रुपये प्रतिकर का भुगतान करने का निर्देश दिया जाता है।",
    "प्रतिकर का भुगतान न करने की स्थिति में अभियुक्त को तीन माह का अतिरिक्त साधारण कारावास भुगतना होगा।",
    "अपील प्रस्तुत करने में सक्षम बनाने हेतु अभियुक्त का जमानत बंधपत्र तीस दिनों की अवधि तक प्रभावी रहेगा।",
]

EN_TA = [
    "நீதித்துறை நடுவர் முதல் வகுப்பு நீதிமன்றம், கோயம்புத்தூர்",
    "எம்/எஸ் ஸ்ரீ விநாயகா டிரேடர்ஸ், அதன் உரிமையாளர் திரு. கே. செல்வம் மூலம் பிரதிநிதித்துவப்படுத்தப்படுகிறது ....",
    "திரு. ஆர். ஆனந்த் குமார் ....",
    "ரூ. 4,50,000 மதிப்புள்ள காசோலை திரும்பியதற்காக, எதிரி மீது 1881 ஆம் ஆண்டு செலுத்துச் சீட்டுச் சட்டத்தின் பிரிவு 138 இன் கீழ் புகார்தாரர் இந்தப் புகாரைத் தாக்கல் செய்துள்ளார்.",
    "புகார்தாரரின் வழக்கு என்னவென்றால், 2022 ஜனவரி முதல் மார்ச் வரையிலான காலத்தில் எதிரி புகார்தாரரின் கடையிலிருந்து ரூ. 4,50,000 மதிப்புள்ள வன்பொருள் பொருட்களை வாங்கி, அறுபது நாட்களுக்குள் தொகையைச் செலுத்துவதாக உறுதியளித்தார்.",
    "இந்தப் பொறுப்பைத் தீர்க்கும் வகையில், கோயம்புத்தூர் ரேஸ் கோர்ஸ் சாலைக் கிளையிலுள்ள பாரத ஸ்டேட் வங்கியின் மீது 10/06/2022 தேதியிட்ட காசோலை எண் 004521 ஐ எதிரி வழங்கினார்.",
    "புகார்தாரர் 14/06/2022 அன்று காசோலையை வசூலுக்காகச் சமர்ப்பித்தபோது, \"போதிய நிதி இல்லை\" என்ற குறிப்புடன் 16/06/2022 அன்று வங்கி அதைப் பணம் வழங்காமல் திருப்பி அனுப்பியது.",
    "புகார்தாரர் 28/06/2022 அன்று சட்டப்பூர்வ வழக்கறிஞர் அறிவிப்பை அனுப்பி, பெற்ற பதினைந்து நாட்களுக்குள் தொகையைச் செலுத்தக் கோரினார்; அந்த அறிவிப்பு 01/07/2022 அன்று எதிரிக்குக் கிடைக்கப்பெற்றது.",
    "எதிரி தொகையைச் செலுத்தவுமில்லை, எந்தப் பதிலும் அனுப்பவுமில்லை; எனவே புகார்தாரர் காலவரம்புக்குள் 29/07/2022 அன்று இந்தப் புகாரைத் தாக்கல் செய்தார்.",
    "புகார்தாரர் தன்னை பு.சா.1 ஆக விசாரித்துக்கொண்டு, காசோலை, வங்கித் திருப்புச் சீட்டு, சட்ட அறிவிப்பு மற்றும் அஞ்சல் ஒப்புகை உள்ளிட்ட பி1 முதல் பி9 வரையிலான சான்றாவணங்களைக் குறிக்கச் செய்தார்.",
    "காசோலை ஒரு கடன் பரிவர்த்தனைக்கான பிணையாக மட்டுமே வழங்கப்பட்டது என்றும், காசோலை தேதியன்று சட்டப்படி வசூலிக்கத்தக்க கடன் எதுவும் இல்லை என்றும் எதிரியின் வழக்கறிஞர் வாதிட்டார்.",
    "விலைப்பட்டியல்களில் உள்ள கையொப்பம் தன்னுடையது அல்ல என்றும், கையொப்பமிடப்பட்ட வெற்றுக் காசோலையைப் புகார்தாரர் தவறாகப் பயன்படுத்தினார் என்றும் எதிரி மேலும் தெரிவித்தார்.",
    "எதிரி தன்னை எ.சா.1 ஆக விசாரித்துக்கொண்டார்; ஆனால் கூறப்படும் கடன் பரிவர்த்தனையையோ, காசோலை தவறாகப் பயன்படுத்தப்பட்டது என்ற வாதத்தையோ நிரூபிக்க எந்த ஆவணத்தையும் தாக்கல் செய்யவில்லை.",
    "காசோலையில் தனது கையொப்பத்தை எதிரி ஒப்புக்கொண்டுள்ளதால், சட்டத்தின் பிரிவுகள் 118 மற்றும் 139 இன் கீழான சட்டப்பூர்வ ஊகம் புகார்தாரருக்குச் சாதகமாகச் செயல்படுகிறது என்று புகார்தாரரின் வழக்கறிஞர் வாதிட்டார்.",
    "வாய்மொழி மற்றும் ஆவண சாட்சியங்களையும் இரு தரப்பினரின் வாதங்களையும் இந்த நீதிமன்றம் பரிசீலித்தது.",
    "காசோலை எதிரியின் கணக்குக்குரியது என்பதும் அதில் அவரது கையொப்பம் உள்ளது என்பதும் மறுக்கப்படவில்லை; குறுக்கு விசாரணையின்போது அவர் அதை ஒப்புக்கொண்டார்.",
    "கையொப்பம் ஒப்புக்கொள்ளப்பட்டவுடன், காசோலை சட்டப்படி வசூலிக்கத்தக்க கடனுக்காக வழங்கப்பட்டது என்று நீதிமன்றம் ஊகிக்கக் கடமைப்பட்டுள்ளது; இந்த ஊகத்தை நிகழ்தகவுகளின் மிகைப்பாட்டின் அடிப்படையில் மறுக்கும் பொறுப்பு எதிரியிடம் மாறுகிறது.",
    "இந்த ஊகத்தை மறுக்க எதிரி எந்த நம்பத்தகுந்த சாட்சியத்தையும் முன்வைக்கவில்லை என்றும், கையொப்பமிடப்பட்ட வெற்றுப் பிணைக் காசோலை என்ற வாதம் குறுக்கு விசாரணையின்போதுதான் முதன்முறையாக எழுப்பப்பட்டது என்றும் நீதிமன்றம் காண்கிறது.",
    "காசோலை திரும்பியதையும், சட்டப்பூர்வ அறிவிப்பு சேர்க்கப்பட்டதையும், குறிப்பிட்ட காலத்துக்குள் எதிரி பணம் செலுத்தத் தவறியதையும் புகார்தாரர் நிரூபித்துள்ளார் என்றும் நீதிமன்றம் மேலும் காண்கிறது.",
    "எனவே 1881 ஆம் ஆண்டு செலுத்துச் சீட்டுச் சட்டத்தின் பிரிவு 138 இன் கீழான குற்றத்தின் அனைத்து கூறுகளும் நியாயமான சந்தேகத்துக்கு அப்பாற்பட்டு நிறுவப்பட்டுள்ளன.",
    "அதன்படி, எதிரி திரு. ஆர். ஆனந்த் குமார் குற்றவாளி எனக் கண்டறியப்பட்டு, 1881 ஆம் ஆண்டு செலுத்துச் சீட்டுச் சட்டத்தின் பிரிவு 138 இன் கீழ் தண்டனைக்குரிய குற்றத்திற்காகத் தண்டிக்கப்படுகிறார்.",
    "குற்றம் வணிகத் தன்மையுடையது என்பதைக் கருத்தில் கொண்டு, எதிரிக்கு ஆறு மாத எளிய சிறைத்தண்டனை விதிக்கப்படுகிறது; மேலும் 1973 ஆம் ஆண்டு குற்றவியல் நடைமுறைச் சட்டத்தின் பிரிவு 357(3) இன் கீழ் அறுபது நாட்களுக்குள் புகார்தாரருக்கு ரூ. 5,00,000 இழப்பீடு செலுத்த வேண்டும்.",
    "இழப்பீடு செலுத்தத் தவறினால், எதிரி மேலும் மூன்று மாத எளிய சிறைத்தண்டனை அனுபவிக்க வேண்டும்.",
    "மேல்முறையீடு செய்ய ஏதுவாக, எதிரியின் பிணை உறுதிமொழிப் பத்திரம் முப்பது நாட்களுக்குச் செயலில் இருக்கும்.",
]

HI_EN = [
    "Court of the Additional Sessions Judge, District Court, Bhopal (M.P.)",
    "The applicant Rajesh Kumar Sharma has filed this regular bail application under Section 439 of the Code of Criminal Procedure.",
    "A case, Crime No. 212/2024, is registered against the applicant at Police Station Kolar, Bhopal, alleging cheating and criminal breach of trust under Sections 420 and 406 of the Indian Penal Code.",
    "According to the prosecution, the applicant lured the complainant with the promise of getting a plot at a cheap rate and received a total of Rs. 8,00,000 between 10/01/2023 and 05/05/2023.",
    "When the plot was not registered, the complainant asked for the money back, but the applicant refused to return it, after which a First Information Report was lodged on 02/02/2024.",
    "The applicant was arrested on 20/02/2024 and has been in judicial custody since then.",
    "The applicant's counsel argued that the applicant has been falsely implicated and that the entire dispute is essentially a civil transaction.",
    "It was also submitted that the applicant has no previous criminal record, is a permanent resident of Bhopal, and that the investigation is complete and the charge sheet has been filed in court.",
    "The applicant's counsel also stated that the maximum punishment is up to seven years and that the trial is likely to take a long time.",
    "Opposing bail, the Public Prosecutor for the non-applicant State stated that the applicant has cheated many persons in a similar manner.",
    "The Public Prosecutor also argued that two other complaints against the applicant are under investigation and that, if released, he may influence the witnesses.",
    "The Court heard the arguments of the counsel for both parties and examined the case diary and the charge sheet.",
    "This Court is of the view that the allegations against the applicant are serious, but they are not punishable with death or life imprisonment.",
    "The charge sheet has been filed and all documentary evidence is secured with the police, therefore the custody of the applicant is no longer necessary.",
    "The Court has reached the conclusion that the trial will take time and it would not be proper to keep the applicant in jail indefinitely.",
    "Therefore, considering all the circumstances of the case, the bail application of the applicant is allowed.",
    "The applicant is directed to be released on bail on furnishing a personal bond of Rs. 50,000 and one local surety for the same amount.",
    "The applicant shall appear in court at every hearing, shall not influence the witnesses, and shall not leave Bhopal without the permission of the court.",
    "In case of violation of the conditions, the prosecution may file an application for cancellation of bail.",
    "A copy of this order shall be sent to the concerned court and the Station House Officer for necessary action.",
]

TA_EN = [
    "The plaintiff Murugesan filed this suit against the defendant Subramanian seeking recovery of Rs. 3,00,000 with interest on the basis of a promissory note.",
    "According to the plaintiff, the defendant borrowed Rs. 3,00,000 from the plaintiff on 12/04/2018 for the construction of his house.",
    "For that amount, the defendant executed a promissory note and promised to repay it within two years with interest at nine percent per annum.",
    "Since the defendant did not repay the money even after the stipulated period, the plaintiff sent a notice through an advocate on 15/09/2020.",
    "As the defendant gave no reply to that notice, the plaintiff filed this suit on 10/03/2021.",
    "In his written statement, the defendant contended that he had not borrowed any loan from the plaintiff and that the signature on the promissory note was forged.",
    "The plaintiff's advocate stated that the handwriting expert's report confirms that the defendant's signature is genuine.",
    "On the plaintiff's side, the plaintiff was examined as a witness, along with a person who was present when the loan was given as witness No. 2; documents were marked as Ex. P1 to Ex. P5.",
    "The defendant testified on his own behalf but did not file any document.",
    "The Court considered the arguments of both sides and the evidence.",
    "It is clear under Section 118 of the Negotiable Instruments Act that if a promissory note is signed and executed, it must be presumed in law that it was given for consideration for a loan.",
    "The Court found, according to the handwriting expert's report, that the signature on the promissory note matches the defendant's specimen signatures.",
    "As the defendant did not produce any credible evidence to prove his contention that he had not taken the loan, the Court has come to the conclusion that his defence is not acceptable.",
    "It has also been proved to the satisfaction of the Court that the suit was filed within the limitation period.",
    "Therefore, this Court determines that the plaintiff is entitled to the relief sought.",
    "Accordingly, the suit is decreed and allowed for the principal amount of Rs. 3,00,000 together with interest at nine percent per annum.",
    "It is ordered that interest at six percent per annum be awarded from the date of filing of the suit until the date of judgment, and thereafter at six percent until the amount is paid.",
    "The defendant shall pay this amount to the plaintiff within two months and shall also pay the costs of the suit.",
]

JOBS = [("english", "en", "hi", EN_HI), ("english", "en", "ta", EN_TA),
        ("hindi", "hi", "en", HI_EN), ("tamil", "ta", "en", TA_EN),
        ("hindi", "hi", "ta", HI_TA), ("tamil", "ta", "hi", TA_HI)]


def main():
    cache = {}
    for sample, src, tgt, translations in JOBS:
        with open(os.path.join(HERE, "samples", f"sample_{sample}.txt"), encoding="utf-8") as fh:
            sentences = split_sentences(fh.read())
        assert len(sentences) == len(translations), (sample, tgt, len(sentences), len(translations))
        for s, t in zip(sentences, translations):
            cache[f"{src}>{tgt}|{s}"] = t
    path = os.path.join(HERE, "translation_cache.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=0)
    print(f"Wrote {len(cache)} translations to {path}")


if __name__ == "__main__":
    main()
