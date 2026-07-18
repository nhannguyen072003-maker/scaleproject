import cv2
import numpy as np


def _local_texture_std(gray, k=15):
    """
    Bản đồ độ lệch chuẩn cục bộ (texture). Giấy trơn có std thấp,
    còn nền đá/gỗ/da có vân => std cao. Biên giữa giấy và nền tạo
    thành 1 đường viền std cao rất rõ, kể cả khi độ sáng giấy/nền
    gần giống nhau (trường hợp Canny thường bị fail).
    """

    gray = gray.astype(np.float32)

    mean = cv2.boxFilter(gray, -1, (k, k))
    sq_mean = cv2.boxFilter(gray * gray, -1, (k, k))

    var = sq_mean - mean * mean
    var[var < 0] = 0

    return np.sqrt(var).astype(np.uint8)


def find_paper_contour(
    image,
    min_value=200,
    max_saturation=60,
    texture_thresh=14,
    min_frac=0.003,
    max_frac=0.5,
    min_rectangularity=0.80,
    max_aspect=2.2,
):
    """Locate the A4 reference sheet and return its convex hull.

    Returns an ``Nx1x2`` int32 convex hull, or ``None`` when no sufficiently
    paper-like rectangle is found.

    A reference sheet has three distinguishing properties versus leather,
    stone, wood or a marble floor:

    * bright        -> high HSV Value (V)
    * uncolored     -> low HSV Saturation (S)
    * smooth        -> low local texture std (no grain / veins)

    We combine all three into a single mask, then keep only the largest
    blob that is genuinely *rectangular* (fills most of its min-area
    bounding box) with a plausible A4 aspect ratio (~1.414). The shape gate
    is important: on a bright marble floor the sheet can bleed into
    equally-bright floor patches, producing a large but ragged blob — that
    blob is rejected rather than mis-reported as the sheet, so callers get a
    trustworthy hull or an honest ``None``.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    std = _local_texture_std(gray)

    paper_like = (
        (hsv[:, :, 2] >= min_value)
        & (hsv[:, :, 1] <= max_saturation)
        & (std < texture_thresh)
    ).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    paper_like = cv2.morphologyEx(paper_like, cv2.MORPH_OPEN, kernel, iterations=1)
    paper_like = cv2.morphologyEx(paper_like, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(
        paper_like, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    image_area = image.shape[0] * image.shape[1]

    best_hull = None
    best_area = 0.0

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < image_area * min_frac or area > image_area * max_frac:
            continue

        (_, _), (rw, rh), _ = cv2.minAreaRect(contour)

        if min(rw, rh) == 0:
            continue

        rectangularity = area / (rw * rh)
        aspect = max(rw, rh) / min(rw, rh)

        # Must actually look like a rectangular sheet, not a ragged blob.
        if rectangularity < min_rectangularity or aspect > max_aspect:
            continue

        if area > best_area:
            best_area = area
            best_hull = cv2.convexHull(contour)

    return best_hull