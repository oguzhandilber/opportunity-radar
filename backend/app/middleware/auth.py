"""API Key authentication middleware."""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Verify the API key from request header.

    Returns the validated API key or raises HTTPException.
    """
    settings = get_settings()

    # If no API key is configured, allow all requests (development mode)
    if not settings.api_key:
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key


def get_api_key_dependency():
    """Get the API key dependency for use in routers."""
    return Depends(verify_api_key)
