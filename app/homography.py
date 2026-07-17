import json
from pathlib import Path

import numpy as np


A4_WIDTH = 210
A4_HEIGHT = 297


def compute(points):
    src = np.array(points, dtype=np.float32)
    dst = np.array(
        [
            [0, 0],
            [A4_WIDTH, 0],
            [A4_WIDTH, A4_HEIGHT],
            [0, A4_HEIGHT],
        ],
        dtype=np.float32,
    )

    A = []
    b = []
    for s, d in zip(src, dst):
        x, y = s
        u, v = d
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append([u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append([v])

    A = np.array(A, dtype=np.float64)
    b = np.array(b, dtype=np.float64)
    coeffs, *_ = np.linalg.lstsq(A, b, rcond=None)

    H = np.array(
        [
            [coeffs[0, 0], coeffs[1, 0], coeffs[2, 0]],
            [coeffs[3, 0], coeffs[4, 0], coeffs[5, 0]],
            [coeffs[6, 0], coeffs[7, 0], 1.0],
        ],
        dtype=np.float64,
    )

    output_path = Path(__file__).resolve().parents[1] / "measurement" / "calibration.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"homography": H.tolist()}, f, indent=4)

    return H
