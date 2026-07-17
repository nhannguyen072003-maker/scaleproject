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

    try:
        raw_points = data.get("points", [])
        if not isinstance(raw_points, list):
            raise ValueError("Payload must contain a points array")

        points = []
        for p in raw_points:
            if not isinstance(p, dict) or "x" not in p or "y" not in p:
                raise ValueError("Each point must contain x and y")
            points.append([float(p["x"]), float(p["y"])])

        if len(points) != 4:
            return {"message": f"Cần đúng 4 điểm, nhận được {len(points)}."}

        H = compute(points)
        print(H)
        return {"message": "Calibration Saved!"}
    except Exception as exc:
        return {"message": f"Không thể lưu calibration: {exc}"}


@router.post("/measure")
async def measure(file: UploadFile = File(...)):
    try:
        from app.state import load_calibration_matrix
    except Exception as exc:
        return {"message": f"Measurement backend unavailable: {exc}"}

    H = load_calibration_matrix()
    if H is None:
        return {"message": "Chưa calibrate. Vui lòng calibrate trước khi đo."}

    try:
        import cv2
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

    area_cm2 = compute_area_cm2(image, np.array(H, dtype=np.float32))

    if area_cm2 is None:

        return {
            "message": "Không tìm thấy miếng da trong ảnh. Thử chụp lại với ánh sáng/nền rõ hơn."
        }

    return {
        "message": f"Diện tích ước tính: {area_cm2:.2f} cm²",
        "area_cm2": round(area_cm2, 2)
    }