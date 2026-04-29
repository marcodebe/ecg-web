import io
import logging
import sys
from pathlib import Path
from typing import Annotated, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.auth import require_api_key
from app.config import get_settings
from app.i18n import detect_language, t
from app.limiter import limiter

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dicom-ecg-plot"))

from ecg.ecg import ECG  # noqa: E402

router = APIRouter(prefix="/api/ecg", tags=["ecg"])

SUPPORTED_FORMATS = {"png", "pdf", "svg", "tiff", "jpg", "jpeg", "eps", "ps", "svgz"}
SUPPORTED_LAYOUTS = {"3x4_1", "3x4", "6x2", "12x1"}
SUPPORTED_PAPERS = {"a4", "letter"}

MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "pdf": "application/pdf",
    "svg": "image/svg+xml",
    "svgz": "image/svg+xml",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "eps": "application/postscript",
    "ps": "application/postscript",
}


def _render(
    source,
    layout: str,
    paper: str,
    format: str,
    minor_grid: bool,
    interpretation: bool,
    mm_mv: float,
    lang: str,
) -> bytes:
    if layout not in SUPPORTED_LAYOUTS:
        raise HTTPException(status_code=422, detail=t("invalid_layout", lang, values=sorted(SUPPORTED_LAYOUTS)))
    if paper not in SUPPORTED_PAPERS:
        raise HTTPException(status_code=422, detail=t("invalid_paper", lang, values=sorted(SUPPORTED_PAPERS)))
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=422, detail=t("invalid_format", lang, values=sorted(SUPPORTED_FORMATS)))

    try:
        with ECG(source, paper=paper) as ecg:
            ecg.draw(layoutid=layout, mm_mv=mm_mv, minor_axis=minor_grid, interpretation=interpretation)
            data = ecg.save(outformat=format)
    except Exception as e:
        logger.exception("DICOM conversion failed")
        raise HTTPException(status_code=400, detail=t("conversion_error", lang))

    return data


def _rate_limit() -> str:
    return get_settings().rate_limit


@router.post("/convert", dependencies=[Depends(require_api_key)])
@limiter.limit(_rate_limit)
async def convert_file(
    request: Request,
    file: Annotated[UploadFile, File(description="File DICOM ECG")],
    layout: Annotated[str, Form(description="Layout: 3x4_1, 3x4, 6x2, 12x1")] = "3x4_1",
    paper: Annotated[str, Form(description="Formato carta: a4, letter")] = "a4",
    format: Annotated[str, Form(description="Formato output: png, pdf, svg, tiff, jpg, eps, ps, svgz")] = "png",
    minor_grid: Annotated[bool, Form(description="Griglia minore 1mm")] = False,
    interpretation: Annotated[bool, Form(description="Mostra interpretazione automatica")] = False,
    mm_mv: Annotated[float, Form(description="Scala ampiezza in mm/mV")] = 10.0,
    accept_language: Optional[str] = Header(default=None),
) -> Response:
    """Converti un file DICOM ECG in immagine."""
    lang = detect_language(accept_language)
    content = await file.read()
    data = _render(io.BytesIO(content), layout, paper, format, minor_grid, interpretation, mm_mv, lang)
    return Response(content=data, media_type=MEDIA_TYPES.get(format, "application/octet-stream"))


@router.post("/convert-wado", dependencies=[Depends(require_api_key)])
@limiter.limit(_rate_limit)
async def convert_wado(
    request: Request,
    study_uid: Annotated[str, Form(description="Study Instance UID")],
    series_uid: Annotated[str, Form(description="Series Instance UID")],
    object_uid: Annotated[str, Form(description="SOP Instance UID")],
    layout: Annotated[str, Form(description="Layout: 3x4_1, 3x4, 6x2, 12x1")] = "3x4_1",
    paper: Annotated[str, Form(description="Formato carta: a4, letter")] = "a4",
    format: Annotated[str, Form(description="Formato output: png, pdf, svg, tiff, jpg, eps, ps, svgz")] = "png",
    minor_grid: Annotated[bool, Form(description="Griglia minore 1mm")] = False,
    interpretation: Annotated[bool, Form(description="Mostra interpretazione automatica")] = False,
    mm_mv: Annotated[float, Form(description="Scala ampiezza in mm/mV")] = 10.0,
    accept_language: Optional[str] = Header(default=None),
) -> Response:
    """Converti un ECG DICOM recuperato da un server WADO."""
    lang = detect_language(accept_language)
    source = {"stu": study_uid, "ser": series_uid, "obj": object_uid}
    data = _render(source, layout, paper, format, minor_grid, interpretation, mm_mv, lang)
    return Response(content=data, media_type=MEDIA_TYPES.get(format, "application/octet-stream"))
