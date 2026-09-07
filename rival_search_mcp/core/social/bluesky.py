"""
Bluesky search via the AT Protocol public endpoint.

api.bsky.app is the working host. public.api.bsky.app now returns 403
for app.bsky.feed.searchPosts.
"""

from typing import Any, Dict, List, Optional

import httpx

from rival_search_mcp.logging.logger import logger
from rival_search_mcp.utils.query import normalize_search_query

_API_BASE = "https://api.bsky.app/xrpc"


class BlueskySearch:
    """Search Bluesky public posts via the AT Protocol."""

    def __init__(self):
        self.api_url = _API_BASE
        self.headers = {
            "User-Agent": "rivalsearchmcp/1.0 (+https://github.com/damionrashford/RivalSearchMCP)",
            "Accept": "application/json",
        }

    async def search(
        self,
        query: str,
        limit: int = 10,
        sort: str = "top",
        lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Args:
            sort: "top" or "latest"
            lang: ISO 639-1 language filter, e.g. "en"
        """
        normalized = normalize_search_query(query, max_terms=3)
        if normalized != query:
            logger.debug("Bluesky query normalized: %r -> %r", query, normalized)

        params: Dict[str, Any] = {
            "q": normalized,
            "limit": max(1, min(limit, 100)),
            "sort": sort,
        }
        if lang:
            params["lang"] = lang

        try:
            async with httpx.AsyncClient(
                headers=self.headers, timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(
                    f"{self.api_url}/app.bsky.feed.searchPosts", params=params
                )
                if response.status_code != 200:
                    logger.warning(
                        "Bluesky returned %s for %r (body: %s)",
                        response.status_code,
                        query,
                        response.text[:200],
                    )
                    return []

                data = response.json()
                results: List[Dict[str, Any]] = []
                for p in data.get("posts", []):
                    author = p.get("author") or {}
                    record = p.get("record") or {}
                    uri = p.get("uri", "")
                    bsky_url = ""
                    if uri.startswith("at://"):
                        # at://did/app.bsky.feed.post/rkey -> bsky.app URL
                        parts = uri[len("at://") :].split("/")
                        if len(parts) >= 3:
                            handle = author.get("handle") or parts[0]
                            bsky_url = f"https://bsky.app/profile/{handle}/post/{parts[2]}"
                    results.append(
                        {
                            "text": record.get("text", ""),
                            "url": bsky_url,
                            "author_handle": author.get("handle", ""),
                            "author_display_name": author.get("displayName", ""),
                            "created_at": record.get("createdAt", ""),
                            "like_count": p.get("likeCount", 0),
                            "repost_count": p.get("repostCount", 0),
                            "reply_count": p.get("replyCount", 0),
                            "uri": uri,
                            "source": "bluesky",
                        }
                    )

                logger.info("Found %d Bluesky posts for %r", len(results), query)
                return results

        except httpx.HTTPError as e:
            logger.warning("Bluesky search failed: %s", e)
            return []
        except Exception:
            logger.exception("Bluesky search failed (unexpected)")
            return []
