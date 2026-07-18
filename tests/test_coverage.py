"""Tests for the A4-coverage visualization layer.

The strongest guarantee here is an *invariant*: because the A4 grid tiles the
plane, the per-tile leather overlaps must partition the leather exactly, so
their sum equals the measured leather area. This ties the visualization to the
measurement engine without letting it drift.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from calibration.leather_detect import find_product_contour
from calibration.coverage import compute_coverage, coverage_summary
from calibration.visualization import build_stages

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "images" / "CALIBRATION" / "calibration2.jpg"

# Same frozen, validated calibration used by test_measurement_accuracy.
FIXTURE_HOMOGRAPHY = np.array(
    [
        [1.1876081710316568, -0.08212203772176188, -658.8045567265336],
        [0.1340579190499458, 1.1350237828462895, -1058.2299489640852],
        [-0.0001868983802594537, -0.00010373610225372643, 1.0],
    ],
    dtype=np.float32,
)


def _leather_real_pts(image):
    contour, _mode, _paper = find_product_contour(image)
    return cv2.perspectiveTransform(
        contour.reshape(-1, 1, 2).astype(np.float32), FIXTURE_HOMOGRAPHY
    ).reshape(-1, 2)


@pytest.mark.skipif(not IMAGE.exists(), reason="sample image not available")
def test_tile_overlaps_partition_the_leather_area():
    image = cv2.imread(str(IMAGE))
    real = _leather_real_pts(image)

    leather_area_cm2 = cv2.contourArea(real.reshape(-1, 1, 2)) / 100.0
    covered = compute_coverage(real)

    assert covered, "expected at least one covered tile"

    total_covered = sum(t["covered_cm2"] for t in covered)
    # Tiles tile the plane, so their leather-overlaps sum to the leather area.
    assert abs(total_covered - leather_area_cm2) / leather_area_cm2 < 0.02

    for t in covered:
        assert 0.0 < t["coverage_pct"] <= 100.0


@pytest.mark.skipif(not IMAGE.exists(), reason="sample image not available")
def test_build_stages_returns_all_tabs():
    image = cv2.imread(str(IMAGE))
    out = build_stages(image, FIXTURE_HOMOGRAPHY)

    assert set(out["stages"]) == {"original", "contour", "a4_layout", "coverage"}
    assert all(v.startswith("data:image") for v in out["stages"].values())

    summary = out["summary"]
    assert summary["tile_count"] == len(out["tiles"])
    assert coverage_summary(compute_coverage(_leather_real_pts(image))) == summary
