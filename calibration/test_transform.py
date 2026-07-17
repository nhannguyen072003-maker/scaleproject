import cv2
import json
import numpy as np

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

# ==========================
# Test 4 góc A4
# ==========================

points = np.array([
    [[7, 37]],
    [[342, 51]],
    [[346, 499]],
    [[19, 498]]
], dtype=np.float32)

result = cv2.perspectiveTransform(
    points,
    H
)

print(result)