# AGENTS.md - Testing Guide for AI Coding Agents

This guide helps AI coding agents run tests for RivalSearchMCP tools efficiently.

## Quick Start

### Test Individual Tools (RECOMMENDED)

Test one tool at a time for focused debugging:

```bash
# Navigate to project root
cd /Users/damionrashford/mcp-expert/servers/RivalSearchMCP

# Test individual tools (run these ONE AT A TIME)
uv run python tests/tools/test_multi_search.py
uv run python tests/tools/test_trends_core.py
uv run python tests/tools/test_trends_export.py
uv run python tests/tools/test_content_operations.py
uv run python tests/tools/test_traverse_website.py
uv run python tests/tools/test_research_topic.py
uv run python tests/tools/test_scientific_research.py
uv run python tests/tools/test_research_workflow.py
```

## Test Structure

```
tests/
├── AGENTS.md                      # This file
├── mcp_client.py                  # Reusable MCP client
├── run.py                         # Helper runner (optional)
└── tools/                         # Individual test files
    ├── test_multi_search.py       # Tests multi_search tool
    ├── test_trends_core.py        # Tests trends_core tool
    ├── test_trends_export.py      # Tests trends_export tool
    ├── test_content_operations.py # Tests content_operations tool
    ├── test_traverse_website.py   # Tests traverse_website tool
    ├── test_research_topic.py     # Tests research_topic tool
    ├── test_scientific_research.py # Tests scientific_research tool
    └── test_research_workflow.py  # Tests research_workflow tool
```

## How Tests Work

### 1. MCP Client (`mcp_client.py`)

This file provides a reusable `create_client()` function:

```python
from tests.mcp_client import create_client

async with create_client() as client:
    result = await client.call_tool("multi_search", {"query": "Python"})
    print(result.content[0].text)
```

### 2. Individual Test Files

Each test file:
- Tests ONE tool comprehensively
- Tests ALL parameters for that tool
- Uses real websites (not example.com)
- Has clear assertions (no cheating!)
- Runs independently with `uv run python tests/tools/test_<tool>.py`

### 3. Simple Execution Model

**No pytest** - Just plain `asyncio.run()`:

```python
async def test_something():
    async with create_client() as client:
        result = await client.call_tool(...)
        assert len(result.content[0].text) > 500
        print("✅ Test passed")

if __name__ == "__main__":
    asyncio.run(test_something())
```

## For AI Coding Agents

### When User Asks: "Test the tools"

**DO THIS:**
1. Test ONE tool at a time
2. Run: `uv run python tests/tools/test_<tool_name>.py`
3. Read the output carefully
4. If test fails, fix the tool's source code
5. Re-run the same test
6. Move to next tool only when current one passes

**DON'T DO THIS:**
- ❌ Run all tests at once
- ❌ Skip tests that take time
- ❌ Assume tests pass without running them
- ❌ Run tests in parallel

### Example Workflow

```bash
# Test multi_search
cd /Users/damionrashford/mcp-expert/servers/RivalSearchMCP
uv run python tests/tools/test_multi_search.py

# If it passes, move to next tool
uv run python tests/tools/test_trends_core.py

# If it fails, fix the source code, then re-test
# Fix: src/tools/trends.py
uv run python tests/tools/test_trends_core.py  # Re-run same test
```

### Reading Test Output

**Successful test:**
```
✅ Default params test passed - 523 chars
✅ num_results=3 test passed
✅ extract_content flag test passed
✅ use_fallback test passed
✅ Quality test passed - 1247 chars

✅ All multi_search tests passed!
```

**Failed test:**
```
Traceback (most recent call last):
  ...
AssertionError: Search results too short: 234 chars (expected >500)
```

### Understanding Test Coverage

Each test file tests **ALL parameters**:

- **test_multi_search.py** (5 tests)
  - query, num_results, extract_content, follow_links, max_depth, use_fallback

- **test_trends_core.py** (6 tests)
  - operation (search/related/regional/compare), keywords, timeframe, geo, resolution

- **test_trends_export.py** (6 tests)
  - keywords, format (csv/json/sql), timeframe, filename

- **test_content_operations.py** (10 tests)
  - operation (retrieve/stream/analyze/extract), url, content, extraction_method, analysis_type, link_type

- **test_traverse_website.py** (7 tests)
  - url, mode (research/docs/map), max_pages, max_depth, generate_llms_txt

- **test_research_topic.py** (6 tests)
  - topic, sources, max_sources, include_analysis

- **test_scientific_research.py** (9 tests)
  - operation (academic_search/dataset_discovery), query, max_results, sources, categories

- **test_research_workflow.py** (10 tests)
  - topic, max_sources, include_trends, include_website_analysis, research_depth, ai_model, enable_ai_insights

**Total: 59 test functions across 8 tools**

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastmcp'"

```bash
cd /Users/damionrashford/mcp-expert/servers/RivalSearchMCP
uv sync
```

### "No module named 'tests'"

Make sure you're running from the project root:
```bash
cd /Users/damionrashford/mcp-expert/servers/RivalSearchMCP
uv run python tests/tools/test_multi_search.py
```

### Tests hang or timeout

- Tests make real network requests (search engines, websites)
- Some tests may take 10-30 seconds
- If a test hangs >60 seconds, interrupt and investigate

### "AssertionError: Output too short"

This means the tool isn't returning quality content. Fix the tool's source code in `src/tools/<tool_name>.py`.

## Best Practices for Agents

1. **Always test after making changes**
   - Modified `src/tools/trends.py`? → Run `tests/tools/test_trends_core.py`
   - Modified `src/tools/analysis.py`? → Run `tests/tools/test_content_operations.py`

2. **Test individual tools, not all at once**
   - Easier to debug
   - Faster feedback loop
   - Can run in any order

3. **Read test output carefully**
   - Look for specific assertion messages
   - Check character counts (many tests verify content length)
   - Review error traces to find root cause

4. **Don't modify tests to make them pass**
   - Tests are correct
   - If test fails, fix the TOOL, not the TEST
   - Tests ensure quality content, not just "no errors"

5. **UV commands**
   ```bash
   uv sync                    # Install dependencies
   uv run <command>           # Run in UV environment
   uv add <package>           # Add dependency
   ```

## Test Quality Standards

Each test verifies:
- ✅ Tool executes without errors
- ✅ Returns content meeting minimum length (e.g., >500 chars)
- ✅ Contains expected data structures (URLs, markdown, etc.)
- ✅ Matches tool's stated purpose

**These are REAL tests** - they will fail if tools are broken!

## Summary

**For agents:**
- Test one tool at a time: `uv run python tests/tools/test_<tool>.py`
- Fix issues immediately when tests fail
- Re-run same test after fixing
- Move to next tool only when current passes

**Files:**
- `mcp_client.py` - Reusable MCP client
- `tools/test_*.py` - 8 comprehensive test files (59 tests total)
- `run.py` - Optional helper

**Remember:** Test individually, fix iteratively, verify thoroughly!
