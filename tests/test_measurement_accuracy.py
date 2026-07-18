"""End-to-end accuracy regression test.

Anchored to a real, tape-measured ground truth: the leather sheet in
``images/CALIBRATION/calibration2.jpg`` is 160 cm long, photographed together
with an A4 reference.

The homography below is a *frozen*, validated calibration for that exact photo
(clicked A4 corners → 210×297 mm). It is intentionally hard-coded rather than
read from ``measurement/calibration.json`` so this test measures the **vision
pipeline** deterministically — the on-disk calibration is mutable and changes
every time a user re-calibrates through the app, which would make the test flaky
and, worse, let an imprecise click silently "fail" correct pipeline code.

If a future change to the segmentation or transform math regresses the scale,
this test fails loudly instead of silently returning a wrong area.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from calibration.leather_detect import compute_area_cm2

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "images" / "CALIBRATION" / "calibration2.jpg"

GROUND_TRUTH_LENGTH_CM = 160.0

# Frozen calibration validated against the 160 cm ground truth (≈1.6% error).
FIXTURE_HOMOGRAPHY = np.array(
    [
        [1.1876081710316568, -0.08212203772176188, -658.8045567265336],
        [0.1340579190499458, 1.1350237828462895, -1058.2299489640852],
        [-0.0001868983802594537, -0.00010373610225372643, 1.0],
    ],
    dtype=np.float32,
)


@pytest.mark.skipif(not IMAGE.exists(), reason="sample image not available")
def test_leather_length_matches_ground_truth():
    image = cv2.imread(str(IMAGE))
    assert image is not None, "could not read sample image"

    result = compute_area_cm2(image, FIXTURE_HOMOGRAPHY)
    assert result is not None

    # The longer detected side should match the 160 cm physical length.
    detected_length = max(result["width_cm"], result["height_cm"])
    error = abs(detected_length - GROUND_TRUTH_LENGTH_CM) / GROUND_TRUTH_LENGTH_CM

    assert error < 0.05, (
        f"detected length {detected_length} cm is "
        f"{error * 100:.1f}% off the 160 cm ground truth"
    )

    # Sanity: area should be plausible for a piece this size, not the
    # sub-1000 cm2 or multi-square-metre values that signal a blowup.
    assert 6000 < result["area_cm2"] < 12000


@pytest.mark.skipif(not IMAGE.exists(), reason="sample image not available")
def test_result_has_expected_fields():
    image = cv2.imread(str(IMAGE))
    result = compute_area_cm2(image, FIXTURE_HOMOGRAPHY)

    for key in (
        "area_cm2",
        "area_dm2",
        "area_m2",
        "area_sqft",
        "area_pia",
        "width_cm",
        "height_cm",
        "detection_mode",
        "paper_check",
    ):
        assert key in result
