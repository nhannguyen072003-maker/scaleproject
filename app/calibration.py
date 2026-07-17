import cv2
import numpy as np
import json


A4_WIDTH = 210
A4_HEIGHT = 297


def compute(points):

    src = np.array(points, dtype=np.float32)

    dst = np.array(
        [
            [0, 0],
            [A4_WIDTH, 0],
            [A4_WIDTH, A4_HEIGHT],
            [0, A4_HEIGHT]
        ],
        dtype=np.float32
    )

    H = cv2.getPerspectiveTransform(src, dst)

    with open(
        "measurement/calibration.json",
        "w"
    ) as f:

        json.dump(

            {

                "homography": H.tolist()

            },

            f,

            indent=4

        )

    return H