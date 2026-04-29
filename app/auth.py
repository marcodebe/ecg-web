from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings
from app.i18n import detect_language, t

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    request: Request,
    api_key: Optional[str] = Security(_api_key_header),
) -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return
    lang = detect_language(request.headers.get("accept-language"))
    if not api_key or api_key not in settings.get_api_keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth_error", lang),
            headers={"WWW-Authenticate": "ApiKey"},
        )
