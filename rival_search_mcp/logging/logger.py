import logging
import os
import sys
from pathlib import Path

# Create a centralized logger for the entire application
# Configure to use stderr instead of stdout to avoid corrupting MCP protocol
logger = logging.getLogger("rival_search_mcp")

# Set log level from environment variable or default to INFO
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Prevent propagation to root logger to avoid duplicate messages
logger.propagate = False

# Timestamp format for all log messages
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Add handler if none exists (to avoid duplicate handlers)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)

# Optional: Log to file when LOG_FILE is set (for debugging)
_log_file_path = os.environ.get("LOG_FILE")
if _log_file_path:
    _log_path = Path(_log_file_path)
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    _file_handler = logging.FileHandler(_log_path, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    _file_handler.setLevel(logger.level)
    logger.addHandler(_file_handler)
