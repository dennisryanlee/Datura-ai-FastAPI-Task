from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> str:
    """
    Validate the API key provided in the X-API-Key header.
    """
    if api_key == settings.API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key or API key missing",
    )
