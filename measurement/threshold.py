from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parent.parent


def main():
    IMAGE = ROOT / "images" / "calibration" / "calibration.jpg"

    image = cv2.imread(str(IMAGE))

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    blur = cv2.GaussianBlur(
        gray,
        (5,5),
        0
    )

    _, binary = cv2.threshold(
        blur,
        200,
        255,
        cv2.THRESH_BINARY
    )

    cv2.imshow("Binary", binary)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (5,5)
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    print(len(contours))
    output = image.copy()

    cv2.drawContours(
        output,
        contours,
        -1,
        (0,255,0),
        2
    )

    cv2.imshow(
        "Contours",
        output
    )
    largest = max(
        contours,
        key=cv2.contourArea
    )

    print(cv2.contourArea(largest))
    x,y,w,h = cv2.boundingRect(
        largest
    )

    result = image.copy()

    cv2.rectangle(
        result,
        (x,y),
        (x+w,y+h),
        (0,0,255),
        2
    )

    cv2.imshow(
        "Largest",
        result
    )


if __name__ == "__main__":
    main()
