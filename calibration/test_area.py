import cv2
import json
import numpy as np

# ===========================
# Load calibration
# ===========================

with open(
    "measurement/calibration.json",
    "r",
    encoding="utf-8"
) as f:

    calibration = json.load(f)

H = np.array(
    calibration["homography"],
    dtype=np.float32
)

# ===========================
# Contour giả lập
# (Pixel)
# ===========================

contour = np.array([
    [[7,37]],
    [[342,51]],
    [[346,499]],
    [[19,498]]
], dtype=np.float32)

# ===========================
# Area trước transform
# ===========================

pixel_area = cv2.contourArea(contour)

print("Pixel Area")
print(pixel_area)

# ===========================
# Transform
# ===========================

real_contour = cv2.perspectiveTransform(
    contour,
    H
)

print("\nReal Contour")
print(real_contour)

# ===========================
# Area sau transform
# ===========================

real_area = cv2.contourArea(
    real_contour
)

print("\nReal Area (mm²)")
print(real_area)

print("\nReal Area (cm²)")
print(real_area / 100)