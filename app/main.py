from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routes.ecg import router as ecg_router
from app.routes.formats import router as formats_router
from app.routes.ui import router as ui_router

app = FastAPI(
    title="ECG DICOM Converter",
    description="Servizio di conversione file ECG DICOM in formato grafico tramite dicom-ecg-plot.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(ecg_router)
app.include_router(formats_router)
app.include_router(ui_router)

_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_static), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(_static / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}
