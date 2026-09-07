"""
Content processing utilities for RivalSearchMCP.
"""

from markdownify import markdownify as _md

_STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]


def clean_html_to_markdown(html_content: str) -> str:
    if not html_content:
        return ""
    return _md(html_content, strip=_STRIP_TAGS).strip()
