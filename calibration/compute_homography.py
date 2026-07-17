import cv2
import json
import os
import numpy as np

# =====================================
# 1. 4 điểm A4 (theo thứ tự)
# Top Left
# Top Right
# Bottom Right
# Bottom Left
# =====================================

image_points = np.array([
    [7, 37],
    [342, 51],
    [346, 499],
    [19, 498]
], dtype=np.float32)

# =====================================
# 2. Tọa độ thật của A4 (đơn vị mm)
# =====================================

real_points = np.array([
    [0, 0],
    [210, 0],
    [210, 297],
    [0, 297]
], dtype=np.float32)

# =====================================
# 3. Tính Homography
# =====================================

H = cv2.getPerspectiveTransform(
    image_points,
    real_points
)

print("========== HOMOGRAPHY ==========")
print(H)

# =====================================
# 4. Lưu calibration
# =====================================

calibration = {
    "paper": {
        "width_mm": 210,
        "height_mm": 297
    },
    "image_points": image_points.tolist(),
    "real_points": real_points.tolist(),
    "homography": H.tolist()
}

os.makedirs("measurement", exist_ok=True)

with open(
    "measurement/calibration.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        calibration,
        f,
        indent=4
    )

print("\nCalibration saved!")