import json
import os
from pathlib import Path
import numpy as np

CALIBRATION_FILE = Path(__file__).resolve().parents[1] / "measurement" / "calibration.json"


def get_calibration_path():
    return CALIBRATION_FILE


def save_homography(H):

    data = {

        "homography": H.tolist()

    }

    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(
        CALIBRATION_FILE,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


def load_homography():

    with open(
        CALIBRATION_FILE,
        "r"
    ) as f:

        data = json.load(f)

    return np.array(
        data["homography"],
        dtype=np.float32
    )