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

# Default allowed origins - configurable via ALLOWED_ORIGINS env var (comma-separated)
_DEFAULT_ALLOWED_ORIGINS: FrozenSet[str] = frozenset(
    {
        "https://rivalsearchmcp.fastmcp.app",
        "https://RivalSearchMCP.fastmcp.app",
        "https://rivalsearchmcp.com",
        "https://www.rivalsearchmcp.com",
    }
)

# Match http://127.0.0.1[:port] and http://localhost[:port] for local development.
# CORS is a browser-only policy; permitting localhost does not expand the attack
# surface because an attacker's page runs on their own origin, not localhost.
_LOCAL_ORIGIN_PATTERN = re.compile(r"^http://(?:127\.0\.0\.1|localhost)(?::\d+)?$")

# Headers the client may read from the response. The MCP session header is
# required for Streamable HTTP session resumption; the protocol version is
# required by MCP spec §6.1 for negotiation.
_EXPOSED_HEADERS = "Mcp-Session-Id, Mcp-Protocol-Version"

# Headers the client may send on a request.
_ALLOWED_HEADERS = (
    "Content-Type, Accept, Authorization, " "Mcp-Protocol-Version, Mcp-Session-Id, Last-Event-Id"
)

# Methods the client may use. DELETE is required for MCP session termination.
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

    Rejects preflight (OPTIONS) and actual requests from untrusted
    origins with a 403 Forbidden response instead of reflecting the
    Origin header back.
    """

    def __init__(self, app, allowed_origins: FrozenSet[str] | None = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or _get_allowed_origins()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # No Origin header → not a cross-origin request, pass through
        if not origin:
            return await call_next(request)

        # Check if origin is allowed
        if not _is_origin_allowed(origin, self.allowed_origins):
            logger.warning(
                "Blocked request from untrusted origin: %s (method=%s path=%s)",
                origin,
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "detail": "Origin not allowed",
                },
            )

        # Allowed origin → handle preflight or pass through with CORS headers
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

        # Actual request from allowed origin
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Expose-Headers"] = _EXPOSED_HEADERS
        response.headers["Vary"] = "Origin"
        return response
