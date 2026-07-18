from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File

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

    print("========== MEASURE ==========")

    print(file.filename)

    return {
        "area_cm2": 99999
    }
    