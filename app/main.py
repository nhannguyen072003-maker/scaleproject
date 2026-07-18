from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router


class NoCacheStaticFiles(StaticFiles):
    """Serve static files but force browsers to revalidate every time.

    Browsers aggressively cache CSS/JS. During development that means an edited
    ``style.css`` / ``script.js`` silently keeps serving the old version until a
    manual hard-refresh — producing a page that mixes new HTML with stale assets
    and appears "broken". ``Cache-Control: no-cache`` makes the browser check
    with the server (via ETag/Last-Modified) before reusing a cached file, so it
    always picks up the latest without a full re-download.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


def _load_persisted_calibration():
    """Try to load a persisted calibration matrix into in-memory state.

    Never raises: a missing/corrupt calibration file or an unavailable
    calibration subsystem must not prevent the app from starting.
    """
    try:
        from calibration import calibration_manager
        from app.state import save_calibration_matrix

        try:
            H = calibration_manager.load_homography()
        except FileNotFoundError:
            H = None
        except Exception as exc:
            # don't crash startup for a bad calibration file; log and continue
            print(f"Warning: failed to load calibration on startup: {exc}")
            H = None

        if H is not None:
            save_calibration_matrix(H)
            print("Loaded calibration matrix on startup")
    except Exception as e:
        # If calibration subsystem unavailable, continue startup
        print(f"Calibration manager not available at startup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, try to load persisted calibration into in-memory state.
    _load_persisted_calibration()
    yield


app = FastAPI(title="KOI Leather Calibration", lifespan=lifespan)

app.mount(
    "/static",
    NoCacheStaticFiles(directory="app/static"),
    name="static"
)

app.include_router(router)
