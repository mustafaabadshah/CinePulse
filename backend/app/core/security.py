"""Security, Authentication, and Input Sanitization."""

import secrets

from app.config import settings
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def verify_admin_key(api_key: str = Security(api_key_header)) -> bool:
    """Verifies that the provided admin API key matches the configured secret."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Please provide a valid 'X-Admin-API-Key' header.",
        )
    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired admin API key.",
        )
    return True
