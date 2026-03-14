# Skill: Python Developer

Guidelines for writing Python code in the **bsoup** project.

---

## Language & runtime

- Target **Python 3.10+**.
- Use built-in types for type hints (`list`, `dict`, `tuple`) — do **not** import from `typing` for these.
- Use `X | None` union syntax instead of `Optional[X]`.

---

## Code style

- Follow **PEP 8** conventions.
- Maximum line length: **100 characters**.
- Use **4 spaces** for indentation — never tabs.
- Use **double quotes** for strings unless a single quote avoids escaping.
- Keep imports at the top of the file, grouped and ordered:
  1. Standard library
  2. Third-party packages
  3. Local modules
  (separate each group with a blank line)

---

## Docstrings

Use **Google-style** docstrings on every public function and module:

```python
async def fetch_html(session: aiohttp.ClientSession, url: str, retries: int = 3) -> str:
    """Fetch the HTML document from the given URL asynchronously.

    Args:
        session: The aiohttp session used for HTTP requests.
        url: URL to fetch.
        retries: Number of retry attempts on failure.

    Returns:
        HTML document as a string, or an empty string on failure.
    """
```

---

## Async patterns

- Use `asyncio` + `aiohttp` for all I/O-bound network work.
- Protect shared state with `asyncio.Semaphore` to cap concurrent connections.
- Prefer `asyncio.create_task` + `asyncio.wait` over `gather` when you need per-task cancellation or timeout handling.
- Always set an explicit `aiohttp.ClientTimeout` on the session.
- Set a descriptive `User-Agent` header: `bsoup/<VERSION>`.

---

## Error handling

- Catch only the specific exceptions you expect; never use a bare `except:`.
- Print a human-readable message before every `exit(1)` call.
- Guard every `BeautifulSoup.find()` result against `None` before accessing attributes or `.text`.
- Use retry loops with back-off for transient network errors.

---

## CLI design

- Use `argparse` with descriptive `help=` strings for every argument.
- Validate user input early and fail with clear error messages.
- Support `-v` / `--version` using `action='version'`.
- Use `choices=` to restrict arguments to a fixed set of values where appropriate.

---

## File & path handling

- Use `os.path` utilities (`os.path.join`, `os.path.abspath`, `os.path.exists`) — do **not** hard-code path separators.
- Respect the XDG user-dirs config for the Desktop path on Linux.
- Always open files with an explicit `encoding='utf-8'`.

---

## Testing recommendations

- Write tests with `pytest` and `pytest-asyncio` for async code.
- Mock `aiohttp.ClientSession` with `aiohttp-mock` or `unittest.mock.AsyncMock`.
- Use `pytest.mark.parametrize` to cover multiple input variants in a single test function.
- Place test files in a `tests/` directory using the naming pattern `test_<module>.py`.

---

## Dependencies

- Declare all runtime dependencies in `requirements.txt` with **pinned or minimum versions**.
- Do not add a dependency if the standard library or an already-used package covers the need.
- Check for known vulnerabilities before adding new packages.
