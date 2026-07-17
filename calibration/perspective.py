import cv2
import numpy as np


def order_points(points):

    points = points.reshape(4, 2)

    rect = np.zeros((4, 2), dtype=np.float32)

    s = points.sum(axis=1)

    rect[0] = points[np.argmin(s)]
    rect[2] = points[np.argmax(s)]

    diff = np.diff(points, axis=1)

    rect[1] = points[np.argmin(diff)]
    rect[3] = points[np.argmax(diff)]

    return rect


def warp_perspective(image, paper):

    rect = order_points(paper)

    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)

    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)

    maxHeight = int(max(heightA, heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(rect, dst)

    warped = cv2.warpPerspective(
        image,
        matrix,
        (maxWidth, maxHeight)
    )

    return warped
