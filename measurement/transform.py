import cv2
import json
import numpy as np
from calibration import calibration_manager


def load_h():
    path = calibration_manager.get_calibration_path()
    with open(path, 'r') as f:
        H = np.array(json.load(f)["homography"], dtype=np.float32)
    return H


def transform(points):
    H = load_h()
    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    return cv2.perspectiveTransform(pts, H)
