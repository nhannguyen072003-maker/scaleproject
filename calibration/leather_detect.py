import cv2
import numpy as np

from calibration.paper_detect import find_paper_contour, _local_texture_std


# =====================================================================
# Ngưỡng lọc contour ứng viên (tính theo % diện tích ảnh, KHÔNG dùng
# số pixel cố định như bản cũ — số pixel cố định sẽ sai hoàn toàn khi
# đổi độ phân giải camera).
# =====================================================================

MIN_AREA_FRAC = 0.03     # bỏ contour nhỏ hơn 3% ảnh (nhiễu)
MAX_AREA_FRAC = 0.75     # bỏ contour quá lớn (thường là viền ảnh/gradient ánh sáng)
MIN_SOLIDITY = 0.55      # contour phải "đặc", không rời rạc/lởm chởm
MAX_BORDER_TOUCH = 2     # chạm >=3/4 cạnh ảnh => coi là nền, không phải vật thể riêng biệt
MIN_EDGE_STRENGTH = 7.0  # biên phải là biên vật liệu thật, không phải gradient ánh sáng mềm


def _method_adaptive(gray):
    """Ngưỡng thích ứng — tốt khi ánh sáng không đều trên khung hình."""

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))

    contours = []

    for inv in (True, False):

        mode = cv2.THRESH_BINARY_INV if inv else cv2.THRESH_BINARY

        th = cv2.adaptiveThreshold(
            blur, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            mode,
            51, 5
        )

        closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)
        closed = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)

        cnts, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contours += cnts

    return contours


def _method_otsu(gray):
    """Ngưỡng Otsu toàn cục — tốt khi vật thể và nền có độ sáng khác biệt rõ."""

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))

    contours = []

    for mode in (cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV):

        _, th = cv2.threshold(blur, 0, 255, mode + cv2.THRESH_OTSU)

        closed = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)

        cnts, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contours += cnts

    return contours


def _method_canny(gray):
    """
    Biên cạnh Canny + morphological close với kernel LỚN để nối liền
    các đoạn biên bị đứt gãy (bản cũ dùng kernel 5x5 — quá nhỏ, đây là
    lý do chính khiến bản cũ không tìm thấy contour nào trên ảnh nền
    có texture, ví dụ đá vân mây).
    """

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    med = float(np.median(blur))

    lower = int(max(0, 0.66 * med))
    upper = int(min(255, 1.33 * med))

    edges = cv2.Canny(blur, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(
        closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    return contours


def _border_touch_count(c, h, w, tol=3):
    """Số cạnh ảnh (trong 4 cạnh) mà contour chạm vào."""

    x, y, cw, ch = cv2.boundingRect(c)

    touches = 0

    touches += x <= tol
    touches += y <= tol
    touches += (x + cw) >= (w - tol)
    touches += (y + ch) >= (h - tol)

    return touches


def _edge_strength(c, std_map, h, w, border_tol=3):
    """
    Cường độ biên trung bình dọc theo contour, đo bằng bản đồ texture-std
    cục bộ — phân biệt biên vật liệu thật (giá trị cao, xem paper_detect)
    với biên "ảo" tạo ra bởi gradient ánh sáng mềm (giá trị thấp).
    Bỏ qua các điểm nằm sát mép ảnh vì boxFilter cho giá trị không đáng
    tin cậy ở đó.
    """

    mask = np.zeros(std_map.shape, dtype=np.uint8)
    cv2.drawContours(mask, [c], -1, 255, 2)

    ys, xs = np.where(mask == 255)

    keep = (
        (xs > border_tol) & (xs < w - border_tol) &
        (ys > border_tol) & (ys < h - border_tol)
    )

    vals = std_map[ys[keep], xs[keep]]

    if len(vals) == 0:
        return 0.0

    return float(vals.mean())


def _valid_candidates(contours, image_shape, paper_hull, std_map):
    """Lọc + chấm điểm các contour ứng viên, trả về list (area, contour) đã sort giảm dần."""

    h, w = image_shape[:2]
    image_area = h * w

    out = []

    for c in contours:

        if len(c) < 3:
            continue

        area = cv2.contourArea(c)

        if area < image_area * MIN_AREA_FRAC:
            continue

        if area > image_area * MAX_AREA_FRAC:
            continue

        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)

        if hull_area <= 0:
            continue

        solidity = area / hull_area

        if solidity < MIN_SOLIDITY:
            continue

        # Contour chạm >=3 cạnh ảnh => giống nền/gradient ánh sáng hơn
        # là 1 vật thể riêng biệt đặt trên nền.
        if _border_touch_count(c, h, w) > MAX_BORDER_TOUCH:
            continue

        # Biên phải là biên vật liệu thật, không phải do gradient ánh
        # sáng mềm bị Otsu/adaptive threshold "cắt" nhầm thành contour.
        if _edge_strength(c, std_map, h, w) < MIN_EDGE_STRENGTH:
            continue

        # Bỏ ứng viên trùng vào vùng tờ giấy tham chiếu
        if paper_hull is not None:

            M = cv2.moments(c)

            if M["m00"] != 0:

                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]

                if cv2.pointPolygonTest(paper_hull, (cx, cy), False) >= 0:
                    continue

        out.append((area, c))

    out.sort(key=lambda t: t[0], reverse=True)

    return out


def find_product_contour(image):
    """
    Tìm vùng sản phẩm cần đo. Chiến lược 2 tầng:

    1) SEGMENTED: thử nhiều phương pháp threshold/edge khác nhau để
       tìm 1 contour "đặc", tách biệt khỏi nền — dùng khi sản phẩm
       nằm gọn trên nền tương phản (vd: da đặt trên nền khác màu).

    2) FULL_FRAME (fallback): nếu không phương pháp nào cho ra contour
       hợp lệ — thường xảy ra khi sản phẩm chiếm gần hết khung hình và
       không có đường biên khép kín rõ ràng (vd: chụp cận 1 tấm đá lớn,
       biên chỉ là các đường ron/grout bị cắt bởi mép ảnh) — coi TOÀN
       BỘ khung hình là sản phẩm, trừ đi vùng tờ giấy tham chiếu (nếu có).
       Cách này giả định camera cố định (rig/copy-stand) giữa lúc
       calibrate và lúc đo, giống như toàn bộ thiết kế hệ thống hiện tại
       (dùng chung 1 ma trận homography cho mọi ảnh đo).

    Trả về (contour, mode, paper_hull) với mode in {"segmented", "full_frame"}.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    paper_hull = find_paper_contour(image)
    std_map = _local_texture_std(gray)

    all_contours = []
    all_contours += _method_adaptive(gray)
    all_contours += _method_otsu(gray)
    all_contours += _method_canny(gray)

    candidates = _valid_candidates(all_contours, image.shape, paper_hull, std_map)

    if candidates:

        _, best_contour = candidates[0]

        return best_contour, "segmented", paper_hull

    # ---- Fallback: toàn khung hình trừ vùng giấy ----

    h, w = image.shape[:2]

    margin = max(1, int(0.005 * min(h, w)))

    frame = np.array([
        [[margin, margin]],
        [[w - 1 - margin, margin]],
        [[w - 1 - margin, h - 1 - margin]],
        [[margin, h - 1 - margin]]
    ], dtype=np.int32)

    return frame, "full_frame", paper_hull


def compute_area_cm2(image, H):

    contour, mode, paper_hull = find_product_contour(image)

    if contour is None:
        return None

    pts = contour.reshape(-1, 1, 2).astype(np.float32)

    real_pts = cv2.perspectiveTransform(pts, H)

    area_mm2 = cv2.contourArea(real_pts)

    # Ở chế độ full_frame, trừ đi diện tích tờ giấy tham chiếu
    # (giấy không phải là 1 phần của sản phẩm).
    if mode == "full_frame" and paper_hull is not None:

        paper_pts = paper_hull.reshape(-1, 1, 2).astype(np.float32)

        real_paper = cv2.perspectiveTransform(paper_pts, H)

        paper_area_mm2 = cv2.contourArea(real_paper)

        area_mm2 = max(area_mm2 - paper_area_mm2, 0)

    print(f"[leather_detect] mode={mode} area_mm2={area_mm2:.1f}")

    return area_mm2 / 100