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
    std_thresh=18,
    min_frac=0.005,
    max_frac=0.6,
    min_value=170,
    max_saturation=45
):
    """
    Tìm vùng tờ giấy tham chiếu (dùng để calibrate / loại trừ khỏi
    vùng sản phẩm). Trả về convex hull (Nx1x2 int32) hoặc None nếu
    không tìm thấy.

    Hoạt động tốt cả khi giấy có độ sáng gần giống nền (không phân
    biệt được bằng ngưỡng độ sáng đơn thuần), miễn giấy "trơn" hơn
    nền về texture.

    Chỉ dựa vào texture (độ mượt) là CHƯA ĐỦ — một sản phẩm mượt, đều
    màu (vd: da thuộc mịn) cũng có thể bị nhận nhầm thành giấy. Vì vậy
    sau khi tìm được vùng "mượt", cần kiểm tra thêm màu sắc: giấy
    tham chiếu phải sáng (V cao) và ít bão hòa màu (S thấp) — khác
    với hầu hết vật liệu/sản phẩm thực tế (da, đá, gỗ...) thường tối
    hơn hoặc có màu sắc rõ (S cao).
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    std = _local_texture_std(gray)

    _, edge_mask = cv2.threshold(
        std, std_thresh, 255, cv2.THRESH_BINARY
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))

    closed = cv2.morphologyEx(
        edge_mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=3
    )

    n, labels, stats, _ = cv2.connectedComponentsWithStats(
        closed, connectivity=8
    )

    if n <= 1:
        return None

    image_area = image.shape[0] * image.shape[1]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Duyệt các component theo diện tích giảm dần, chọn cái ĐẦU TIÊN
    # vừa đủ lớn/nhỏ hợp lý, vừa có màu giống giấy (sáng, ít bão hòa).
    candidates = []

    for i in range(1, n):

        area = stats[i, cv2.CC_STAT_AREA]

        if area < image_area * min_frac:
            continue

        if area > image_area * max_frac:
            continue

        candidates.append((area, i))

    candidates.sort(reverse=True)

    for area, label in candidates:

        mask = (labels == label).astype(np.uint8) * 255

        pts = cv2.findNonZero(mask)

        if pts is None:
            continue

        hull = cv2.convexHull(pts)

        # Kiểm tra màu sắc bên trong hull — phải sáng & ít bão hòa
        hull_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(hull_mask, [hull], -1, 255, -1)

        v_mean = hsv[:, :, 2][hull_mask == 255].mean()
        s_mean = hsv[:, :, 1][hull_mask == 255].mean()

        if v_mean >= min_value and s_mean <= max_saturation:
            return hull

    return None