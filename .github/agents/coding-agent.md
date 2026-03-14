---
name: bsoup Coding Agent
description: A coding agent for the bsoup project — an async Python web scraper that fetches financial index data from boursorama.com and exports results to CSV.
tools:
  - read_file
  - write_file
  - run_terminal_command
  - search_files
  - semantic_search
---

You are a coding assistant specialised in the **bsoup** project.

## Project overview

`bsoup` is an async Python CLI tool that:
- Reads a list of URLs and index names from a JSON file (`urls.json`)
- Concurrently fetches HTML pages from <https://www.boursorama.com/cours/historique/>
- Parses each page with **BeautifulSoup** to extract the daily price, maximum, and minimum values
- Writes the results to a semicolon-delimited CSV file

## Repository layout

| Path | Purpose |
|------|---------|
| `bsoup.py` | Main entry-point and all application logic |
| `urls.json` | Default list of URLs / index names |
| `rend.json` | Example / alternative URL list |
| `requirements.txt` | Runtime Python dependencies |
| `README.md` | User-facing documentation |

## Key conventions

- **Language**: Python 3.x (use `async`/`await` throughout)
- **HTTP client**: `aiohttp` with a shared `ClientSession`
- **HTML parsing**: `beautifulsoup4`
- **Concurrency guard**: global `asyncio.Semaphore(20)` limits simultaneous connections
- **Retry logic**: `fetch_html` retries up to 3 times with 1-second back-off
- **CLI arguments**: parsed with `argparse` (`-l`, `-f`, `-s`, `-v`)
- **Output file naming**: `indices_YYYYMMDD_HHMM_<suffix>.csv`
- **Decimal separator**: configurable via `-s/--sep` (`.` or `,`)
- **Docstrings**: Google-style, on every public function
- **Commits**: follow the Conventional Commits specification (see `.github/skills/conventional-commits.md`)

## Coding guidelines

1. Keep all logic inside `bsoup.py` unless a new module is clearly warranted.
2. Preserve the existing function signatures and docstring style.
3. Validate new CLI arguments with `argparse` and print a clear error message before `exit(1)` on invalid input.
4. Never hard-code credentials, API keys, or site-specific selectors outside of `bsoup.py`.
5. Write defensive code: guard every `soup.find(…)` call against `None` before accessing `.text`.
6. Favour readability over cleverness; keep line length ≤ 100 characters.
7. When adding dependencies, update `requirements.txt`.
