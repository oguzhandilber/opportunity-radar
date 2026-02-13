"""Rate limiting middleware using SlowAPI."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/minute",
    "search": "30/minute",
    "scrape": "5/minute",
    "analyze": "10/minute",
    "export": "10/minute",
}


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Too many requests. Limit: {exc.detail}",
                "retry_after": getattr(exc, "retry_after", 60),
            },
        )
    raise exc


def get_limiter() -> Limiter:
    return limiter
