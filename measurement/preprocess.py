from pathlib import Path
import cv2

# Thư mục gốc project
ROOT = Path(__file__).resolve().parent.parent

image_path = ROOT / "images" / "calibration" / "calibration.jpg"

print(image_path)

image = cv2.imread(str(image_path))

if image is None:
    raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

blur = cv2.GaussianBlur(gray, (5,5), 0)

cv2.imshow("Original", image)
cv2.imshow("Gray", gray)
cv2.imshow("Blur", blur)

cv2.waitKey(0)
cv2.destroyAllWindows()
