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
        return [{"bbox": (10, 20, 90, 180)}]

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
            Region(RegionKind.FIGURE, (10.0, 20.0, 90.0, 180.0), "high", ("image",))
        ])

    def test_protect_mask_scales_inverts_and_clamps_page_coordinates(self):
        mask = np.ones((100, 100))
        regions = [
            Region(RegionKind.FIGURE, (20, 30, 50, 60), "high", ("test",)),
            Region(RegionKind.FIGURE, (-10, -10, 10, 10), "high", ("test",)),
        ]

        count = protect_mask(mask, regions, (0, 0, 100, 100))

        self.assertEqual(count, 2)
        self.assertTrue((mask[40:70, 20:50] == 0).all())
        self.assertTrue((mask[90:100, 0:10] == 0).all())
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
