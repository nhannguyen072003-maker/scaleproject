from dataclasses import dataclass
import math

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0


@dataclass
class A4Tile:
    id: int
    x: float
    y: float
    width: float = A4_WIDTH_MM
    height: float = A4_HEIGHT_MM

    @property
    def polygon(self):
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height),
        ]


def generate_a4_grid(min_x, min_y, max_x, max_y):
    """
    Sinh toàn bộ các ô A4 bao phủ bounding box (đơn vị mm).
    """

    start_x = math.floor(min_x / A4_WIDTH_MM) * A4_WIDTH_MM
    start_y = math.floor(min_y / A4_HEIGHT_MM) * A4_HEIGHT_MM

    end_x = math.ceil(max_x / A4_WIDTH_MM) * A4_WIDTH_MM
    end_y = math.ceil(max_y / A4_HEIGHT_MM) * A4_HEIGHT_MM

    tiles = []

    idx = 1

    y = start_y

    while y < end_y:

        x = start_x

        while x < end_x:

            tiles.append(
                A4Tile(
                    id=idx,
                    x=x,
                    y=y,
                )
            )

            idx += 1

            x += A4_WIDTH_MM

        y += A4_HEIGHT_MM

    return tiles