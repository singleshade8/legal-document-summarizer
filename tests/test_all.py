"""Run with:  python -m unittest discover -s tests -v"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, build_result                      # noqa: E402
from extractors import _clean_repeated_page_margins    # noqa: E402
from legal_info import detect_outcome, extract_key_info  # noqa: E402
import translator                                        # noqa: E402
from summarizer import detect_language, split_sentences, summarize  # noqa: E402

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")


def sample(name):
    with open(os.path.join(SAMPLES, f"sample_{name}.txt"), encoding="utf-8") as fh:
        return fh.read()


class LanguageTests(unittest.TestCase):
    def test_detects_all_three(self):
        self.assertEqual(detect_language(sample("english")), "en")
        self.assertEqual(detect_language(sample("hindi")), "hi")
        self.assertEqual(detect_language(sample("tamil")), "ta")

    def test_bilingual_prefers_indic_when_substantial(self):
        self.assertEqual(detect_language("Case No. 5/2020 " + "यह एक आदेश है " * 30), "hi")


class SplitterTests(unittest.TestCase):
    def test_legal_abbreviations_do_not_split(self):
        text = ("The petition was filed by Mr. K. Selvam against Smt. Lakshmi under Sec. 138 of the N.I. Act "
                "before the Hon'ble Court. The court dismissed the petition on merits after hearing both sides.")
        sents = split_sentences(text)
        self.assertEqual(len(sents), 2, sents)

    def test_hindi_danda_and_rupee_abbreviation(self):
        sents = split_sentences("आवेदक ने 5,00,000 रु. की राशि प्राप्त की थी और लौटाने से इनकार कर दिया। "
                                "न्यायालय ने दोनों पक्षों को सुना और आदेश सुरक्षित रखा।")
        self.assertEqual(len(sents), 2, sents)

    def test_tamil_rupee_abbreviation(self):
        sents = split_sentences("வாதி பிரதிவாதியிடமிருந்து ரூ. 3,00,000 கடனாகப் பெற்றார் என்று கூறினார். "
                                "நீதிமன்றம் இரு தரப்பையும் விசாரித்து முடிவுக்கு வந்தது.")
        self.assertEqual(len(sents), 2, sents)

    def test_numbering_removed(self):
        sents = split_sentences("1. The complainant filed the complaint before this Court in time.\n"
                                "2. The accused did not appear despite service of summons repeatedly.")
        self.assertTrue(sents[0].startswith("The complainant"))


class PdfCleanupTests(unittest.TestCase):
    def test_repeated_page_header_and_page_numbers_are_removed(self):
        pages = [
            "Lalita Kumari v. State of U.P.\nPage 1\nFirst body paragraph has enough content.\nFooter 1",
            "Lalita Kumari v. State of U.P.\nPage 2\nSecond body paragraph has enough content.\nFooter 2",
            "Lalita Kumari v. State of U.P.\nPage 3\nThird body paragraph has enough content.\nFooter 3",
        ]
        cleaned = _clean_repeated_page_margins(pages)
        self.assertTrue(all("Lalita Kumari v. State of U.P." not in page for page in cleaned))
        self.assertTrue(all(not line.lower().startswith("page ") for page in cleaned for line in page.splitlines()))
        self.assertIn("First body paragraph", cleaned[0])
        self.assertIn("Second body paragraph", cleaned[1])

    def test_single_page_text_is_preserved(self):
        page = "Court title\nPage 1\nA single page with meaningful legal text."
        self.assertEqual(_clean_repeated_page_margins([page]), [page])


class KeyInfoTests(unittest.TestCase):
    def test_english(self):
        info = extract_key_info(sample("english"))
        self.assertIn("1187/2022", info["case_numbers"][0])
        self.assertTrue(any("138" in s and "Negotiable" in s for s in info["sections"]))
        self.assertEqual(info["outcome"], "Convicted")
        self.assertEqual(len(info["parties"]), 2)

    def test_hindi_bail_granted_not_overridden_by_later_conditions(self):
        self.assertEqual(detect_outcome(sample("hindi")), "Bail granted")

    def test_tamil_decreed(self):
        self.assertEqual(extract_key_info(sample("tamil"))["outcome"], "Decreed")

    def test_outcome_is_not_inferred_from_a_reference_to_an_old_acquittal(self):
        prefix = "Procedural background concerns statutory interpretation and police duties. " * 20
        text = (
            prefix
            + "A cited case records that the accused was acquitted of all charges. "
            + "The present court directs registration of information disclosing a cognizable offence "
            + "and lays down procedural directions."
        )
        self.assertEqual(detect_outcome(text), "")

    def test_outcome_requires_explicit_operative_wording(self):
        prefix = "Procedural background concerns statutory interpretation and police duties. " * 20
        self.assertEqual(detect_outcome(
            prefix + "The accused is hereby convicted for the offence and sentenced according to law."
        ), "Convicted")
        self.assertEqual(detect_outcome(
            prefix + "The court directs registration of an FIR and provides guidance to police officers."
        ), "")

    def test_digits_in_devanagari_are_normalised(self):
        info = extract_key_info("वाद क्रमांक १२३/२०२४\nआदेश दिनांक १५/०३/२०२४ को पारित किया गया।")
        self.assertIn("123/2024", info["case_numbers"][0])
        self.assertIn("15/03/2024", info["dates"])


class SummariserTests(unittest.TestCase):
    def test_summary_is_shorter_and_ordered(self):
        for name in ("english", "hindi", "tamil"):
            text = sample(name)
            res = summarize(text, ratio=0.3)
            self.assertGreaterEqual(len(res["selected"]), 3)
            self.assertLess(len(" ".join(res["selected"])), len(text) * 0.6)
            sents = split_sentences(text)
            idx = [sents.index(s) for s in res["selected"]]
            self.assertEqual(idx, sorted(idx), "summary must keep document order")

    def test_operative_order_always_included(self):
        res = summarize(sample("english"), ratio=0.15)
        order = [s for sec in res["sections"] if sec["key"] == "Order" for s in sec["sentences"]]
        self.assertTrue(order, "operative portion missing")
        self.assertTrue(any("sentenced" in s or "convicted" in s for s in order))

    def test_empty_and_tiny_inputs(self):
        self.assertEqual(summarize("")["selected"], [])
        self.assertIsInstance(summarize("The court heard the matter today and reserved orders.")["selected"], list)

    def test_larger_document_is_fast(self):
        import time
        big = "\n".join(sample("english") for _ in range(25))
        t = time.time()
        summarize(big, ratio=0.1)
        self.assertLess(time.time() - t, 20)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def test_home_and_health(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        self.assertEqual(self.c.get("/health").get_json()["status"], "ok")

    def test_text_summarise(self):
        r = self.c.post("/api/summarize", data={"text": sample("hindi"), "ratio": "0.3"})
        j = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(j["language"]["code"], "hi")
        self.assertTrue(j["sections"])

    def test_too_short_rejected(self):
        self.assertEqual(self.c.post("/api/summarize", data={"text": "too short"}).status_code, 400)

    def test_bad_file_type_rejected(self):
        r = self.c.post("/api/summarize", data={"file": (io.BytesIO(b"x"), "a.exe")},
                        content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def test_docx_upload(self):
        import docx
        d = docx.Document()
        for para in sample("english").split("\n"):
            d.add_paragraph(para)
        buf = io.BytesIO()
        d.save(buf)
        buf.seek(0)
        r = self.c.post("/api/summarize", data={"file": (buf, "order.docx")}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertEqual(r.get_json()["language"]["code"], "en")

    def test_pdf_upload(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            self.skipTest("reportlab not installed")
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        y = 800
        for line in sample("english").replace("\n\n", "\n").split("\n"):
            for chunk in [line[i:i + 95] for i in range(0, len(line), 95)] or [""]:
                c.drawString(30, y, chunk)
                y -= 13
                if y < 40:
                    c.showPage()
                    y = 800
        c.save()
        buf.seek(0)
        r = self.c.post("/api/summarize", data={"file": (buf, "order.pdf")}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        self.assertTrue(r.get_json()["sections"])

    def test_translation_failure_is_graceful(self):
        j = build_result(sample("english"), 0.3, out_lang="hi")
        self.assertIsNotNone(j["translation"])
        if j["translation"]["error"]:  # offline / package missing -> still returns the original summary
            self.assertTrue(j["sections"])


class BuiltInSampleTranslationTests(unittest.TestCase):
    """The shipped translation_cache.json must serve the demo with no network / packages."""

    def test_samples_translate_without_any_provider(self):
        pairs = (("english", "hi"), ("english", "ta"), ("hindi", "en"), ("hindi", "ta"),
                 ("tamil", "en"), ("tamil", "hi"))
        for name, out in pairs:
            for ratio in (0.15, 0.3, 0.5):
                tr = build_result(sample(name), ratio, out)["translation"]
                self.assertIsNone(tr["error"], (name, out, ratio, tr["error"]))
                self.assertEqual(tr["provider"], "cache")
                self.assertTrue(tr["sections"])


class TranslatorResilienceTests(unittest.TestCase):
    """Simulate free-service rate limits without any network access."""

    def setUp(self):
        import tempfile
        self._orig = (translator._CACHE_PATH, translator._cache, translator._providers, translator.time.sleep)
        translator._CACHE_PATH = os.path.join(tempfile.mkdtemp(), "cache.json")
        translator._cache = None
        translator.time.sleep = lambda *_: None
        self.calls = []

    def tearDown(self):
        translator._CACHE_PATH, translator._cache, translator._providers, translator.time.sleep = self._orig

    def _fake(self, name, fn, limit=4500, batch=True):
        translator._providers = lambda s, t: [(name, fn, limit, batch)]

    SENTS = ["The court heard the matter.", "The petition is dismissed.", "No costs are awarded."]

    def test_single_batched_request_for_many_sentences(self):
        def ok(text, s, t):
            self.calls.append(text)
            return "\n".join("T:" + x for x in text.split("\n"))
        self._fake("fake", ok)
        out, err, prov = translator.translate_sentences(self.SENTS, "en", "hi")
        self.assertIsNone(err)
        self.assertEqual(len(self.calls), 1, "should be ONE request, not one per sentence")
        self.assertEqual(out[1], "T:The petition is dismissed.")

    def test_cache_prevents_second_request(self):
        def ok(text, s, t):
            self.calls.append(text)
            return "\n".join("T:" + x for x in text.split("\n"))
        self._fake("fake", ok)
        translator.translate_sentences(self.SENTS, "en", "ta")
        translator.translate_sentences(self.SENTS, "en", "ta")
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(os.path.exists(translator._CACHE_PATH))

    def test_rate_limit_then_recovery_via_retry(self):
        state = {"n": 0}

        def flaky(text, s, t):
            state["n"] += 1
            if state["n"] < 2:
                raise Exception("429 Too Many Requests")
            return "\n".join("T:" + x for x in text.split("\n"))
        self._fake("fake", flaky)
        out, err, _ = translator.translate_sentences(self.SENTS, "en", "hi")
        self.assertIsNone(err)
        self.assertEqual(len(out), 3)

    def test_falls_back_to_second_provider(self):
        def blocked(text, s, t):
            raise Exception("429 Too Many Requests")

        def good(text, s, t):
            return "M:" + text
        translator._providers = lambda s, t: [("google", blocked, 4500, True), ("mymemory", good, 450, False)]
        out, err, prov = translator.translate_sentences(self.SENTS, "en", "hi")
        self.assertIsNone(err)
        self.assertEqual(prov, "mymemory")
        self.assertEqual(out[0], "M:The court heard the matter.")

    def test_all_providers_rate_limited_gives_clear_message(self):
        def blocked(text, s, t):
            raise Exception("429 Too Many Requests")
        self._fake("google", blocked)
        out, err, prov = translator.translate_sentences(self.SENTS, "en", "hi")
        self.assertIsNone(out)
        self.assertIn("busy", err)

    def test_line_count_mismatch_falls_back_per_sentence(self):
        def merges(text, s, t):
            return "T:" + text.replace("\n", " ") if "\n" in text else "T:" + text
        self._fake("fake", merges)
        out, err, _ = translator.translate_sentences(self.SENTS, "en", "hi")
        self.assertIsNone(err)
        self.assertEqual(out, ["T:" + s for s in self.SENTS])

    def test_gtx_response_is_parsed_and_batched(self):
        seen = []

        def fake_http(url, timeout=15):
            seen.append(url)
            return [[["T1\n", "a", None, None, 1], ["T2\n", "b", None, None, 1], ["T3", "c", None, None, 1]]]
        orig = translator._http_json
        translator._http_json = fake_http
        try:
            translator._providers = lambda s, t: [("google-gtx", translator._gtx, 4000, True, translator._enc_size)]
            out, err, prov = translator.translate_sentences(self.SENTS, "en", "hi")
        finally:
            translator._http_json = orig
        self.assertIsNone(err)
        self.assertEqual(out, ["T1", "T2", "T3"])
        self.assertEqual(len(seen), 1)
        self.assertIn("translate.googleapis.com", seen[0])

    def test_mymemory_quota_message_counts_as_rate_limit(self):
        orig = translator._http_json
        translator._http_json = lambda url, timeout=15: {
            "responseStatus": 200, "responseData": {"translatedText": "MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS"}}
        try:
            translator._providers = lambda s, t: [("mymemory", translator._mymemory, 450, False)]
            out, err, _ = translator.translate_sentences(self.SENTS, "en", "hi")
        finally:
            translator._http_json = orig
        self.assertIsNone(out)
        self.assertIn("busy", err)

    def test_http_429_maps_to_rate_limited(self):
        import urllib.error
        orig = translator.urllib.request.urlopen

        def boom(*a, **k):
            raise urllib.error.HTTPError("u", 429, "Too Many", {}, None)
        translator.urllib.request.urlopen = boom
        try:
            with self.assertRaises(translator.RateLimited):
                translator._http_json("https://example.org/x")
        finally:
            translator.urllib.request.urlopen = orig

    def test_long_indic_sentence_is_split_for_small_limit_provider(self):
        long = " ".join(["न्यायालय"] * 80)
        pieces = translator._split_bytes(long)
        self.assertTrue(all(len(p.encode("utf-8")) <= 440 for p in pieces))
        self.assertEqual(" ".join(pieces), long)


if __name__ == "__main__":
    unittest.main()
