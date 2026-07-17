from __future__ import annotations

from typing import Optional


_calibration_matrix: Optional[list[list[float]]] = None


def save_calibration_matrix(matrix):
    global _calibration_matrix
    _calibration_matrix = matrix.tolist()
    return _calibration_matrix


def load_calibration_matrix():
    return _calibration_matrix
