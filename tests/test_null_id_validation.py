"""
Tests for NullIdValidationMiddleware.

Validates MCP spec §4.2.1 compliance: requests with id: null must be rejected.
Workaround for https://github.com/modelcontextprotocol/python-sdk/issues/2057
"""

import pytest
from starlette.testclient import TestClient


def test_has_null_id_helper():
    """Unit test for _has_null_id detection logic."""
    from rival_search_mcp.middleware.null_id_validation import _has_null_id

    assert _has_null_id({"jsonrpc": "2.0", "method": "init", "id": None}) is True
    assert _has_null_id({"jsonrpc": "2.0", "method": "init", "id": "x"}) is False
    assert _has_null_id({"jsonrpc": "2.0", "method": "init", "id": 1}) is False
    assert _has_null_id({"jsonrpc": "2.0", "method": "init"}) is False  # notification
    assert _has_null_id({"jsonrpc": "2.0", "method": "init", "id": 0}) is False


@pytest.fixture
def http_client():
    """Create test client with HTTP app (includes NullIdValidationMiddleware)."""
    from rival_search_mcp.server import app

    asgi_app = app.http_app(path="/mcp/")
    return TestClient(asgi_app, raise_server_exceptions=False)


def test_rejects_null_id_request(http_client):
    """Requests with id: null must be rejected with 400 and JSON-RPC error."""
    response = http_client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "method": "initialize", "id": None},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] is None
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]
    assert "null" in data["error"].get("data", "").lower()


def test_allows_valid_request_id_string(http_client):
    """Requests with string id should pass through (not blocked by null-id middleware)."""
    response = http_client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "method": "initialize", "id": "test-123"},
        headers={"Content-Type": "application/json"},
    )
    # Should not be 400 from our middleware (downstream may return 500 in
    # test environment due to missing FastMCP lifespan, but that is unrelated)
    assert response.status_code != 400 or "Invalid Request" not in str(response.content)


def test_allows_notification_without_id(http_client):
    """Notifications (no id field) should pass through."""
    response = http_client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={"Content-Type": "application/json"},
    )
    # Notifications don't have id - should pass through
    assert response.status_code != 400 or "Invalid Request" not in str(response.content)
