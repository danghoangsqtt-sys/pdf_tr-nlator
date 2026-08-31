"""Evidence-backed protected regions discovered from a rendered PDF page.

Coordinates are expressed in PyMuPDF page space (origin at top-left). The
converter's layout mask uses PDFMiner's lower-left coordinate space, so only
``protect_mask`` performs that conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil, floor
from typing import Any, Iterable


class RegionKind(str, Enum):
    """Content classifications used by the academic safety pipeline."""

    PROSE_SAFE = "PROSE_SAFE"
    FORMULA = "FORMULA"
    FIGURE = "FIGURE"
    TABLE = "TABLE"
    SCAN = "SCAN"
    UNKNOWN = "UNKNOWN"


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


def discover_regions(page: Any, *, min_vector_area_ratio: float = 0.08) -> list[Region]:
    """Discover high-confidence image and large vector figure regions.

    Small drawing clusters are often rules, underlines, or formula fraction
    bars. They deliberately stay out of this phase; formula classification is
    added separately by T-103.
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
    return regions


def protect_mask(
    mask: Any,
    regions: Iterable[Region],
    page_bbox: Any,
    *,
    kinds: frozenset[RegionKind] = frozenset({RegionKind.FIGURE}),
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
