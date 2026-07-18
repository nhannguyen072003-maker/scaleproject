import cv2
from calibration.perspective import warp_perspective
from calibration.preprocess import preprocess
from calibration.detect_a4 import detect_contours
from calibration.contour_filter import find_best_paper


def main():
    image = cv2.imread("images/calibration/calibration.jpg")

    if image is None:
        print("Không đọc được ảnh!")
        return

    binary = preprocess(image)

    contours = detect_contours(binary)

    paper = find_best_paper(contours)

    if paper is not None:
        warped = warp_perspective(image, paper)
        cv2.imshow("Warp", warped)
    else:
        print("Không tìm thấy A4!")

    cv2.imshow("Original", image)
    cv2.imshow("Binary", binary)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
