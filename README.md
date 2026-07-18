# KOI Leather — Area Measurement

Measure the real-world area of an irregular leather hide from a single phone
photo, using a sheet of **A4 paper (210 × 297 mm)** as the scale reference.

The user clicks the four corners of the A4 sheet once to calibrate; after that,
any photo taken from the same camera position can be measured automatically.

---

## How it works

```
photo ─▶ click 4 A4 corners ─▶ homography (pixels → mm) ─▶ save
                                                             │
product photo ─▶ segment leather contour ─▶ warp contour to mm ─▶ area
```

1. **Calibration.** The four clicked A4 corners are mapped to a rectangle of
   `210 × 297` mm. Solving the 8-parameter perspective transform gives a
   homography `H` that converts any image pixel to millimetres on the floor
   plane. This corrects for camera tilt automatically (a homography is exact for
   a flat plane). See [`app/homography.py`](app/homography.py).

2. **Segmentation.** The leather outline is found by combining three thresholding
   methods (adaptive, Otsu, Canny) and keeping the largest candidate that passes
   area/solidity/edge-strength filters. See
   [`calibration/leather_detect.py`](calibration/leather_detect.py).

3. **Measurement.** The contour is transformed to millimetres with `H`, and the
   real area is the polygon area of the warped contour.

### A4-coverage visualization

To *show* how the area is produced (not just print a number), the app can tile
the leather with virtual A4 sheets:

- an infinite A4 grid is generated in real-world mm ([`calibration/a4_grid.py`](calibration/a4_grid.py)),
- each tile is clipped against the leather polygon with Shapely to get its
  coverage % ([`calibration/coverage.py`](calibration/coverage.py)),
- the grid is projected back into the photo via the inverse homography and drawn
  ([`calibration/visualization.py`](calibration/visualization.py)).

The UI presents four tabs — **Original → Contour → A4 Layout → Coverage**. This
is purely explanatory: **the measured area always comes from
`cv2.contourArea`**, never from the tiles. An invariant test asserts the tile
overlaps sum back to the measured area
([`tests/test_coverage.py`](tests/test_coverage.py)).

### Accuracy

Validated against a tape-measured sample (`images/CALIBRATION/calibration2.jpg`,
a 160 cm-long hide):

| Quantity        | Ground truth | Computed | Error |
|-----------------|--------------|----------|-------|
| Length          | 160 cm       | 157.4 cm | 1.6 % |
| Area            | —            | 9,073 cm² (≈ 0.91 m² / 90.7 dm² / 9.8 sq ft) | — |

This is locked in by [`tests/test_measurement_accuracy.py`](tests/test_measurement_accuracy.py).

**Accuracy tips:** keep the leather flat (folded/curled corners can't be
measured by a planar transform), keep the whole piece and the A4 sheet in frame,
and take the measurement photo from the same position used for calibration.

---

## Running locally

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows;  source .venv/bin/activate on Unix
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run it from the **project root** (so `app/static` and `app/templates` resolve).
Any of these module paths work: `app.main:app`, `api:app`, `api.index:app` —
but **not** `uvicorn api` alone, and the attribute must be `:app`.

Then open <http://localhost:8000>:

1. Load the A4 photo, click the 4 corners, press **Save Calibration**.
2. Load the product photo, press **Đo diện tích** — the measured area, unit
   conversions, and detected size are shown.

Run the tests with `pytest`.

To dump intermediate vision images while tuning, set `KOI_DEBUG=1` (they go to a
temp dir, or `KOI_DEBUG_DIR` if set) — never written in normal/production runs.

---

## API

| Method & path         | Purpose                                             |
|-----------------------|-----------------------------------------------------|
| `GET /`               | Web UI                                               |
| `POST /calibrate`     | Body `{points:[{x,y}×4]}` → computes & saves `H`     |
| `GET /calibration`    | Current calibration (if any)                         |
| `POST /calibration/load` | Reload calibration from disk into memory         |
| `DELETE /calibration` | Clear calibration (`?remove_disk=true` deletes file) |
| `POST /measure`       | multipart `file` → area + dimensions, or preview     |
| `POST /visualize`     | multipart `file` → measurement + A4-coverage stages  |

`POST /measure` returns, on success:

```json
{
  "message": "OK", "mode": "measured",
  "area_cm2": 9073.2, "area_dm2": 90.73, "area_m2": 0.907, "area_sqft": 9.77,
  "area_pia": 10.08,
  "width_cm": 89.9, "height_cm": 157.4,
  "detection_mode": "segmented",
  "paper_check": null
}
```

If no calibration is loaded it returns a `mode: "preview"` response instead of
processing the image.

---

## Deployment (Vercel)

`api/index.py` exposes the app for `@vercel/python` (see `vercel.json`).

- Requirements use **`opencv-python-headless`** — the GUI build fails to import
  on serverless Linux (missing `libGL`).
- The serverless filesystem is read-only and per-request ephemeral, so persisted
  calibration doesn't survive there; without it, `/measure` returns preview mode.
  For a real hosted measurement service you'd store the homography in external
  storage (DB / object store) rather than a local JSON file.

---

## Layout

```
app/            FastAPI web app (routes, homography, in-memory state, UI)
calibration/    calibration_manager (persistence) + vision (leather_detect,
                paper_detect); other files are standalone dev/experiment scripts
measurement/    calibration.json (persisted homography) + dev scripts
tests/          path, preview, and accuracy regression tests
api/index.py    Vercel entry point
```
