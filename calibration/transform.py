import cv2
import json
import numpy as np


def load_h():

    with open("measurement/calibration.json") as f:

        H = np.array(
            json.load(f)["homography"],
            dtype=np.float32
        )

    return H


def transform(points):

    H = load_h()

    pts = np.array(
        points,
        dtype=np.float32
    ).reshape(-1,1,2)

    return cv2.perspectiveTransform(
        pts,
        H
    )