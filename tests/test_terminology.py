from __future__ import annotations

import unittest
from pathlib import Path

from pdf2zh.terminology import GlossaryEntry, GlossaryResolver, GlossaryValidationError, load_glossary


GLOSSARY = Path(__file__).parents[1] / "terminology" / "vi-ai-ml.json"


class TerminologyTests(unittest.TestCase):
    def setUp(self):
        self.resolver = load_glossary(GLOSSARY)

    def test_fixture_terms_resolve_with_longest_phrase_priority(self):
        text = "Scaled Dot-Product Attention uses ensemble models for sequence transduction."
        self.assertEqual(self.resolver.apply(text), "Cơ chế Attention tích vô hướng có tỷ lệ uses mô hình tổ hợp for chuyển đổi chuỗi.")
        self.assertEqual([match.entry.identifier for match in self.resolver.matches(text)], ["attn.scaled_dot_product_attention", "ml.ensemble_models", "seq.sequence_transduction"])

    def test_word_boundary_and_case_policy_prevent_false_matches(self):
        self.assertEqual(self.resolver.apply("an ensemblement and query"), "an ensemblement and query")
        self.assertEqual(self.resolver.apply("Google Research and google research"), "Google Research and google research")

    def test_conflicting_sources_are_rejected(self):
        entries = [
            GlossaryEntry("one", "dot product", "tích vô hướng", "translate", False, "math"),
            GlossaryEntry("two", "Dot Product", "sản phẩm chấm", "translate", False, "math"),
        ]
        with self.assertRaisesRegex(GlossaryValidationError, "conflicting"):
            GlossaryResolver(entries)


if __name__ == "__main__":
    unittest.main()
