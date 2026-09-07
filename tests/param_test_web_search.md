# web_search Parameter Test Log

## Parameters
| Param | Type | Default | Range | Required |
|-------|------|---------|-------|----------|
| query | str | - | 2-500 chars | ✅ |
| num_results | int | 10 | 1-20 | ❌ |
| extract_content | bool | true | - | ❌ |
| follow_links | bool | true | - | ❌ |
| max_depth | int | 2 | 1-3 | ❌ |
| use_fallback | bool | true | - | ❌ |

## Test Cases (run via MCP)
1. [x] baseline query=Python num=3
2. [x] num_results=1
3. [x] num_results=20
4. [x] extract_content=false
5. [x] follow_links=false
6. [x] max_depth=1
7. [x] max_depth=3
8. [x] use_fallback=false

## Fixes Applied
- **DuckDuckGo**: Added fallback to html.duckduckgo.com/html/ when lite returns 403
- **DuckDuckGo**: Rotating User-Agent via get_random_user_agent()
- **Yahoo**: Rotating User-Agent (500 may be server-side, can't fix)

## Remaining Issues (external)
- Yahoo: 500 Internal Server Error (Yahoo's servers)
- Wikipedia: 403 rate limit when fetching content (bot-traffic@wikimedia.org)
