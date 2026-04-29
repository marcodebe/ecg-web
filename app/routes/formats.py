from fastapi import APIRouter, Depends, Request
from app.auth import require_api_key
from app.config import get_settings
from app.limiter import limiter

router = APIRouter(prefix="/api/ecg", tags=["ecg"])


def _rate_limit() -> str:
    return get_settings().rate_limit


@router.get("/formats", dependencies=[Depends(require_api_key)])
@limiter.limit(_rate_limit)
def list_formats(request: Request) -> dict:
    """Restituisce tutti i valori accettati dai parametri di conversione."""
    return {
        "layouts": ["3x4_1", "3x4", "6x2", "12x1"],
        "papers": ["a4", "letter"],
        "formats": ["png", "pdf", "svg", "svgz", "tiff", "jpg", "jpeg", "eps", "ps"],
        "defaults": {
            "layout": "3x4_1",
            "paper": "a4",
            "format": "png",
            "minor_grid": False,
            "interpretation": False,
            "mm_mv": 10.0,
        },
    }
