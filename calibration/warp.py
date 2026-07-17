import cv2
import numpy as np
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def find_all(filename, search_root):
    matches = []
    for root, dirs, files in os.walk(search_root):
        if filename in files:
            matches.append(os.path.join(root, filename))
    return matches

matches = find_all("calibration.jpg", PROJECT_ROOT)

if not matches:
    raise FileNotFoundError(f"Không tìm thấy 'calibration.jpg' trong: {PROJECT_ROOT}")
if len(matches) > 1:
    print("CẢNH BÁO: có nhiều file trùng tên 'calibration.jpg':")
    for m in matches:
        print(f"  - {m}")
    print(f"-> Đang dùng file đầu tiên: {matches[0]}")

image_path = matches[0]
image = cv2.imread(image_path)

if image is None:
    raise ValueError(f"Tìm thấy file nhưng không đọc được ảnh: {image_path}")

print(f"Ảnh: {image_path}")
print(f"Kích thước: {image.shape[1]} x {image.shape[0]} (rộng x cao)")

# 4 góc A4 (theo thứ tự: TL, TR, BR, BL)
pts = np.array([
    [12, 38],
    [341, 53],
    [346, 498],
    [19, 497]
], dtype=np.float32)

# --- Kiểm tra: vẽ 4 điểm lên ảnh để xác nhận chúng đúng là 4 góc tờ A4 ---
check = image.copy()
labels = ["TL", "TR", "BR", "BL"]
for (x, y), label in zip(pts, labels):
    cv2.circle(check, (int(x), int(y)), 8, (0, 0, 255), -1)
    cv2.putText(check, label, (int(x) + 12, int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

cv2.namedWindow("Kiem tra 4 diem", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Kiem tra 4 diem", 1000, 700)
cv2.imshow("Kiem tra 4 diem", check)
# --------------------------------------------------------------------------

# Kích thước thật của A4 (đơn vị pixel đầu ra)
width = 210 * 10
height = 297 * 10
dst = np.array([
    [0, 0],
    [width - 1, 0],
    [width - 1, height - 1],
    [0, height - 1]
], dtype=np.float32)

matrix = cv2.getPerspectiveTransform(pts, dst)
warped = cv2.warpPerspective(image, matrix, (width, height))

cv2.namedWindow("Original", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Original", 900, 650)
cv2.imshow("Original", image)

cv2.namedWindow("Warp A4", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Warp A4", 700, 990)
cv2.imshow("Warp A4", warped)

cv2.waitKey(0)
cv2.destroyAllWindows()
