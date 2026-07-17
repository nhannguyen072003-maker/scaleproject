from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router

app = FastAPI(title="KOI Leather Calibration")

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

app.include_router(router)