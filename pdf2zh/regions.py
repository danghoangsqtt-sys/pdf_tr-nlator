"""Evidence-backed protected regions discovered from a rendered PDF page.

Coordinates are expressed in PyMuPDF page space (origin at top-left). The
converter's layout mask uses PDFMiner's lower-left coordinate space, so only
``protect_mask`` performs that conversion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from math import ceil, floor
from typing import Any, Iterable, Mapping

from pdf2zh.rules import is_formula_font


class RegionKind(str, Enum):
    """Content classifications used by the academic safety pipeline."""

    PROSE_SAFE = "PROSE_SAFE"
    FORMULA = "FORMULA"
    FIGURE = "FIGURE"
    TABLE = "TABLE"
    SCAN = "SCAN"
    UNKNOWN = "UNKNOWN"


PROTECTED_REGION_KINDS = frozenset(
    {
        RegionKind.FIGURE,
        RegionKind.FORMULA,
        RegionKind.SCAN,
        RegionKind.UNKNOWN,
    }
)

MATH_UNICODE_RANGES = (
    (0x2200, 0x22FF),
    (0x27C0, 0x27EF),
    (0x2900, 0x2BFF),
    (0x1D400, 0x1D7FF),
)
FORMULA_OPERATORS = frozenset("=+-*/^_<>|~\\")


@dataclass(frozen=True)
class Region:
    """A page-space rectangle with the evidence that caused protection."""

    kind: RegionKind
    bbox: tuple[float, float, float, float]
    confidence: str
    evidence: tuple[str, ...]

    @property
    def area(self) -> float:
        x0, y0, x1, y1 = self.bbox
        return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _bbox(value: Any) -> tuple[float, float, float, float] | None:
    """Return a valid rectangle tuple from a PyMuPDF-like value."""
    try:
        x0, y0, x1, y1 = (float(item) for item in value)
    except (TypeError, ValueError):
        return None
    if x1 <= x0 or y1 <= y0:
        return None
    return x0, y0, x1, y1


def _contains_math_unicode(text: str) -> bool:
    return any(
        lower <= ord(character) <= upper
        for character in text
        for lower, upper in MATH_UNICODE_RANGES
    )


def _formula_regions(page: Any, page_bbox: tuple[float, float, float, float]) -> list[Region]:
    """Classify formula-looking text lines without relying on one PDF font."""
    try:
        text = page.get_text("dict")
        blocks = text.get("blocks", ()) if isinstance(text, Mapping) else ()
    except (AttributeError, RuntimeError, ValueError):
        return []

    page_width = page_bbox[2] - page_bbox[0]
    page_height = page_bbox[3] - page_bbox[1]
    regions: list[Region] = []
    for block in blocks:
        if not isinstance(block, Mapping) or block.get("type") != 0:
            continue
        for line in block.get("lines", ()):
            if not isinstance(line, Mapping):
                continue
            spans = [
                span
                for span in line.get("spans", ())
                if isinstance(span, Mapping) and _bbox(span.get("bbox")) is not None
            ]
            if not spans:
                continue
            content = "".join(str(span.get("text", "")) for span in spans).strip()
            if not content:
                continue
            span_boxes = [_bbox(span.get("bbox")) for span in spans]
            boxes = [box for box in span_boxes if box is not None]
            x0 = min(box[0] for box in boxes)
            y0 = min(box[1] for box in boxes)
            x1 = max(box[2] for box in boxes)
            y1 = max(box[3] for box in boxes)
            bbox = (x0, y0, x1, y1)

            formula_fonts = sorted(
                {
                    str(span.get("font", ""))
                    for span in spans
                    if is_formula_font(str(span.get("font", "")))
                }
            )
            has_unicode_math = _contains_math_unicode(content)
            operator_count = sum(character in FORMULA_OPERATORS for character in content)
            structural_syntax = any(character in content for character in "_^/()[]{}")
            has_digit = any(character.isdigit() for character in content)
            word_count = len(re.findall(r"[A-Za-z]+", content))
            short_geometry = (
                x1 - x0 <= page_width * 0.85 and y1 - y0 <= page_height * 0.08
            )
            syntax_signal = (
                operator_count >= 2
                and (has_digit or structural_syntax or "=" in content)
                and (word_count <= 3 or structural_syntax)
            )

            evidence: list[str] = []
            if formula_fonts:
                evidence.extend(f"formula-font:{font}" for font in formula_fonts)
            if has_unicode_math:
                evidence.append("unicode-math")
            if syntax_signal:
                evidence.append(f"formula-syntax:operators={operator_count}")
            if short_geometry:
                evidence.append("single-line-geometry")

            if formula_fonts or has_unicode_math:
                regions.append(Region(RegionKind.FORMULA, bbox, "high", tuple(evidence)))
            elif syntax_signal and short_geometry:
                # A plausible equation without reliable font or Unicode metadata
                # is deliberately kept rather than being sent to translation.
                regions.append(Region(RegionKind.UNKNOWN, bbox, "low", tuple(evidence)))
    return regions


def discover_regions(
    page: Any,
    *,
    min_vector_area_ratio: float = 0.08,
    min_scan_area_ratio: float = 0.5,
) -> list[Region]:
    """Discover evidence-backed figure, scan, and formula regions.

    Small drawing clusters are often rules, underlines, or formula fraction
    bars, so vector discovery only accepts a substantial portion of the page.
    Formula classification uses text metadata instead of drawing geometry.
    """
    page_bbox = _bbox(getattr(page, "rect", None))
    if page_bbox is None:
        return []
    page_area = (page_bbox[2] - page_bbox[0]) * (page_bbox[3] - page_bbox[1])
    if page_area <= 0:
        return []

    regions: list[Region] = []
    try:
        images: Iterable[dict[str, Any]] = page.get_image_info()
    except (AttributeError, RuntimeError, ValueError):
        images = ()
    for image in images:
        bbox = _bbox(image.get("bbox"))
        if bbox is not None:
            regions.append(Region(RegionKind.FIGURE, bbox, "high", ("image",)))
            image_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            if image_area / page_area > min_scan_area_ratio:
                regions.append(
                    Region(
                        RegionKind.SCAN,
                        bbox,
                        "high",
                        ("image", f"coverage={image_area / page_area:.3f}"),
                    )
                )

    try:
        clusters: Iterable[Any] = page.cluster_drawings()
    except (AttributeError, RuntimeError, ValueError):
        clusters = ()
    for cluster in clusters:
        bbox = _bbox(cluster)
        if bbox is None:
            continue
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area / page_area >= min_vector_area_ratio:
            regions.append(Region(RegionKind.FIGURE, bbox, "high", ("vector-drawing",)))
    regions.extend(_formula_regions(page, page_bbox))
    return regions


def protect_mask(
    mask: Any,
    regions: Iterable[Region],
    page_bbox: Any,
    *,
    kinds: frozenset[RegionKind] = PROTECTED_REGION_KINDS,
) -> int:
    """Set protected regions to zero in a lower-left-origin layout mask.

    Returns how many regions intersected the mask. Values are clipped so an
    imperfect detector cannot index beyond the raster page.
    """
    source = _bbox(page_bbox)
    if source is None or len(mask.shape) < 2:
        return 0
    page_x0, page_y0, page_x1, page_y1 = source
    page_width, page_height = page_x1 - page_x0, page_y1 - page_y0
    if page_width <= 0 or page_height <= 0:
        return 0
    height, width = int(mask.shape[0]), int(mask.shape[1])
    protected = 0
    for region in regions:
        if region.kind not in kinds:
            continue
        x0, y0, x1, y1 = region.bbox
        left = max(0, min(width, floor((x0 - page_x0) / page_width * width)))
        right = max(0, min(width, ceil((x1 - page_x0) / page_width * width)))
        # Page coordinates grow down while PDFMiner's layout coordinates grow up.
        bottom = max(0, min(height, floor((page_y1 - y1) / page_height * height)))
        top = max(0, min(height, ceil((page_y1 - y0) / page_height * height)))
        if right <= left or top <= bottom:
            continue
        mask[bottom:top, left:right] = 0
        protected += 1
    return protected
