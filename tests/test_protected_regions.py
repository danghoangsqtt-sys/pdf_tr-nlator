"""Structural and visual regression proof for academic protected regions."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np
import pymupdf

from pdf2zh.regions import PROTECTED_REGION_KINDS, discover_regions, protect_mask


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "academic-v1"
FIXTURE = FIXTURE_DIR / "academic-ml-source.pdf"
SNAPSHOT = FIXTURE_DIR / "protected-regions.json"


def serialise_regions(page: pymupdf.Page) -> list[dict[str, object]]:
    """Return deterministic detector evidence in the reviewed snapshot format."""
    return [
        {
            "kind": region.kind.value,
            "bbox": [round(value, 1) for value in region.bbox],
            "confidence": region.confidence,
            "evidence": list(region.evidence),
        }
        for region in discover_regions(page)
    ]


def glyph_centres(page: pymupdf.Page) -> list[tuple[str, float, float]]:
    """Extract visible text glyph centres in PyMuPDF's top-left page space."""
    glyphs: list[tuple[str, float, float]] = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                for char in span["chars"]:
                    x0, y0, x1, y1 = char["bbox"]
                    glyphs.append((char["c"], (x0 + x1) / 2, (y0 + y1) / 2))
    return glyphs


def mask_index(page: pymupdf.Page, mask: np.ndarray, x: float, y: float) -> tuple[int, int]:
    """Map a top-left PyMuPDF point to the lower-left layout mask index."""
    height, width = mask.shape
    rect = page.rect
    column = min(width - 1, max(0, int((x - rect.x0) / rect.width * width)))
    row = min(height - 1, max(0, int((rect.y1 - y) / rect.height * height)))
    return row, column


class ProtectedRegionTests(unittest.TestCase):
    def test_detector_matches_reviewed_fixture_snapshot(self):
        expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        with pymupdf.open(FIXTURE) as document:
            actual = [
                {"page": page.number + 1, "regions": serialise_regions(page)}
                for page in document
            ]

        self.assertEqual(expected["schema_version"], 1)
        self.assertEqual(expected["pages"], actual)

    def test_every_glyph_in_a_protected_fixture_region_hits_the_locked_mask(self):
        with pymupdf.open(FIXTURE) as document:
            for page in document:
                pixmap = page.get_pixmap()
                mask = np.ones((pixmap.height, pixmap.width), dtype=np.uint8)
                regions = discover_regions(page)
                protected = [region for region in regions if region.kind in PROTECTED_REGION_KINDS]
                self.assertGreater(protect_mask(mask, regions, page.rect), 0)

                all_glyphs = glyph_centres(page)
                for region in protected:
                    x0, y0, x1, y1 = region.bbox
                    enclosed = [
                        (char, x, y)
                        for char, x, y in all_glyphs
                        if x0 <= x <= x1 and y0 <= y <= y1
                    ]
                    self.assertTrue(enclosed, f"page {page.number + 1} {region} has no glyph evidence")
                    for char, x, y in enclosed:
                        with self.subTest(page=page.number + 1, region=region.kind.value, glyph=char):
                            row, column = mask_index(page, mask, x, y)
                            self.assertEqual(mask[row, column], 0)

    def test_formula_and_vector_figure_crops_render_with_visible_ink(self):
        crops = ((0, pymupdf.Rect(64, 302, 531, 404)), (1, pymupdf.Rect(72, 160, 523, 540)))
        with pymupdf.open(FIXTURE) as document:
            for page_number, crop in crops:
                pixmap = document[page_number].get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=crop, alpha=False)
                pixels = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, 3)
                ink_ratio = np.any(pixels < 240, axis=2).mean()
                with self.subTest(page=page_number + 1):
                    self.assertGreater(ink_ratio, 0.01)


if __name__ == "__main__":
    unittest.main()
