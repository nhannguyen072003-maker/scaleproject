import cv2


def find_best_paper(contours):

    best_paper = None
    best_score = float("inf")

    for i, contour in enumerate(contours):

        area = cv2.contourArea(contour)

        print(f"Contour {i}")
        print(f"Area     : {area}")

        x, y, w, h = cv2.boundingRect(contour)
        print(f"Bounding : {w} x {h}")

        # Bỏ contour quá nhỏ
        if area < 30000:
            continue

        perimeter = cv2.arcLength(contour, True)

        approx = cv2.approxPolyDP(
            contour,
            0.02 * perimeter,
            True
        )

        if len(approx) != 4:
            continue

        if not cv2.isContourConvex(approx):
            continue

        rect = cv2.minAreaRect(approx)

        width = rect[1][0]
        height = rect[1][1]

        if width == 0 or height == 0:
            continue

        ratio = max(width, height) / min(width, height)

        score = abs(ratio - 1.414)

        print("----------------------------")
        print("Width  :", round(width, 2))
        print("Height :", round(height, 2))
        print("Ratio  :", round(ratio, 3))
        print("Score  :", round(score, 3))

        if score < best_score:
            best_score = score
            best_paper = approx

    return best_paper
