"""Integrity checks for the self-authored academic PDF regression corpus."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pymupdf


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "academic-v1"
PDF_PATH = FIXTURE_ROOT / "academic-ml-source.pdf"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"


class AcademicFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.document = pymupdf.open(PDF_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.document.close()

    def test_manifest_hash_matches_committed_pdf(self):
        digest = hashlib.sha256(PDF_PATH.read_bytes()).hexdigest()
        self.assertEqual(self.manifest["sha256"], digest)
        self.assertEqual(self.manifest["license"], "CC0-1.0")

    def test_fixture_has_expected_pages_and_terminology(self):
        self.assertEqual(self.document.page_count, self.manifest["pages"])
        # Text extractors may insert a line break inside a wrapped phrase. The
        # corpus contract is semantic term coverage, not a particular wrap.
        text = " ".join("\n".join(page.get_text() for page in self.document).split())
        for term in self.manifest["terms"]:
            with self.subTest(term=term):
                self.assertIn(" ".join(term.split()), text)

    def test_formula_page_uses_a_monospace_font(self):
        fonts = {
            span["font"].lower()
            for block in self.document[0].get_text("dict")["blocks"]
            if block["type"] == 0
            for line in block["lines"]
            for span in line["spans"]
        }
        self.assertTrue(any("cour" in font for font in fonts))

    def test_figure_page_contains_vector_drawing_and_labels(self):
        page = self.document[1]
        self.assertGreater(len(page.get_drawings()), 5)
        text = page.get_text()
        for label in ("Query", "Key", "Value", "Attention weights"):
            with self.subTest(label=label):
                self.assertIn(label, text)


if __name__ == "__main__":
    unittest.main()
