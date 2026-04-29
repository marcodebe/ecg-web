import io
from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.config import get_settings
from app.i18n import detect_language
from app.limiter import limiter
from app.routes.ecg import MEDIA_TYPES, _render

router = APIRouter(prefix="/ui", tags=["ui"])


def _rate_limit() -> str:
    return get_settings().rate_limit


def _sample_path(filename: str):
    """Restituisce il path del file campione, bloccando path traversal."""
    settings = get_settings()
    base = settings.sample_files_dir.resolve()
    target = (base / filename).resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Sample file not found.")
    return target


@router.get("/samples")
def list_samples() -> list[str]:
    """Elenca i file DICOM di esempio disponibili."""
    settings = get_settings()
    d = settings.sample_files_dir
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.suffix.lower() == ".dcm")


@router.post("/convert")
@limiter.limit(_rate_limit)
async def ui_convert(
    request: Request,
    file: Annotated[UploadFile, File()],
    layout: Annotated[str, Form()] = "3x4_1",
    paper: Annotated[str, Form()] = "a4",
    format: Annotated[str, Form()] = "png",
    minor_grid: Annotated[bool, Form()] = False,
    interpretation: Annotated[bool, Form()] = False,
    mm_mv: Annotated[float, Form()] = 10.0,
    accept_language: Optional[str] = Header(default=None),
) -> Response:
    lang = detect_language(accept_language)
    content = await file.read()
    data = _render(io.BytesIO(content), layout, paper, format, minor_grid, interpretation, mm_mv, lang)
    return Response(content=data, media_type=MEDIA_TYPES.get(format, "application/octet-stream"))


@router.post("/convert-sample")
@limiter.limit(_rate_limit)
async def ui_convert_sample(
    request: Request,
    filename: Annotated[str, Form()],
    layout: Annotated[str, Form()] = "3x4_1",
    paper: Annotated[str, Form()] = "a4",
    format: Annotated[str, Form()] = "png",
    minor_grid: Annotated[bool, Form()] = False,
    interpretation: Annotated[bool, Form()] = False,
    mm_mv: Annotated[float, Form()] = 10.0,
    accept_language: Optional[str] = Header(default=None),
) -> Response:
    lang = detect_language(accept_language)
    path = _sample_path(filename)
    data = _render(io.BytesIO(path.read_bytes()), layout, paper, format, minor_grid, interpretation, mm_mv, lang)
    return Response(content=data, media_type=MEDIA_TYPES.get(format, "application/octet-stream"))
