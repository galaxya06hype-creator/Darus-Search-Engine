"""
Utility functions for RivalSearchMCP.
"""

from .agents import get_enhanced_ua_list, get_random_user_agent
from .clients import get_http_client
from .content import clean_html_to_markdown


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    import re

    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


__all__ = [
    "clean_html_to_markdown",
    "clean_text",
    "get_random_user_agent",
    "get_enhanced_ua_list",
    "get_http_client",
]
