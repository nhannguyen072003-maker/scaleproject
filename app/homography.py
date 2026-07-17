import numpy as np

from app.state import save_calibration_matrix


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

    save_calibration_matrix(H)
    return H
