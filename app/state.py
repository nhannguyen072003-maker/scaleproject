from __future__ import annotations
import threading
from typing import Optional

# Thread-safe calibration holder

class CalibrationState:
    def __init__(self):
        self._lock = threading.RLock()
        self._matrix: Optional[object] = None

    def save(self, matrix):
        with self._lock:
            self._matrix = matrix

    def load(self):
        with self._lock:
            return self._matrix

    def clear(self):
        with self._lock:
            self._matrix = None


# Backwards-compatible module-level functions used elsewhere
_state = CalibrationState()


def save_calibration_matrix(matrix):
    """Save matrix into thread-safe state."""
    _state.save(matrix)


def load_calibration_matrix():
    """Return current matrix or None."""
    return _state.load()


def clear_calibration_matrix():
    _state.clear()


def _get_internal_state():
    """Internal helper for tests / advanced operations."""
    return _state
