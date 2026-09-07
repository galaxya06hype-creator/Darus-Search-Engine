"""
Production middleware for Darus Search Engine.
Security validation and performance metrics are kept; application rate limiting
and response-size middleware are intentionally not registered.
"""
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

_security_middleware = None

class PerformanceMonitoringMiddleware(Middleware):
    def __init__(self):
        self.operation_times = defaultdict(list)
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.logger = logging.getLogger("performance")

    async def on_request(self, context: MiddlewareContext, call_next):
        start = time.perf_counter()
        operation = context.method
        try:
            result = await call_next(context)
            duration = time.perf_counter() - start
            self.operation_times[operation].append(duration)
            self.operation_counts[operation] += 1
            if len(self.operation_times[operation]) > 100:
                self.operation_times[operation] = self.operation_times[operation][-100:]
            return result
        except Exception:
            duration = time.perf_counter() - start
            self.error_counts[operation] += 1
            self.operation_times[operation].append(duration)
            self.operation_counts[operation] += 1
            raise

    def get_metrics(self) -> Dict[str, Any]:
        metrics = {}
        for operation, count in self.operation_counts.items():
            times = self.operation_times[operation]
            if times:
                metrics[operation] = {
                    "count": count,
                    "error_count": self.error_counts[operation],
                    "avg_time_ms": sum(times) / len(times) * 1000,
                    "min_time_ms": min(times) * 1000,
                    "max_time_ms": max(times) * 1000,
                    "success_rate": 1 - self.error_counts[operation] / count,
                }
        return metrics

class SecurityMiddleware(Middleware):
    def __init__(self, block_suspicious_requests: bool = True):
        self.block_suspicious_requests = block_suspicious_requests
        self.logger = logging.getLogger("security")
        from rival_search_mcp.core.security.security import get_security_middleware
        self.security = get_security_middleware()

    def start_cleanup_task(self):
        # Kept for compatibility with the existing security component.
        # It only manages its internal state; it is not an application quota.
        if hasattr(self.security, "start_cleanup_task"):
            self.security.start_cleanup_task()

    def _is_suspicious(self, context: MiddlewareContext) -> bool:
        message = str(context.message).lower()
        patterns = [
            "<script", "<iframe", "<object", "<embed", "vbscript:",
            "data:text/html", "file://", "rm -rf", "drop table",
            "union select", "eval(", "exec(", "system(", "'; drop",
            '"; drop', "' or '1'='1",
        ]
        return any(pattern in message for pattern in patterns)

    async def on_request(self, context: MiddlewareContext, call_next):
        request_data = {
            "client_ip": getattr(context, "client_ip", "unknown"),
            "user_agent": getattr(context, "user_agent", ""),
            "tool_name": context.method.replace("tools/", "") if context.method else "",
            "parameters": getattr(context.message, "params", {}) if hasattr(context.message, "params") else {},
        }
        allowed, reason = await self.security.check_request(request_data)
        if not allowed:
            self.logger.warning("Request blocked: %s", reason)
            raise ToolError(f"Request blocked: {reason}")
        if self._is_suspicious(context) and self.block_suspicious_requests:
            self.logger.warning("Suspicious pattern detected in request: %s", context.method)
            raise ToolError("Request blocked due to suspicious content")
        return await call_next(context)

def register_middleware(mcp) -> None:
    from fastmcp.server.middleware.caching import (
        CallToolSettings, GetPromptSettings, ListPromptsSettings,
        ListResourcesSettings, ListToolsSettings, ReadResourceSettings,
        ResponseCachingMiddleware,
    )
    from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
    from fastmcp.server.middleware.logging import LoggingMiddleware
    from fastmcp.server.middleware.ping import PingMiddleware
    from fastmcp.server.middleware.timing import TimingMiddleware

    security_middleware = SecurityMiddleware(block_suspicious_requests=True)
    mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=False, transform_errors=False))
    mcp.add_middleware(security_middleware)

    try:
        from key_value.aio.stores.filetree import (
            FileTreeStore,
            FileTreeV1CollectionSanitizationStrategy,
            FileTreeV1KeySanitizationStrategy,
        )
        cache_dir = Path("/tmp/fastmcp-cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_store = FileTreeStore(
            data_directory=cache_dir,
            key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(cache_dir),
            collection_sanitization_strategy=FileTreeV1CollectionSanitizationStrategy(cache_dir),
        )
        caching_kwargs = {"cache_storage": cache_store}
    except ImportError:
        caching_kwargs = {}

    disabled = {"enabled": False}
    mcp.add_middleware(ResponseCachingMiddleware(
        list_tools_settings=ListToolsSettings(**disabled),
        list_resources_settings=ListResourcesSettings(**disabled),
        list_prompts_settings=ListPromptsSettings(**disabled),
        read_resource_settings=ReadResourceSettings(**disabled),
        get_prompt_settings=GetPromptSettings(**disabled),
        call_tool_settings=CallToolSettings(ttl=300, included_tools=["content_operations", "document_analysis"]),
        **caching_kwargs,
    ))
    mcp.add_middleware(PerformanceMonitoringMiddleware())
    mcp.add_middleware(TimingMiddleware())
    mcp.add_middleware(LoggingMiddleware(include_payloads=True, max_payload_length=500))
    mcp.add_middleware(PingMiddleware(interval_ms=30_000))

    global _security_middleware
    _security_middleware = security_middleware
    logging.getLogger("middleware").info(
        "Middleware stack registered: error, security, cache, perf, timing, logging, ping"
    )

def start_background_tasks():
    # Avoid starting asynchronous tasks during module import/deployment discovery.
    # Security cleanup is optional and starts only when an event loop is available.
    return None
