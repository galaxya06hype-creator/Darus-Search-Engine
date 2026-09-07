"""
Search engines package for RivalSearchMCP.
Contains implementations for various search engines.
"""

from .duckduckgo.duckduckgo_engine import DuckDuckGoSearchEngine
from .yahoo.yahoo_engine import YahooSearchEngine

__all__ = ["DuckDuckGoSearchEngine", "YahooSearchEngine"]
