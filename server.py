#!/usr/bin/env python3
"""Compatibility entrypoint for FastMCP Cloud and MCP clients.

The application implementation lives in `rival_search_mcp.server`.
Both `mcp` and `app` are exported so deployment platforms and MCP clients
that expect either conventional entrypoint name can load the same server.
"""

import os

from rival_search_mcp.server import app as _app
from rival_search_mcp.server import logger

# Canonical FastMCP entrypoint plus backwards-compatible alias.
mcp = _app
app = _app

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


if __name__ == "__main__":
    if ENVIRONMENT == "production":
        logger.info(f"Starting RivalSearchMCP in production mode on port {PORT}")
        mcp.run(transport="http", host="0.0.0.0", port=PORT, log_level=LOG_LEVEL)
    else:
        logger.info("Starting RivalSearchMCP in development mode (stdio)")
        mcp.run()
