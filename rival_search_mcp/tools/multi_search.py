"""
Ultra-fast multi-search across all configured engines.
"""
import asyncio
from datetime import datetime
from typing import Any, Dict
from fastmcp import Context
from rival_search_mcp.core.search.engines.bing.bing_engine import BingSearchEngine
from rival_search_mcp.core.search.engines.duckduckgo.duckduckgo_engine import DuckDuckGoSearchEngine
from rival_search_mcp.core.search.engines.mojeek.mojeek_engine import MojeekSearchEngine
from rival_search_mcp.core.search.engines.wikipedia.wikipedia_engine import WikipediaSearchEngine
from rival_search_mcp.core.search.engines.yahoo.yahoo_engine import YahooSearchEngine
from rival_search_mcp.logging.logger import logger
from rival_search_mcp.utils.markdown_formatter import format_multi_search_markdown

class MultiSearchOrchestrator:
    def __init__(self):
        self.engines = {
            "duckduckgo": DuckDuckGoSearchEngine(),
            "bing": BingSearchEngine(),
            "yahoo": YahooSearchEngine(),
            "mojeek": MojeekSearchEngine(),
            "wikipedia": WikipediaSearchEngine(),
        }
        self.engine_order = list(self.engines)

    async def search_all_engines(self, query: str, num_results: int = 10,
                                 extract_content: bool = False,
                                 follow_links: bool = False, max_depth: int = 2) -> Dict[str, Any]:
        logger.info("Starting concurrent search across %s engines for: %s", len(self.engines), query)
        tasks = [
            engine.search(query=query, num_results=num_results,
                          extract_content=extract_content,
                          follow_links=follow_links, max_depth=max_depth)
            for engine in self.engines.values()
        ]
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        results: Dict[str, Any] = {}
        all_results = []
        successful_engines = 0
        for (engine_name, _), engine_result in zip(zip(self.engines.keys(), tasks), search_results):
            if isinstance(engine_result, Exception):
                logger.error("%s search failed: %s", engine_name, engine_result)
                results[engine_name] = {"status": "failed", "error": str(engine_result), "count": 0,
                                        "results": [], "timestamp": datetime.now().isoformat()}
            elif engine_result:
                data = [r.to_dict() for r in engine_result]
                results[engine_name] = {"status": "success", "count": len(data), "results": data,
                                        "timestamp": datetime.now().isoformat()}
                successful_engines += 1
                all_results.extend(engine_result)
            else:
                results[engine_name] = {"status": "no_results", "count": 0, "results": [],
                                        "timestamp": datetime.now().isoformat()}
        seen = set()
        dedup = []
        for result in all_results:
            url = result.url.lower().strip()
            if url not in seen:
                seen.add(url)
                dedup.append(result)
        results["deduplicated"] = {"status": "success", "count": len(dedup),
                                    "results": [r.to_dict() for r in dedup],
                                    "timestamp": datetime.now().isoformat()}
        return {"summary": {"query": query, "engines_searched": len(self.engines),
                             "successful_engines": successful_engines,
                             "total_results": len(dedup), "results_before_dedup": len(all_results),
                             "extract_content": extract_content, "follow_links": follow_links,
                             "max_depth": max_depth, "timestamp": datetime.now().isoformat()},
                "results": results}

    async def close_all_engines(self):
        await asyncio.gather(*(engine.close() for engine in self.engines.values()), return_exceptions=True)

_orchestrator = None
def get_orchestrator() -> MultiSearchOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiSearchOrchestrator()
    return _orchestrator

async def web_search(query: str, ctx: Context, num_results: int = 10,
                     extract_content: bool = False, follow_links: bool = False,
                     max_depth: int = 2) -> str:
    from rival_search_mcp.core.cache.cache_manager import get_cache_manager
    try:
        await ctx.info(f"🔍 Starting multi-engine search for: {query}")
        cache_key = f"multi_search:{query}:{num_results}:{extract_content}:{follow_links}:{max_depth}"
        cache_manager = get_cache_manager()
        cached = await cache_manager.get(cache_key)
        if cached:
            await ctx.info("✅ Using cached search results")
            return cached
        results = await get_orchestrator().search_all_engines(query, num_results, extract_content,
                                                               follow_links, max_depth)
        try:
            from rival_search_mcp.core.quality import assess_results, summarize_quality
            union = []
            for engine_data in (results.get("results") or {}).values():
                scored = assess_results(engine_data.get("results") or [])
                engine_data["results"] = scored
                union.extend(scored)
            if union:
                results["summary"]["confidence"] = summarize_quality(union)
        except Exception as exc:
            logger.warning("web_search quality scoring failed: %s", exc)
        formatted = format_multi_search_markdown(results)
        await cache_manager.set(cache_key, formatted, ttl_seconds=1800)
        return formatted
    except Exception as exc:
        logger.exception("Multi-engine search failed")
        return f"❌ **Error:** Multi-engine search failed: {exc}"
