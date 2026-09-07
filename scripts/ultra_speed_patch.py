from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, pattern: str, replacement: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    new, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n:
        p.write_text(new, encoding="utf-8")


def patch_web_search() -> None:
    p = ROOT / "rival_search_mcp/tools/search.py"
    if not p.exists():
        return
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'(extract_content:\s*Annotated\[\s*bool,.*?\n\s*)=.*?(,)', r'\1=False\2', text, count=1, flags=re.DOTALL)
    text = re.sub(r'(follow_links:\s*Annotated\[\s*bool,.*?\n\s*)=.*?(,)', r'\1=False\2', text, count=1, flags=re.DOTALL)
    p.write_text(text, encoding="utf-8")


def patch_concurrency() -> None:
    candidates = [
        "rival_search_mcp/core/search/core/multi_engines.py",
        "rival_search_mcp/core/social/__init__.py",
        "rival_search_mcp/core/scientific/search/orchestrator.py",
        "rival_search_mcp/core/scientific/datasets/orchestrator.py",
        "rival_search_mcp/core/traverse/core.py",
    ]
    for rel in candidates:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        text = re.sub(r'(?i)(concurrency|semaphore|parallelism|workers?)\s*=\s*(?:5|8|10|12)', lambda m: m.group(1) + " = 20", text)
        p.write_text(text, encoding="utf-8")


def patch_map_website_cache() -> None:
    p = ROOT / "rival_search_mcp/tools/traversal.py"
    if not p.exists():
        return
    text = p.read_text(encoding="utf-8")
    # Keep cache reads, but ensure a successful result is written when a cache manager exists.
    if "cache_manager" in text and "set(" not in text:
        text = text.replace("return result", "\n        try:\n            await cache_manager.set(cache_key, result, ttl=1800)\n        except Exception:\n            pass\n        return result", 1)
    p.write_text(text, encoding="utf-8")


def remove_internal_rate_limit_registration() -> None:
    files = [ROOT / "rival_search_mcp/server.py", ROOT / "server.py"]
    for p in files:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        text = re.sub(r'^.*(?:RateLimit|rate_limit|ResponseLimit|response_limit).*middleware.*\n', '', text, flags=re.IGNORECASE | re.MULTILINE)
        p.write_text(text, encoding="utf-8")


def remove_generated_files() -> None:
    for pat in ("**/__pycache__", "**/*.pyc", ".pytest_cache", "logs"):
        for p in ROOT.glob(pat):
            if p.is_dir():
                import shutil
                shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                p.unlink(missing_ok=True)


if __name__ == "__main__":
    patch_web_search()
    patch_concurrency()
    patch_map_website_cache()
    remove_internal_rate_limit_registration()
    remove_generated_files()
    print("Ultra Speed patch applied")
