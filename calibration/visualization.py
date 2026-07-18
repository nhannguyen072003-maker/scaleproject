"""Rendering layer for the A4-coverage visualization.

Turns a measurement into a set of annotated images (one per UI tab):

    original  ->  contour  ->  a4_layout  ->  coverage

This module only *draws*. It reads the leather contour from the detector and the
tile coverage from :mod:`calibration.coverage`, and never computes or alters the
measured area. Keeping it separate means the measurement engine stays clean.
"""

import base64

import cv2
import numpy as np

from calibration.coverage import compute_coverage, coverage_summary
from calibration.leather_detect import find_product_contour

# BGR colors
_GREEN = (0, 220, 0)
_BLUE = (255, 90, 0)
_CYAN = (255, 220, 0)


def encode_image(image, ext=".jpg", quality=82):
    """Encode a BGR image as a base64 data URI (JPEG by default)."""
    params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext == ".jpg" else []
    ok, buffer = cv2.imencode(ext, image, params)
    if not ok:
        return None
    mime = "jpeg" if ext == ".jpg" else "png"
    return f"data:image/{mime};base64," + base64.b64encode(buffer).decode("utf-8")


def _mm_to_px(points_mm, H_inv):
    """Project real-world (mm) points back into image pixels."""
    pts = np.asarray(points_mm, dtype=np.float32).reshape(-1, 1, 2)
    px = cv2.perspectiveTransform(pts, H_inv)
    return px.reshape(-1, 2).astype(np.int32)


def _coverage_color(pct):
    """Red (low) -> yellow -> green (high). Returns BGR."""
    t = max(0.0, min(1.0, pct / 100.0))
    return (0, int(255 * t), int(255 * (1 - t)))


def _draw_contour(image, contour, paper_hull):
    out = image.copy()
    cv2.drawContours(out, [contour], -1, _GREEN, 4, cv2.LINE_AA)
    if paper_hull is not None:
        cv2.drawContours(out, [paper_hull], -1, _BLUE, 3, cv2.LINE_AA)
    return out


def _draw_layout(image, contour, covered, H_inv):
    out = image.copy()
    for tile in covered:
        poly = _mm_to_px(tile["polygon_mm"], H_inv)
        cv2.polylines(out, [poly], True, _CYAN, 2, cv2.LINE_AA)
        cx, cy = poly.mean(axis=0).astype(int)
        cv2.putText(out, f"#{tile['id']}", (cx - 14, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, _CYAN, 2, cv2.LINE_AA)
    cv2.drawContours(out, [contour], -1, _GREEN, 3, cv2.LINE_AA)
    return out


def _draw_coverage(image, contour, covered, H_inv):
    fill = image.copy()
    for tile in covered:
        poly = _mm_to_px(tile["polygon_mm"], H_inv)
        cv2.fillPoly(fill, [poly], _coverage_color(tile["coverage_pct"]))

    out = cv2.addWeighted(fill, 0.45, image, 0.55, 0)

    for tile in covered:
        poly = _mm_to_px(tile["polygon_mm"], H_inv)
        cv2.polylines(out, [poly], True, (255, 255, 255), 1, cv2.LINE_AA)
        cx, cy = poly.mean(axis=0).astype(int)
        label = f"{tile['coverage_pct']:.0f}%"
        cv2.putText(out, label, (cx - 22, cy + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(out, label, (cx - 22, cy + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.drawContours(out, [contour], -1, _GREEN, 3, cv2.LINE_AA)
    return out


def build_stages(image, H):
    """Produce the full visualization payload for one image + homography.

    Returns ``None`` if no leather contour is found. Otherwise::

        {
          "stages": {"original", "contour", "a4_layout", "coverage"},  # data URIs
          "tiles": [{"id", "coverage_pct", "covered_cm2"}, ...],
          "summary": {"tile_count", "full_tiles", "equivalent_a4"},
        }
    """
    contour, mode, paper_hull = find_product_contour(image)
    if contour is None:
        return None

    H_inv = np.linalg.inv(H)

    real_pts = cv2.perspectiveTransform(
        contour.reshape(-1, 1, 2).astype(np.float32), H
    ).reshape(-1, 2)

    covered = compute_coverage(real_pts)

    stages = {
        "original": encode_image(image),
        "contour": encode_image(_draw_contour(image, contour, paper_hull)),
        "a4_layout": encode_image(_draw_layout(image, contour, covered, H_inv)),
        "coverage": encode_image(_draw_coverage(image, contour, covered, H_inv)),
    }

    tiles = [
        {"id": t["id"], "coverage_pct": t["coverage_pct"], "covered_cm2": t["covered_cm2"]}
        for t in covered
    ]

    return {
        "stages": stages,
        "tiles": tiles,
        "summary": coverage_summary(covered),
    }
