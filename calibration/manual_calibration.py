import cv2
import os

# Đường dẫn ảnh

def main():
    image_path = "images/calibration/calibration.jpg"

    # Kiểm tra file tồn tại trước khi đọc
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Không tìm thấy file: {image_path}")

    image = cv2.imread(image_path)

    # Kiểm tra ảnh đọc thành công (imread trả None nếu lỗi, không raise exception)
    if image is None:
        raise ValueError(f"Không thể đọc ảnh (file có thể bị hỏng): {image_path}")

    clone = image.copy()

    # Danh sách chứa các điểm được click
    points = []
    MAX_POINTS = 4

    def mouse(event, x, y, flags, param):
        nonlocal image
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) >= MAX_POINTS:
                print(f"Đã đủ {MAX_POINTS} điểm, không nhận thêm.")
                return
            points.append((x, y))
            cv2.circle(image, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(
                image,
                str(len(points)),
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )
            print(f"Point {len(points)} : ({x}, {y})")

    cv2.namedWindow("Calibration")
    cv2.setMouseCallback("Calibration", mouse)

    while True:
        cv2.imshow("Calibration", image)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC để thoát
            break
        elif key == ord('r'):  # 'r' để reset lại các điểm
            image = clone.copy()
            points = []
            print("Đã reset các điểm.")
        elif len(points) == MAX_POINTS:
            print(f"Đã click đủ {MAX_POINTS} điểm, tự động thoát.")
            break

    cv2.destroyAllWindows()

    print("===== RESULT =====")
    print(points)


if __name__ == "__main__":
    main()
