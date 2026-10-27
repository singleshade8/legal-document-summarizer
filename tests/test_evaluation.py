"""Regression tests for source-text traceability screening."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import build_result  # noqa: E402
from evaluation import _negated, evaluate_claims  # noqa: E402
from summarizer import summarize  # noqa: E402


class ClaimEvaluationTests(unittest.TestCase):
    def test_exact_source_text_is_supported_with_sentence_reference(self):
        source = (
            "The court heard both parties carefully. "
            "The petition is dismissed after hearing the submissions. "
            "No costs are awarded by the court."
        )
        result = evaluate_claims(source, ["The petition is dismissed after hearing the submissions."])
        claim = result["claims"][0]
        self.assertEqual(claim["status"], "Supported")
        self.assertIsNotNone(claim["source_sentence_number"])
        self.assertEqual(result["exact_source_match_percent"], 100)
        self.assertIn("validated benchmark", result["metric_definition"])

    def test_near_match_with_opposite_negation_is_flagged_for_review(self):
        source = "The court did not dismiss the petition after hearing both parties."
        claim = "The court did dismiss the petition after hearing both parties."
        result = evaluate_claims(source, [claim])
        self.assertEqual(result["claims"][0]["status"], "Contradicted")
        self.assertIn("manual review", result["claims"][0]["reason"])

    def test_unrelated_word_containing_not_is_not_a_negation(self):
        self.assertFalse(_negated("The court noted a notable procedural issue.", "en"))
        self.assertTrue(_negated("The court did not dismiss the petition.", "en"))

    def test_explicit_directions_heading_preserves_multiple_operative_lines(self):
        background = "The court reviewed police procedure and statutory duties in the record. " * 18
        prior_case = "A cited decision discussed medical negligence in a separate context."
        text = (
            background
            + "\\n\\n"
            + prior_case
            + "\\n\\nCONCLUSION AND DIRECTIONS\\n"
            + "The officer shall register the information when a cognizable offence is disclosed.\\n"
            + "The officer must communicate reasons in writing if the complaint is closed."
        )
        result = summarize(text, ratio=0.1)
        order = " ".join(
            sentence
            for section in result["sections"] if section["key"] == "Order"
            for sentence in section["sentences"]
        ).casefold()
        self.assertIn("shall register", order)
        self.assertIn("must communicate", order)
        self.assertNotIn("medical negligence", order)

    def test_pdf_page_is_reported_when_the_match_is_unambiguous(self):
        page_one = "Background facts are discussed on this page in detail."
        page_two = "The petition is dismissed after hearing the submissions."
        source_pages = [page_one, page_two]
        source = "\n\n".join(source_pages)
        result = evaluate_claims(
            source,
            ["The petition is dismissed after hearing the submissions."],
            source_pages=source_pages,
        )
        self.assertEqual(result["claims"][0]["source_page"], 2)

    def test_empty_claim_list_has_no_percentage(self):
        result = evaluate_claims("The court issued an order.", [])
        self.assertEqual(result["claims_total"], 0)
        self.assertIsNone(result["claim_support_percent"])
        self.assertIsNone(result["exact_source_match_percent"])

    def test_partial_match_is_not_called_exact_support(self):
        source = "The petition was dismissed by the court after hearing both parties."
        claim = "The court dismissed the petition after both parties were heard."
        result = evaluate_claims(source, [claim])
        self.assertEqual(result["claims"][0]["status"], "Partially Supported")
        self.assertEqual(result["exact_source_match_percent"], 0)

    def test_build_result_exposes_claim_check_without_claiming_accuracy(self):
        source = (
            "This is a sufficiently long court document describing the facts of a dispute. "
            "The petitioner filed an application before the competent court. "
            "Both parties were heard and their submissions were considered by the judge. "
            "The court dismissed the petition after considering the record. "
            "No costs are awarded and the order is pronounced in open court."
        )
        result = build_result(source)
        self.assertIn("claim_check", result)
        self.assertEqual(result["claim_check"]["metric_name"], "Claim-support text-match screening")
        self.assertNotIn("accuracy_percent", result["claim_check"])


if __name__ == "__main__":
    unittest.main()
