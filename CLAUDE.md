# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RivalSearchMCP is an MCP server providing 9 specialized tools for web research, content discovery, and analysis. Built on FastMCP, it offers multi-engine search (Yahoo/DuckDuckGo), website traversal, scientific research, and AI-enhanced research workflows. Ships with Claude Code Agent Skills for standalone CLI usage.

- **100% free**: No API keys required for core functionality
- **Dual deployment**: Hosted service at `https://RivalSearchMCP.fastmcp.app/mcp` or local development
- **Transport modes**: stdio (default, for CLI/IDE) or HTTP (production via `ENVIRONMENT=production`)

## Development Commands

The project uses [uv](https://docs.astral.sh/uv/) for dependency management and the [`fastmcp`](https://gofastmcp.com) CLI for running the server. Configuration lives in `fastmcp.json` (source / environment / deployment) and `pyproject.toml`.

### Setup & Running
```bash
# Install all dependencies (prod + dev) into a uv-managed venv
uv sync --extra dev

# Set up pre-commit hooks
uv run pre-commit install

# Run server (auto-detects fastmcp.json)
fastmcp run

# Run with stdio transport (for MCP clients / IDEs)
fastmcp run --transport stdio

# Run with HTTP transport (production)
fastmcp run --transport http --host 0.0.0.0 --port 8000

# Inspect server's tools/resources/prompts
fastmcp inspect

# Launch MCP Inspector UI for interactive testing
fastmcp dev inspector
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_web_search.py

# Run specific test function
uv run pytest tests/test_web_search.py::test_function_name

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing

# Verbose with short traceback
uv run pytest -v --tb=short
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Sort imports
uv run isort src/ tests/

# Lint with auto-fix
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Architecture

### High-Level Structure

RivalSearchMCP uses a **modular tool-based architecture** where each tool category registers MCP tools with the FastMCP app in `server.py`. The architecture separates tool interfaces from core business logic:

```
src/
├── tools/          # MCP tool implementations (deterministic, no LLM)
│   ├── analysis.py       # content_operations + research_topic
│   ├── multi_search.py   # MultiSearchOrchestrator (web_search)
│   ├── scientific.py     # scientific_research (academic + datasets)
│   ├── search.py         # web_search registration
│   ├── traversal.py      # map_website
│   ├── social_media.py   # social_search (9 platforms)
│   ├── news.py           # news_aggregation (5 sources)
│   ├── github_tool.py    # github_search
│   ├── pdf_tool.py       # document_analysis
│   ├── quality.py        # score_sources
│   ├── entity.py         # entity_research
│   └── conflict.py       # find_conflicts
├── core/           # Core business logic (reusable, not MCP-specific)
│   ├── search/     # Multi-engine search orchestration (Scrapling-backed)
│   ├── content/    # Extraction, parsing, cleaning (6-tier fallback)
│   ├── news/       # Google/Bing/Guardian/GDELT/DDG aggregator
│   ├── social/     # 9 platform adapters
│   ├── scientific/ # OpenAlex, CrossRef, arXiv, PubMed, Europe PMC + datasets
│   ├── quality/    # Source-quality scoring (tier/freshness/corroboration/citations)
│   ├── conflict/   # Rule-based numeric / date / polarity conflict detection
│   ├── traverse/   # Website crawling logic
│   ├── bypass/     # Anti-detection, proxy handling
│   └── security/   # Rate limiting, IP filtering
├── middleware/     # FastMCP middleware (timing, security, metrics)
├── schemas/        # Pydantic validation schemas
└── utils/          # Shared utilities (content, parsing, headers, etc.)
```

### Key Architectural Patterns

**Tool Registration Pattern:**
Each `src/tools/<category>.py` exports a `register_<category>_tools(app: FastMCP)` function that decorates tool implementations and registers them with the FastMCP app. All registration functions are called in `server.py` (lines 109-116).

Example pattern:
```python
def register_search_tools(app: FastMCP):
    @app.tool(name="multi_search", description="...")
    async def multi_search(query: str, ...) -> SearchResults:
        # Uses core modules from src/core/search/
        pass
```

**Multi-Engine Search Architecture:**
- Core implementation: `src/core/search/core/multi_engines.py`
- Concurrent execution across DuckDuckGo, Bing, Yahoo, Mojeek, Wikipedia
- Scrapling-backed TLS-fingerprint impersonation for Cloudflare-fronted engines
- Automatic fallback when individual engines fail
- Result deduplication by URL via `MultiSearchResult` class

**Content Processing Pipeline:**
- 6-tier fallback system in `src/core/content/extractors.py`
- HTML → Markdown conversion via `src/utils/content.py::clean_html_to_markdown()`
- Parser preference: selectolax (fastest) > lxml > html.parser
- BeautifulSoup4 used for robustness with lxml backend

**No LLM inside the server:**
Every tool returns structured, auditable output. Synthesis is the
caller's job. This is why tools like `entity_research` and
`find_conflicts` return deterministic reports instead of free-form
summaries -- the caller's model can reason over them; a consistent
machine can't hallucinate them.

**Middleware Stack:**
Registered in `src/middleware/middleware.py::register_middleware()`:
- `TimingMiddleware` - Logs slow operations (>1000ms threshold)
- `SecurityMiddleware` - Rate limiting and IP filtering
- `MetricsMiddleware` - Usage analytics and performance tracking

### Critical Implementation Details

**FastMCP Configuration (server.py:96-104):**
```python
app = FastMCP(
    name="RivalSearchMCP",
    instructions=SERVER_INSTRUCTIONS,
    include_fastmcp_meta=True,      # Rich metadata enabled
    on_duplicate_tools="error",      # Prevents tool conflicts
    on_duplicate_resources="warn",
    on_duplicate_prompts="replace",
)
```
- stdio transport is default for CLI/IDE compatibility
- HTTP transport enabled when `ENVIRONMENT=production`
- Background tasks started via `start_background_tasks()` at module level

**Dependency Constraints:**
- `urllib3<2.0.0` - Pinned for pytrends compatibility
- `pytrends==4.9.2` - Exact version required for Google Trends
- Use `httpx` for async HTTP requests
- Use `requests` only when synchronous calls required

**Search Engine Compliance:**
- User-agent rotation from `src/config/user_agents.py`
- Rate limiting built into search core
- Anti-detection measures in `src/core/bypass/bypass.py`
- Respects robots.txt and implements delays

**Error Handling Strategy:**
- All tools implement fallback chains (see `src/error/recovery.py`)
- Multi-engine search continues if one engine fails
- Errors logged via `src/logging/logger.py` with context
- Graceful degradation preferred over complete failure

## Environment Variables

All environment variables are optional — the system works without any configuration:

- `ENVIRONMENT` - Set to `production` for HTTP transport
- `PORT` - Server port for HTTP mode (default: 8000)
- `LOG_LEVEL` - Logging verbosity (default: INFO)
  to this filesystem path (otherwise they live in an in-memory MemoryStore
  that doesn't survive server restarts).

## Testing Configuration

**pytest configuration** (in `pyproject.toml` under `[tool.pytest.ini_options]`):
- Test directory: `tests/`
- File pattern: `test_*.py`
- Async mode: `auto` (pytest-asyncio handles async/await transparently)

Coverage is available via `pytest-cov` but not enforced by default — opt in with `--cov=src`.

## Workflow: Adding New Tools

1. **Create tool function** in `src/tools/<category>.py`
   - Use async def for I/O operations
   - Accept Pydantic models for input validation

2. **Define schemas** in `src/schemas/<category>.py`
   - Use Pydantic BaseModel for type safety
   - Include descriptions for MCP metadata

3. **Implement core logic** in `src/core/<category>/`
   - Keep MCP-agnostic (reusable outside MCP context)
   - Implement error handling and fallbacks

4. **Register tool** - Add `register_<category>_tools(app)` call in `server.py`
   - Insert around lines 109-116 with other registrations

5. **Write tests** in `tests/test_<category>.py`
   - Use pytest-asyncio for async tools
   - Aim for 80%+ coverage

6. **Update README** - Increment tool count if adding new tool (currently 9 total)

7. **Update Agent Skill** - If the new tool should be exposed via the CLI, regenerate:
   ```bash
   fastmcp generate-cli https://RivalSearchMCP.fastmcp.app/mcp skills/rival-search-mcp/cli.py -f
   ```
   Then update `skills/rival-search-mcp/SKILL.md` and the relevant resource file in `skills/rival-search-mcp/resources/`.

## Agent Skills

RivalSearchMCP ships with a Claude Code Agent Skill in `skills/rival-search-mcp/`. This packages all 9 tools as a standalone CLI that agents can invoke directly.

### Structure
```
skills/rival-search-mcp/
├── SKILL.md              # Agent instructions (loaded when skill triggers)
├── scripts/
│   └── cli.py            # Self-contained CLI (PEP 723 inline deps, runs with uv)
└── resources/
    ├── search.md         # web_search, social_search, news_aggregation, github_search, map_website
    ├── content.md        # content_operations, document_analysis
    └── research.md       # research_topic, scientific_research, entity_research,
                          # score_sources, find_conflicts
```

### How it works
- `SKILL.md` tells the agent what tools exist and how to invoke them via `scripts/cli.py`
- `scripts/cli.py` was generated by `fastmcp generate-cli` and connects to the live server at `https://RivalSearchMCP.fastmcp.app/mcp`
- Resource files in `resources/` provide detailed flag reference (only loaded when the agent needs specifics)
- The CLI is self-contained with PEP 723 inline dependencies — `uv run scripts/cli.py` just works

### Regenerating the CLI
```bash
fastmcp generate-cli https://RivalSearchMCP.fastmcp.app/mcp skills/rival-search-mcp/cli.py -f
```

## Code Style Standards

Enforced via pre-commit hooks:

- **Line length:** 100 characters (black, isort, ruff)
- **Type hints:** Required for all function signatures (checked via `uv run mypy src/`)
- **Import sorting:** isort with black profile
- **Linting:** ruff (auto-fix on pre-commit)
- **Python version:** 3.10+ (`requires-python = ">=3.10"` in pyproject.toml; pinned to 3.12 via `.python-version`)

## Performance Considerations

- **Async/await required** for all I/O operations (HTTP, file I/O)
- **Connection pooling** via httpx for HTTP requests
- **Timing middleware** automatically logs operations >1000ms
- **Cache manager** in `src/core/cache/` for repeated requests
- **Fast parsers** used when available (selectolax > lxml > html.parser)
- **Concurrent execution** in multi-engine search via asyncio.gather()
