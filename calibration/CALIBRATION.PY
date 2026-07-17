import cv2
import json

# Đọc ảnh calibration
image = cv2.imread("images/calibration/calibration.jpg")

print("===== CALIBRATION =====")

# Sau này:
# 1. Detect A4
# 2. Lấy contour
# 3. Tính pixel/cm
# 4. Ghi calibration.json
