import json
import os
import tempfile
from pathlib import Path
import numpy as np

CALIBRATION_FILE = Path(__file__).resolve().parents[1] / "measurement" / "calibration.json"


def get_calibration_path():
    return CALIBRATION_FILE


def save_homography(H):
    """Atomically save homography H (numpy array) to calibration JSON."""
    data = {"homography": H.tolist()}

    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in same directory then atomically replace
    dirpath = str(CALIBRATION_FILE.parent)
    with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=4)
        tf.flush()
        tempname = tf.name

    # Atomic replace
    os.replace(tempname, str(CALIBRATION_FILE))


def load_homography():
    """Load homography from calibration file. Raises FileNotFoundError if missing."""
    with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return np.array(data["homography"], dtype=np.float32)
