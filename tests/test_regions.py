"""Tests for evidence-backed protected region discovery and mask mapping."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pymupdf

from pdf2zh.regions import Region, RegionKind, discover_regions, protect_mask


FIXTURE = Path(__file__).parent / "fixtures" / "academic-v1" / "academic-ml-source.pdf"


class FakeImagePage:
    rect = pymupdf.Rect(0, 0, 100, 200)

    def get_image_info(self):
        return [{"bbox": (10, 20, 50, 80)}]

    def cluster_drawings(self):
        return []


class RegionTests(unittest.TestCase):
    def test_fixture_vector_figure_is_discovered_without_a_layout_model(self):
        with pymupdf.open(FIXTURE) as document:
            regions = discover_regions(document[1])

        figures = [region for region in regions if region.kind is RegionKind.FIGURE]
        self.assertTrue(any("vector-drawing" in region.evidence for region in figures))
        self.assertTrue(
            any(
                region.bbox[0] <= 72
                and region.bbox[1] <= 160
                and region.bbox[2] >= 523
                and region.bbox[3] >= 540
                for region in figures
            )
        )

    def test_image_region_is_high_confidence_figure(self):
        regions = discover_regions(FakeImagePage())
        self.assertEqual(regions, [
            Region(RegionKind.FIGURE, (10.0, 20.0, 50.0, 80.0), "high", ("image",))
        ])

    def test_fixture_formula_lines_are_discovered_from_font_evidence(self):
        with pymupdf.open(FIXTURE) as document:
            regions = discover_regions(document[0])

        formulas = [region for region in regions if region.kind is RegionKind.FORMULA]
        self.assertEqual(len(formulas), 2)
        self.assertTrue(
            any(
                region.bbox[0] <= 88
                and region.bbox[1] <= 346
                and region.bbox[2] >= 289
                and region.bbox[3] >= 365
                and "formula-font:Courier" in region.evidence
                for region in formulas
            )
        )

    def test_unicode_math_is_formula_and_ambiguous_syntax_is_unknown(self):
        class FormulaPage:
            rect = pymupdf.Rect(0, 0, 200, 200)

            def get_image_info(self):
                return []

            def cluster_drawings(self):
                return []

            def get_text(self, mode):
                if mode != "dict":
                    raise ValueError(mode)
                return {
                    "blocks": [
                        {
                            "type": 0,
                            "lines": [
                                {"spans": [{"text": "∑ xᵢ = 1", "font": "Helvetica", "bbox": (10, 10, 80, 20)}]},
                                {"spans": [{"text": "x = y / z", "font": "Helvetica", "bbox": (10, 30, 80, 40)}]},
                            ],
                        }
                    ]
                }

        regions = discover_regions(FormulaPage())
        self.assertEqual([region.kind for region in regions], [RegionKind.FORMULA, RegionKind.UNKNOWN])
        self.assertIn("unicode-math", regions[0].evidence)
        self.assertIn("formula-syntax:operators=2", regions[1].evidence)

    def test_full_page_image_is_also_classified_as_scan(self):
        class ScanPage:
            rect = pymupdf.Rect(0, 0, 100, 100)

            def get_image_info(self):
                return [{"bbox": (0, 0, 90, 90)}]

            def cluster_drawings(self):
                return []

        regions = discover_regions(ScanPage())
        self.assertEqual([region.kind for region in regions], [RegionKind.FIGURE, RegionKind.SCAN])
        self.assertEqual(regions[1].confidence, "high")
        self.assertIn("coverage=0.810", regions[1].evidence)

    def test_protect_mask_scales_inverts_and_clamps_page_coordinates(self):
        mask = np.ones((100, 100))
        regions = [
            Region(RegionKind.FIGURE, (20, 30, 50, 60), "high", ("test",)),
            Region(RegionKind.FIGURE, (-10, -10, 10, 10), "high", ("test",)),
            Region(RegionKind.UNKNOWN, (70, 70, 80, 80), "low", ("test",)),
        ]

        count = protect_mask(mask, regions, (0, 0, 100, 100))

        self.assertEqual(count, 3)
        self.assertTrue((mask[40:70, 20:50] == 0).all())
        self.assertTrue((mask[90:100, 0:10] == 0).all())
        self.assertTrue((mask[20:30, 70:80] == 0).all())
        self.assertEqual(mask[0, 99], 1)

    def test_small_vector_cluster_is_not_misclassified_as_a_figure(self):
        class SmallDrawingPage:
            rect = pymupdf.Rect(0, 0, 100, 100)

            def get_image_info(self):
                return []

            def cluster_drawings(self):
                return [pymupdf.Rect(10, 10, 30, 30)]

        self.assertEqual(discover_regions(SmallDrawingPage()), [])


if __name__ == "__main__":
    unittest.main()
