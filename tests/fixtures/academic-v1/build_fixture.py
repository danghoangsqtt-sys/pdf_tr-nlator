"""Build the self-authored academic PDF regression fixture.

The fixture deliberately contains only original prose and diagrams. It exercises
terminology, monospace formula protection, and text embedded in vector graphics
without redistributing a third-party paper.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "academic-ml-source.pdf"
MANIFEST_PATH = ROOT / "manifest.json"
PAGE_SIZE = (595, 842)  # A4 at 72 dpi
MARGIN = 64

TERMS = [
    "Attention Is All You Need",
    "Google Research",
    "ensemble models",
    "Scaled Dot-Product Attention",
    "English constituency parsing",
    "sequence transduction",
    "Label Smoothing",
]


def add_textbox(page: pymupdf.Page, rect: pymupdf.Rect, text: str, *, size: float = 11,
                font: str = "helv", color: tuple[float, float, float] = (0.08, 0.1, 0.15)) -> None:
    """Insert text and fail rather than silently clipping a fixture label."""
    remaining = page.insert_textbox(rect, text, fontsize=size, fontname=font, color=color, lineheight=1.28)
    if remaining < 0:
        raise RuntimeError(f"Text did not fit in fixture rectangle: {rect}")


def draw_header(page: pymupdf.Page, title: str, subtitle: str) -> None:
    page.draw_rect(pymupdf.Rect(0, 0, PAGE_SIZE[0], 54), color=None, fill=(0.04, 0.15, 0.27))
    page.insert_text((MARGIN, 31), title, fontsize=16, fontname="hebo", color=(1, 1, 1))
    page.insert_text((MARGIN, 48), subtitle, fontsize=8.5, fontname="helv", color=(0.75, 0.86, 0.96))


def build_page_one(doc: pymupdf.Document) -> None:
    page = doc.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
    draw_header(page, "Academic translation regression fixture", "Self-authored CC0 source document - page 1 of 2")

    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 82, 531, 138),
        "A compact test document for terminology-sensitive PDF translation.",
        size=18,
        font="hebo",
    )
    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 152, 531, 282),
        "This fixture references Attention Is All You Need as a paper title and Google Research as an organisation name. "
        "It uses ensemble models for sequence transduction and reports an English constituency parsing benchmark. "
        "The implementation applies Scaled Dot-Product Attention before Label Smoothing. These terms are deliberate "
        "regression targets and should not be translated word-for-word.",
    )

    page.draw_rect(pymupdf.Rect(MARGIN, 302, 531, 404), color=(0.23, 0.41, 0.61), fill=(0.94, 0.97, 1.0), width=0.8)
    page.insert_text((MARGIN + 14, 328), "Protected formula region", fontsize=11, fontname="hebo", color=(0.04, 0.15, 0.27))
    page.insert_text((MARGIN + 24, 360), "scale = 1 / sqrt(d_k)", fontsize=16, fontname="cour", color=(0.02, 0.05, 0.08))
    page.insert_text((MARGIN + 24, 386), "loss = cross_entropy + label_smoothing", fontsize=12, fontname="cour", color=(0.02, 0.05, 0.08))

    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 438, 531, 540),
        "The two formulas are printed in a monospace font so the existing protection rules have a deterministic source "
        "signal. Future region inventory code must also preserve formulas when font metadata is incomplete or conflicting.",
    )

    page.draw_line((MARGIN, 590), (531, 590), color=(0.72, 0.76, 0.82), width=0.7)
    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 610, 531, 714),
        "Acceptance notes: preserve organisation names, preserve title casing where configured, retain formula glyphs, "
        "and produce a partial result rather than corrupting content that cannot be classified safely.",
        size=10.5,
        color=(0.23, 0.28, 0.35),
    )


def draw_arrow(page: pymupdf.Page, start: tuple[float, float], end: tuple[float, float]) -> None:
    page.draw_line(start, end, color=(0.08, 0.24, 0.43), width=1.2)
    x, y = end
    page.draw_line((x - 8, y - 4), end, color=(0.08, 0.24, 0.43), width=1.2)
    page.draw_line((x - 8, y + 4), end, color=(0.08, 0.24, 0.43), width=1.2)


def build_page_two(doc: pymupdf.Document) -> None:
    page = doc.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
    draw_header(page, "Vector attention visualisation", "All labels are original fixture content - page 2 of 2")

    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 82, 531, 130),
        "Figure 1. A vector graphic with English labels that must be preserved unless image translation is explicitly enabled.",
        size=12,
        font="hebo",
    )

    figure = pymupdf.Rect(72, 160, 523, 540)
    page.draw_rect(figure, color=(0.12, 0.29, 0.49), fill=(0.98, 0.99, 1.0), width=1.0)
    page.draw_rect(pymupdf.Rect(102, 224, 206, 292), color=(0.14, 0.42, 0.61), fill=(0.85, 0.94, 0.98), width=1.0)
    page.draw_rect(pymupdf.Rect(246, 224, 350, 292), color=(0.14, 0.42, 0.61), fill=(0.85, 0.94, 0.98), width=1.0)
    page.draw_rect(pymupdf.Rect(390, 224, 494, 292), color=(0.14, 0.42, 0.61), fill=(0.85, 0.94, 0.98), width=1.0)
    draw_arrow(page, (206, 258), (246, 258))
    draw_arrow(page, (350, 258), (390, 258))
    page.insert_text((122, 255), "Query", fontsize=14, fontname="hebo", color=(0.04, 0.15, 0.27))
    page.insert_text((267, 255), "Key", fontsize=14, fontname="hebo", color=(0.04, 0.15, 0.27))
    page.insert_text((407, 255), "Value", fontsize=14, fontname="hebo", color=(0.04, 0.15, 0.27))
    page.insert_text((167, 196), "The model will never be perfect.", fontsize=11, fontname="helv", color=(0.12, 0.16, 0.22))
    page.insert_text((139, 340), "Attention weights", fontsize=12, fontname="hebo", color=(0.04, 0.15, 0.27))

    bars = [(134, 0.36), (194, 0.71), (254, 0.52), (314, 0.86), (374, 0.43)]
    for x, weight in bars:
        height = 115 * weight
        page.draw_rect(pymupdf.Rect(x, 488 - height, x + 34, 488), color=None, fill=(0.19, 0.54, 0.75))
    page.draw_line((116, 488), (422, 488), color=(0.12, 0.18, 0.26), width=0.8)
    page.insert_text((118, 515), "source tokens: the / model / will / never / fail", fontsize=9.5, fontname="cour", color=(0.12, 0.16, 0.22))

    add_textbox(
        page,
        pymupdf.Rect(MARGIN, 572, 531, 684),
        "The entire boxed area is a vector figure. A future region inventory must recognise it through drawing geometry "
        "and preserve all labels. This test guards against garbled text caused by applying prose translation to PDF glyph "
        "order inside a diagram.",
        size=10.5,
        color=(0.23, 0.28, 0.35),
    )


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    doc.set_metadata({
        "format": "PDF 1.7",
        "title": "Academic ML PDF Translation Regression Fixture",
        "author": "dh-pdf-trans maintainers",
        "subject": "Self-authored regression fixture",
        "keywords": "PDF translation, terminology, formulas, vector figures",
        "creator": "dh-pdf-trans fixture generator",
        "producer": "dh-pdf-trans",
        "creationDate": "D:20260828000000Z",
        "modDate": "D:20260828000000Z",
    })
    build_page_one(doc)
    build_page_two(doc)
    doc.save(PDF_PATH, garbage=4, deflate=True, no_new_id=True)
    doc.close()

    digest = hashlib.sha256(PDF_PATH.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "fixture_id": "academic-v1",
        "file": PDF_PATH.name,
        "sha256": digest,
        "license": "CC0-1.0",
        "creator": "dh-pdf-trans maintainers",
        "pages": 2,
        "terms": TERMS,
        "expected_regions": [
            {"page": 1, "kind": "FORMULA", "description": "Two monospace formula lines"},
            {"page": 2, "kind": "FIGURE", "description": "Boxed vector attention visualisation with labels"},
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {PDF_PATH}")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
