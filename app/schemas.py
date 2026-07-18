from pydantic import BaseModel
from typing import List


class Point(BaseModel):
    x: float
    y: float


class CalibrateRequest(BaseModel):
    points: List[Point]
