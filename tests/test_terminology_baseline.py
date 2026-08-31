"""Data-contract tests for the academic Vietnamese terminology baseline."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
FIXTURE_ROOT = ROOT / "fixtures" / "academic-v1"
GLOSSARY_PATH = ROOT.parent / "terminology" / "vi-ai-ml.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TerminologyBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.glossary = load(GLOSSARY_PATH)
        cls.fixture = load(FIXTURE_ROOT / "manifest.json")
        cls.expected = load(FIXTURE_ROOT / "expected-vi.json")
        cls.banned = load(FIXTURE_ROOT / "banned-translations.json")
        cls.entries = cls.glossary["entries"]
        cls.by_id = {entry["id"]: entry for entry in cls.entries}

    def test_glossary_schema_has_a_viable_seed_size_and_unique_ids(self):
        self.assertEqual(self.glossary["schema_version"], 1)
        self.assertEqual(self.glossary["source_language"], "en")
        self.assertEqual(self.glossary["target_language"], "vi")
        self.assertGreaterEqual(len(self.entries), 20)
        self.assertEqual(len(self.by_id), len(self.entries))
        for entry in self.entries:
            with self.subTest(entry=entry["id"]):
                self.assertTrue(entry["source"])
                self.assertTrue(entry["target"])
                self.assertIn(entry["policy"], {"translate", "preserve"})
                self.assertIsInstance(entry["case_sensitive"], bool)

    def test_fixture_terms_have_exact_expected_glossary_entries(self):
        expected_sources = {item["source"] for item in self.expected["term_expectations"]}
        self.assertEqual(expected_sources, set(self.fixture["terms"]))
        for item in self.expected["term_expectations"]:
            with self.subTest(source=item["source"]):
                entry = self.by_id[item["glossary_id"]]
                self.assertEqual(entry["source"], item["source"])
                self.assertEqual(entry["target"], item["target"])

    def test_preserved_names_and_titles_have_identity_targets(self):
        for item in self.expected["term_expectations"]:
            entry = self.by_id[item["glossary_id"]]
            if entry["policy"] == "preserve":
                with self.subTest(entry=entry["id"]):
                    self.assertEqual(entry["source"], entry["target"])

    def test_bans_reference_known_entries_and_never_match_expected_target(self):
        for item in self.banned["entries"]:
            with self.subTest(entry=item["glossary_id"]):
                entry = self.by_id[item["glossary_id"]]
                self.assertTrue(item["forbidden_targets"])
                self.assertNotIn(entry["target"], item["forbidden_targets"])
                self.assertTrue(all(len(value.split()) >= 2 for value in item["forbidden_targets"]))


if __name__ == "__main__":
    unittest.main()
