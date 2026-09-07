"""
CORS Origin validation middleware for MCP HTTP transport.

The MCP server must not reflect arbitrary Origin headers in
Access-Control-Allow-Origin responses. Doing so allows any website
to make cross-origin requests to the server, which is a security
misconfiguration.

This HTTP-level middleware intercepts requests before they reach
FastMCP/Starlette's default CORS handling and enforces a strict
allowlist of trusted origins.
"""

import logging
import os
import re
from typing import Callable, FrozenSet

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("cors_validation")

# Allowed first-party origins. The Darus hostname is the production endpoint;
# the legacy RivalSearchMCP origins remain for backwards compatibility.
_DEFAULT_ALLOWED_ORIGINS: FrozenSet[str] = frozenset(
    {
        "https://darus-search-engine.fastmcp.app",
        "https://rivalsearchmcp.fastmcp.app",
        "https://RivalSearchMCP.fastmcp.app",
        "https://rivalsearchmcp.com",
        "https://www.rivalsearchmcp.com",
    }
)

# Match http://127.0.0.1[:port] and http://localhost[:port] for local development.
_LOCAL_ORIGIN_PATTERN = re.compile(r"^http://(?:127\.0\.0\.1|localhost)(?::\d+)?$")

_EXPOSED_HEADERS = "Mcp-Session-Id, Mcp-Protocol-Version"
_ALLOWED_HEADERS = (
    "Content-Type, Accept, Authorization, " "Mcp-Protocol-Version, Mcp-Session-Id, Last-Event-Id"
)
_ALLOWED_METHODS = "GET, POST, DELETE, OPTIONS"


def _get_allowed_origins() -> FrozenSet[str]:
    """Load allowed origins from environment or use defaults."""
    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins.strip():
        custom = frozenset(o.strip() for o in env_origins.split(",") if o.strip())
        return _DEFAULT_ALLOWED_ORIGINS | custom
    return _DEFAULT_ALLOWED_ORIGINS


def _is_origin_allowed(origin: str, allowed: FrozenSet[str]) -> bool:
    """Check exact-match allowlist, then local-development pattern."""
    if origin in allowed:
        return True
    if _LOCAL_ORIGIN_PATTERN.match(origin):
        return True
    return False


class CORSOriginValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates the Origin header on incoming requests and sets
    Access-Control-Allow-Origin only for trusted origins.
    """

    def __init__(self, app, allowed_origins: FrozenSet[str] | None = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or _get_allowed_origins()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # Native/non-browser clients normally omit Origin.
        if not origin:
            return await call_next(request)

        if not _is_origin_allowed(origin, self.allowed_origins):
            logger.warning(
                "Blocked request from untrusted origin: %s (method=%s path=%s)",
                origin,
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "detail": "Origin not allowed"},
            )

        if request.method == "OPTIONS":
            return Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": _ALLOWED_METHODS,
                    "Access-Control-Allow-Headers": _ALLOWED_HEADERS,
                    "Access-Control-Expose-Headers": _EXPOSED_HEADERS,
                    "Access-Control-Max-Age": "86400",
                    "Vary": "Origin",
                },
            )

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Expose-Headers"] = _EXPOSED_HEADERS
        response.headers["Vary"] = "Origin"
        return response
