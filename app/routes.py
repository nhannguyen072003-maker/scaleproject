from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile, File, HTTPException
from typing import Optional

from app.schemas import CalibrateRequest

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    print("Rendering app/templates/index.html")
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/calibrate")
async def calibrate(payload: CalibrateRequest):
    try:
        from app.homography import compute
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Calibration backend unavailable: {exc}")

    try:
        raw_points = payload.points

        if len(raw_points) != 4:
            raise HTTPException(status_code=400, detail=f"Need exactly 4 points, got {len(raw_points)}.")

        points = [[float(p.x), float(p.y)] for p in raw_points]

        H = compute(points)

        # Persist homography to disk so other scripts/processes can use it
        try:
            from calibration import calibration_manager
            calibration_manager.save_homography(H)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Calibration computed but could not save to disk: {exc}")

        # Update in-memory state as well
        try:
            from app.state import save_calibration_matrix
            save_calibration_matrix(H)
        except Exception:
            pass

        print(H)
        return {"message": "Calibration Saved!", "mode": "calibrated"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not compute calibration: {exc}")


@router.get("/calibration")
async def get_calibration():
    """Return persisted calibration if available."""
    from calibration import calibration_manager
    from app.state import load_calibration_matrix

    H = load_calibration_matrix()
    if H is None:
        # try load from disk
        try:
            H = calibration_manager.load_homography()
        except FileNotFoundError:
            return {"exists": False, "homography": None}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to load calibration: {exc}")

    return {"exists": True, "homography": H.tolist()}


@router.post("/calibration/load")
async def reload_calibration():
    from calibration import calibration_manager
    from app.state import save_calibration_matrix

    try:
        H = calibration_manager.load_homography()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Calibration file not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load calibration: {exc}")

    save_calibration_matrix(H)
    return {"message": "Calibration loaded into memory", "mode": "calibrated"}


@router.delete("/calibration")
async def delete_calibration(remove_disk: Optional[bool] = Query(False)):
    """Clear in-memory calibration; if remove_disk True, delete persisted file too."""
    from app.state import clear_calibration_matrix
    from calibration import calibration_manager

    clear_calibration_matrix()

    if remove_disk:
        path = calibration_manager.get_calibration_path()
        try:
            if path.exists():
                path.unlink()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to remove calibration file: {exc}")

    return {"message": "Calibration cleared", "disk_removed": bool(remove_disk)}


@router.post("/measure")
async def measure(file: UploadFile = File(...)):
    from app.state import load_calibration_matrix

    print("========== MEASURE ==========")

    # Check calibration first. When it is missing we return a preview response
    # without touching OpenCV, so the public (preview-only) deployment stays
    # functional even where the heavy vision stack cannot load or run.
    H = load_calibration_matrix()

    print("H =", H)

    if H is None:
        # Standardized preview response when calibration is missing
        return {"message": "Preview mode: no calibration", "area_cm2": 0.0, "mode": "preview"}

    # Heavy image-processing dependencies are imported lazily, only when we are
    # actually going to process an image.
    import cv2
    import numpy as np

    from calibration.leather_detect import compute_area_cm2

    data = await file.read()

    image = cv2.imdecode(
        np.frombuffer(data, np.uint8),
        cv2.IMREAD_COLOR
    )

    if image is None:
        raise HTTPException(status_code=400, detail="Could not read image")

    result = compute_area_cm2(image, H)

    if result is None:
        raise HTTPException(status_code=422, detail="No leather region could be detected")

    print("AREA =", result["area_cm2"])

    return {"message": "OK", "mode": "measured", **result}


@router.post("/visualize")
async def visualize(file: UploadFile = File(...)):
    """Measure the leather AND return the A4-coverage visualization stages.

    The measured area is still produced by the unchanged measurement engine
    (``compute_area_cm2``); the A4 tiling is an explanatory overlay only.
    """
    from app.state import load_calibration_matrix

    print("========== VISUALIZE ==========")

    H = load_calibration_matrix()

    if H is None:
        return {"message": "Preview mode: no calibration", "mode": "preview"}

    import cv2
    import numpy as np

    from calibration.leather_detect import compute_area_cm2
    from calibration.visualization import build_stages

    data = await file.read()

    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Could not read image")

    measurement = compute_area_cm2(image, H)

    if measurement is None:
        raise HTTPException(status_code=422, detail="No leather region could be detected")

    visualization = build_stages(image, H)

    return {
        "message": "OK",
        "mode": "measured",
        "measurement": measurement,
        "visualization": visualization,
    }