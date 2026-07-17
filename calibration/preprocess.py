import cv2


def preprocess(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    edge = cv2.Canny(
        blur,
        50,
        150
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5, 5)
    )

    edge = cv2.dilate(
        edge,
        kernel,
        iterations=1
    )

    edge = cv2.erode(
        edge,
        kernel,
        iterations=1
    )

    return edge
