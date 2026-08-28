"""Regression coverage for text embedded in PDF Form XObjects."""

from __future__ import annotations

import unittest

from pdfminer.layout import LTFigure, LTPage
from pdfminer.pdfinterp import PDFResourceManager

from pdf2zh.converter import PDFConverterEx


class RecordingConverter(PDFConverterEx):
    """Minimal converter that records how an XObject is handed back."""

    def __init__(self) -> None:
        super().__init__(PDFResourceManager())
        self.received: tuple[object, bool] | None = None

    def receive_layout(self, item, *, force_protected: bool = False):
        self.received = (item, force_protected)


class FigureProtectionTests(unittest.TestCase):
    def test_figure_content_is_always_marked_protected(self):
        converter = RecordingConverter()
        page = LTPage(1, (0, 0, 200, 200))
        figure = LTFigure("Figure1", (20, 20, 180, 180), (1, 0, 0, 1, 0, 0))
        converter.cur_item = figure
        converter._stack = [page]

        converter.end_figure("Figure1")

        self.assertIs(converter.cur_item, page)
        self.assertIn(figure, page)
        self.assertEqual(converter.received, (figure, True))


if __name__ == "__main__":
    unittest.main()
