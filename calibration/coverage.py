"""Per-tile A4 coverage analysis.

This is an *explanation* layer that sits on top of the measurement engine. It
answers "how many A4 sheets would it take to tile this leather, and how full is
each one?" — purely for visualization. It never changes the measured area,
which remains ``cv2.contourArea`` of the warped contour in
``calibration.leather_detect``.

All geometry here is done in real-world millimetres, where an A4 sheet is a
fixed 210 x 297 mm rectangle, so coverage percentages are physically meaningful
regardless of camera perspective.
"""

import numpy as np
from shapely.geometry import Polygon

from calibration.a4_grid import A4_WIDTH_MM, A4_HEIGHT_MM, generate_a4_grid

A4_AREA_MM2 = A4_WIDTH_MM * A4_HEIGHT_MM


def _leather_polygon(leather_real_pts):
    """Build a valid Shapely polygon from the leather contour (mm)."""
    pts = np.asarray(leather_real_pts, dtype=np.float64).reshape(-1, 2)
    poly = Polygon(pts)
    if not poly.is_valid:
        # buffer(0) repairs self-intersections / bowties without changing area
        poly = poly.buffer(0)
    return poly


def compute_coverage(leather_real_pts, tiles=None, min_fraction=0.005):
    """Compute how much of each A4 tile overlaps the leather.

    Parameters
    ----------
    leather_real_pts : (N, 2) array
        Leather contour in real-world millimetres.
    tiles : list[A4Tile] | None
        Pre-generated grid. If None, a grid covering the contour's bounding box
        is generated automatically.
    min_fraction : float
        Tiles covering less than this fraction of an A4 sheet are ignored (they
        are effectively outside the leather).

    Returns
    -------
    list[dict]
        One entry per covered tile, sorted by id::

            {"id": int, "coverage_pct": float, "covered_cm2": float,
             "polygon_mm": [(x, y), ...]}
    """
    leather = _leather_polygon(leather_real_pts)

    pts = np.asarray(leather_real_pts, dtype=np.float64).reshape(-1, 2)
    if tiles is None:
        tiles = generate_a4_grid(
            float(pts[:, 0].min()),
            float(pts[:, 1].min()),
            float(pts[:, 0].max()),
            float(pts[:, 1].max()),
        )

    covered = []
    for tile in tiles:
        overlap = leather.intersection(Polygon(tile.polygon)).area
        fraction = overlap / A4_AREA_MM2 if A4_AREA_MM2 else 0.0

        if fraction < min_fraction:
            continue

        covered.append(
            {
                "id": tile.id,
                "coverage_pct": round(min(100.0, fraction * 100.0), 1),
                "covered_cm2": round(overlap / 100.0, 1),
                "polygon_mm": [(float(px), float(py)) for px, py in tile.polygon],
            }
        )

    covered.sort(key=lambda t: t["id"])
    return covered


def coverage_summary(covered):
    """Aggregate figures for the covered tiles."""
    if not covered:
        return {"tile_count": 0, "full_tiles": 0, "equivalent_a4": 0.0}

    total_pct = sum(t["coverage_pct"] for t in covered)
    return {
        "tile_count": len(covered),
        "full_tiles": sum(1 for t in covered if t["coverage_pct"] >= 99.5),
        "equivalent_a4": round(total_pct / 100.0, 2),
    }
