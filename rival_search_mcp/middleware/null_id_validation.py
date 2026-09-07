"""
Null ID validation middleware for MCP JSON-RPC compliance.

Workaround for MCP Python SDK issue #2057:
https://github.com/modelcontextprotocol/python-sdk/issues/2057

When a JSON-RPC request arrives with "id": null, the SDK incorrectly
classifies it as a notification and returns 202 with no response.
Per MCP spec §4.2.1 and JSON-RPC 2.0, request IDs must be strings or
numbers - null must be rejected with an error.

This HTTP-level middleware validates the raw request body BEFORE it
reaches the MCP SDK, rejecting malformed requests with a proper
JSON-RPC error response.
"""

import json
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("null_id_validation")


def _has_null_id(data: dict) -> bool:
    """Check if JSON-RPC message has id: null (invalid per MCP spec)."""
    return (
        isinstance(data, dict)
        and data.get("jsonrpc") == "2.0"
        and "method" in data
        and "id" in data
        and data["id"] is None
    )


def _json_rpc_error_response(request_id: None, code: int, message: str) -> dict:
    """Build JSON-RPC 2.0 error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
            "data": "Request id must be a string or number, not null. "
            "See MCP spec §4.2.1 and https://github.com/modelcontextprotocol/python-sdk/issues/2057",
        },
    }


class NullIdValidationMiddleware(BaseHTTPMiddleware):
    """
    Rejects JSON-RPC requests with id: null before they reach the MCP SDK.

    Per MCP 2025-11-25 §4.2.1: Request identifiers must be strings or
    numbers. Requests with id: null must be rejected with an error.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method != "POST":
            return await call_next(request)

        try:
            body = await request.body()
        except Exception as e:
            logger.warning("NullIdValidation: could not read body: %s", e)
            return await call_next(request)

        if not body:
            return await call_next(request)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return await call_next(request)

        if not _has_null_id(data):
            # Valid - pass through; re-inject body for downstream
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request = Request(request.scope, receive=receive)
            return await call_next(request)

        # Reject with JSON-RPC Invalid Request
        logger.warning("Rejected JSON-RPC request with id: null (method=%s)", data.get("method"))
        return JSONResponse(
            status_code=400,
            content=_json_rpc_error_response(
                request_id=None,
                code=-32600,
                message="Invalid Request",
            ),
        )
