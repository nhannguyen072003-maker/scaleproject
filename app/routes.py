from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File

import numpy as np

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    print("Rendering app/templates/index.html")

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@router.post("/calibrate")
async def calibrate(data: dict = Body(...)):
    try:
        from app.homography import compute
    except Exception as exc:
        return {"message": f"Calibration backend unavailable: {exc}"}

    points = []

    for p in data["points"]:
        points.append([
            p["x"],
            p["y"]
        ])

    if len(points) != 4:

        return {
            "message": f"Cần đúng 4 điểm, nhận được {len(points)}."
        }

    H = compute(points)

    print(H)

    return {
        "message": "Calibration Saved!"
    }


@router.post("/measure")
async def measure(file: UploadFile = File(...)):
    try:
        import cv2
        from calibration.calibration_manager import load_homography
        from calibration.leather_detect import compute_area_cm2
    except Exception as exc:
        return {"message": f"Measurement backend unavailable: {exc}"}

    print("Received:", file.filename)

    contents = await file.read()

    npimg = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if image is None:

        return {
            "message": "Không đọc được ảnh, thử lại với file khác."
        }

    try:
        H = load_homography()
    except FileNotFoundError:

        return {
            "message": "Chưa calibrate. Vui lòng calibrate trước khi đo."
        }

    area_cm2 = compute_area_cm2(image, H)

    if area_cm2 is None:

        return {
            "message": "Không tìm thấy miếng da trong ảnh. Thử chụp lại với ánh sáng/nền rõ hơn."
        }

    return {
        "message": f"Diện tích ước tính: {area_cm2:.2f} cm²",
        "area_cm2": round(area_cm2, 2)
    }