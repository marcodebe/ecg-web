import io
from typing import Annotated, Optional

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import Response

from app.i18n import detect_language
from app.limiter import limiter
from app.config import get_settings
from app.routes.ecg import MEDIA_TYPES, _render

router = APIRouter(prefix="/ui", tags=["ui"])


def _rate_limit() -> str:
    return get_settings().rate_limit


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
