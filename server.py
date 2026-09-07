#!/usr/bin/env python3
"""Compatibility entrypoint for FastMCP Cloud and MCP clients.

The application implementation lives in `rival_search_mcp.server`; this
module keeps deployments and docs that expect a repository-root `server.py`
working.
"""

import os

from rival_search_mcp.server import app, logger

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


if __name__ == "__main__":
    if ENVIRONMENT == "production":
        logger.info(f"Starting RivalSearchMCP in production mode on port {PORT}")
        app.run(transport="http", host="0.0.0.0", port=PORT, log_level=LOG_LEVEL)
    else:
        logger.info("Starting RivalSearchMCP in development mode (stdio)")
        app.run()
