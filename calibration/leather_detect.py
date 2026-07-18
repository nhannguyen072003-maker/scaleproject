import os
import tempfile

import cv2
import numpy as np

from calibration.paper_detect import (
    find_paper_contour,
    _local_texture_std,
)

# ==========================================================
# Debug image output
# ==========================================================
# Writing intermediate images is useful when tuning the pipeline locally, but
# it must never run on a read-only / serverless filesystem (it would crash) and
# it should not litter the working directory. Enable it by setting the env var
# KOI_DEBUG=1; output goes to a temp directory (or KOI_DEBUG_DIR if provided).

_DEBUG = os.environ.get("KOI_DEBUG", "").lower() in ("1", "true", "yes", "on")
_DEBUG_DIR = os.environ.get("KOI_DEBUG_DIR") or os.path.join(
    tempfile.gettempdir(), "koi_debug"
)


def _debug_write(name, image):
    """Write a debug image only when debugging is explicitly enabled."""
    if not _DEBUG:
        return
    try:
        os.makedirs(_DEBUG_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(_DEBUG_DIR, name), image)
    except Exception as exc:  # never let debug output break measurement
        print(f"[WARN] could not write debug image {name}: {exc}")

# ==========================================================
# Reference sheet dimensions (A4, millimetres)
# ==========================================================

A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297

# Leather-trade unit: 1 "pía" = a 30 x 30 cm square = 900 cm².
PIA_CM2 = 30 * 30


# ==========================================================
# Candidate filtering thresholds
# ==========================================================

MIN_AREA_FRAC = 0.03
MAX_AREA_FRAC = 0.75

MIN_SOLIDITY = 0.55
MAX_BORDER_TOUCH = 2
MIN_EDGE_STRENGTH = 7.0


# ==========================================================
# Adaptive Threshold
# ==========================================================

def _method_adaptive(gray):

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (9, 9),
    )

    contours = []

    for inv in (True, False):

        mode = (
            cv2.THRESH_BINARY_INV
            if inv
            else cv2.THRESH_BINARY
        )

        th = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            mode,
            51,
            5,
        )

        closed = cv2.morphologyEx(
            th,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2,
        )

        closed = cv2.morphologyEx(
            closed,
            cv2.MORPH_OPEN,
            kernel,
            iterations=1,
        )

        cnts, _ = cv2.findContours(
            closed,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        contours.extend(cnts)

    _debug_write("debug_adaptive.png", closed)

    return contours


# ==========================================================
# OTSU
# ==========================================================

def _method_otsu(gray):

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (9, 9),
    )

    contours = []

    for mode in (
        cv2.THRESH_BINARY,
        cv2.THRESH_BINARY_INV,
    ):

        _, th = cv2.threshold(
            blur,
            0,
            255,
            mode + cv2.THRESH_OTSU,
        )

        closed = cv2.morphologyEx(
            th,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2,
        )

        cnts, _ = cv2.findContours(
            closed,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        contours.extend(cnts)

    _debug_write("debug_otsu.png", closed)

    return contours
# ==========================================================
# CANNY
# ==========================================================

def _method_canny(gray):

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    med = np.median(blur)

    lower = int(max(0, med * 0.66))
    upper = int(min(255, med * 1.33))

    edges = cv2.Canny(
        blur,
        lower,
        upper,
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (15, 15),
    )

    closed = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2,
    )

    contours, _ = cv2.findContours(
        closed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    _debug_write("debug_edges.png", closed)

    return contours


# ==========================================================
# Border touch
# ==========================================================

def _border_touch_count(contour, h, w, tol=3):

    x, y, cw, ch = cv2.boundingRect(contour)

    touches = 0

    if x <= tol:
        touches += 1

    if y <= tol:
        touches += 1

    if x + cw >= w - tol:
        touches += 1

    if y + ch >= h - tol:
        touches += 1

    return touches


# ==========================================================
# Edge strength
# ==========================================================

def _edge_strength(
    contour,
    std_map,
    h,
    w,
    border_tol=3,
):

    mask = np.zeros(
        std_map.shape,
        dtype=np.uint8,
    )

    cv2.drawContours(
        mask,
        [contour],
        -1,
        255,
        2,
    )

    ys, xs = np.where(mask == 255)

    keep = (
        (xs > border_tol)
        & (xs < w - border_tol)
        & (ys > border_tol)
        & (ys < h - border_tol)
    )

    vals = std_map[
        ys[keep],
        xs[keep],
    ]

    if len(vals) == 0:
        return 0.0

    return float(vals.mean())
# ==========================================================
# Candidate filtering
# ==========================================================

def _valid_candidates(
    contours,
    image,
    paper_hull,
    std_map,
):

    h, w = image.shape[:2]
    image_area = h * w

    debug = image.copy()

    candidates = []

    for contour in contours:

        if len(contour) < 3:
            continue

        area = cv2.contourArea(contour)

        if area < image_area * MIN_AREA_FRAC:
            continue

        if area > image_area * MAX_AREA_FRAC:
            continue

        hull = cv2.convexHull(contour)

        hull_area = cv2.contourArea(hull)

        if hull_area <= 0:
            continue

        solidity = area / hull_area

        if solidity < MIN_SOLIDITY:
            continue

        if _border_touch_count(contour, h, w) > MAX_BORDER_TOUCH:
            continue

        edge = _edge_strength(
            contour,
            std_map,
            h,
            w,
        )

        if edge < MIN_EDGE_STRENGTH:
            continue

        if paper_hull is not None:

            M = cv2.moments(contour)

            if M["m00"] != 0:

                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]

                if cv2.pointPolygonTest(
                    paper_hull,
                    (cx, cy),
                    False,
                ) >= 0:
                    continue

        candidates.append((area, contour))

        cv2.drawContours(
            debug,
            [contour],
            -1,
            (0, 255, 0),
            3,
        )

    _debug_write("debug_candidates.jpg", debug)

    candidates.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return candidates


# ==========================================================
# Find product contour
# ==========================================================

def find_product_contour(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    std_map = _local_texture_std(gray)

    paper_hull = find_paper_contour(image)

    contours = []

    contours.extend(_method_adaptive(gray))
    contours.extend(_method_otsu(gray))
    contours.extend(_method_canny(gray))

    candidates = _valid_candidates(
        contours,
        image,
        paper_hull,
        std_map,
    )

    if len(candidates) > 0:

        area, contour = candidates[0]

        print(f"[INFO] segmented contour area = {area:.0f}")

        return contour, "segmented", paper_hull

    print("[INFO] fallback full frame")

    h, w = image.shape[:2]

    margin = max(
        1,
        int(min(h, w) * 0.005),
    )

    frame = np.array(
        [
            [[margin, margin]],
            [[w - margin, margin]],
            [[w - margin, h - margin]],
            [[margin, h - margin]],
        ],
        dtype=np.int32,
    )

    return frame, "full_frame", paper_hull


# ==========================================================
# Compute Area  (measurement engine — source of truth)
# ==========================================================

def compute_area_cm2(image, H):
    contour, mode, paper_hull = find_product_contour(image)

    if contour is None:
        print("[ERROR] No contour detected.")
        return None

    # ------------------------------------------------------
    # DEBUG: contour được chọn
    # ------------------------------------------------------

    debug = image.copy()

    cv2.drawContours(
        debug,
        [contour],
        -1,
        (0, 255, 0),
        5,
    )

    if paper_hull is not None:

        cv2.drawContours(
            debug,
            [paper_hull],
            -1,
            (255, 0, 0),
            3,
        )

    _debug_write("debug_contour.jpg", debug)

    # ------------------------------------------------------
    # Transform contour into real-world millimetres via the homography
    # ------------------------------------------------------

    pts = contour.reshape(-1, 1, 2).astype(np.float32)

    real_pts = cv2.perspectiveTransform(pts, H)

    area_mm2 = cv2.contourArea(real_pts)

    # Real-world bounding size — a robust, tape-measurable sanity check.
    flat = real_pts.reshape(-1, 2)
    width_mm = float(flat[:, 0].max() - flat[:, 0].min())
    height_mm = float(flat[:, 1].max() - flat[:, 1].min())

    # ------------------------------------------------------
    # Optional A4 self-check: re-measure the reference sheet through the
    # same homography and compare against its known area. Only runs when the
    # sheet was confidently detected.
    # ------------------------------------------------------

    paper_check = None

    if paper_hull is not None:

        paper_pts = paper_hull.reshape(-1, 1, 2).astype(np.float32)
        real_paper = cv2.perspectiveTransform(paper_pts, H)
        paper_area = cv2.contourArea(real_paper)

        expected = float(A4_WIDTH_MM * A4_HEIGHT_MM)
        error_pct = abs(paper_area - expected) / expected * 100.0

        paper_check = {
            "measured_cm2": round(paper_area / 100.0, 1),
            "expected_cm2": round(expected / 100.0, 1),
            "error_pct": round(error_pct, 1),
        }

        print("--------------------------------")
        print("PAPER AREA (mm²):", paper_area)
        print("EXPECTED A4    :", expected)
        print("A4 CHECK error :", f"{error_pct:.1f}%")
        print("--------------------------------")

        # In the full-frame fallback the contour is the whole image, so the
        # visible reference sheet is part of that area and must be removed.
        if mode == "full_frame":
            area_mm2 = max(area_mm2 - paper_area, 0)

    area_cm2 = area_mm2 / 100.0

    result = {
        "area_cm2": round(area_cm2, 1),
        "area_dm2": round(area_cm2 / 100.0, 2),
        "area_m2": round(area_cm2 / 10000.0, 3),
        "area_sqft": round(area_cm2 / 929.0304, 2),
        "area_pia": round(area_cm2 / PIA_CM2, 2),
        "width_cm": round(width_mm / 10.0, 1),
        "height_cm": round(height_mm / 10.0, 1),
        "detection_mode": mode,
        "paper_check": paper_check,
    }

    print("--------------------------------")
    print("MODE       :", mode)
    print("AREA cm²   :", result["area_cm2"])
    print("SIZE (cm)  :", result["width_cm"], "x", result["height_cm"])
    print("--------------------------------")

    return result