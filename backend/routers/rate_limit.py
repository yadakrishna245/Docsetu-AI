"""
Rate Limiting Middleware for DocSetu AI.
Uses slowapi to enforce request rate limits on API endpoints.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Create limiter instance with remote address as the key function
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Rate limit constants
AUTH_RATE_LIMIT = "20/minute"
DEFAULT_RATE_LIMIT = "100/minute"


def setup_rate_limiting(app):
    """
    Wire rate limiting into the FastAPI application.

    Args:
        app: FastAPI application instance

    Sets up:
        - Default limit: 100 requests/minute for authenticated endpoints
        - Auth limit: 20 requests/minute for login/register endpoints
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
