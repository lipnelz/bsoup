# bsoup – Boursorama Financial Data Scraper

**bsoup** is an asynchronous Python scraper that fetches historical price data
from [Boursorama](https://www.boursorama.com) and exports it as a CSV file.
It can be run as a **command-line tool** *or* imported as a **library** inside
any Python program.

## Features

- Async HTTP fetching with configurable concurrency (default: 20 simultaneous
  connections)
- Automatic retry with back-off on transient errors
- Configurable decimal separator (`.` or `,`) for international CSV consumers
- Cross-platform Desktop / local-directory output
- Clean public API: `Scraper` class + `ScrapeResult` dataclass
- ≥ 90 % test coverage (currently 100 %)

## Requirements

- Python 3.10+
- `aiohttp >= 3.8`
- `beautifulsoup4 >= 4.11`

## Installation

```bash
# Clone and install in editable mode
git clone https://github.com/lipnelz/bsoup.git
cd bsoup
pip install -r requirements.txt
```

## Command-line usage

### Configuration file

Create a JSON file (default name: `urls.json`) containing an array of
`[url, display_name, enabled]` entries:

```json
[
    ["https://www.boursorama.com/cours/historique/<id1>", "Name1", 1],
    ["https://www.boursorama.com/cours/historique/<id2>", "Name2", 1],
    ["https://www.boursorama.com/cours/historique/<id3>", "Name3", 0]
]
```

`enabled` is `1` to include the URL or `0` to skip it.

### Running the scraper

```bash
# Save CSV on the Desktop (default)
python3 -m bsoup

# Save CSV in the current directory
python3 -m bsoup -l

# Use a custom JSON file
python3 -m bsoup -f my_urls.json

# Use comma as the decimal separator
python3 -m bsoup -s ,

# Print version and exit
python3 -m bsoup -v
```

| Option | Description |
|--------|-------------|
| `-l, --local` | Write the CSV next to the package instead of on the Desktop. |
| `-f, --file FILE` | Path to the JSON config file (default: `urls.json`). |
| `-s, --sep {.,}` | Decimal separator for numeric values (default: `.`). |
| `-v, --version` | Print version and exit. |

## Library / public API

`bsoup` exposes a clean async API that can be used from any Python program.

### `Scraper`

```python
import asyncio
from bsoup import Scraper, ScrapeResult

urls_config = [
    ("https://www.boursorama.com/cours/historique/1rPEN",  "BOUYGUES", 1),
    ("https://www.boursorama.com/cours/historique/1rPAXA", "AXA",      1),
    ("https://www.boursorama.com/cours/historique/1rPMERY","MERCIALYS", 0),  # skipped
]

scraper = Scraper(decimal_sep=',')
results: list[ScrapeResult] = asyncio.run(scraper.scrape(urls_config))

for r in results:
    print(f"{r.name}: cours={r.daily_value}  max={r.max_value} ({r.max_date})  min={r.min_value} ({r.min_date})")
```

#### `Scraper` constructor parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_connections` | `20` | Maximum simultaneous HTTP connections. |
| `decimal_sep` | `'.'` | Decimal separator (`'.'` or `','`). |
| `request_timeout` | `10` | Per-request timeout in seconds. |
| `overall_timeout` | `60` | Total batch timeout in seconds. |
| `retries` | `3` | Retry attempts per URL on failure. |

#### `Scraper` methods

| Method | Description |
|--------|-------------|
| `await scraper.scrape(urls_config)` | Fetch all enabled URLs; return `list[ScrapeResult]`. |
| `await scraper.scrape_to_csv(urls_config, output_dir, filename_suffix)` | Fetch, format, and write a CSV file; return the file path. |

### `ScrapeResult`

A dataclass with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name of the stock/index. |
| `daily_value` | `float` | Latest closing price. |
| `max_value` | `float` | Maximum price in the historical range. |
| `max_date` | `str` | Date of the maximum price. |
| `min_value` | `float` | Minimum price in the historical range. |
| `min_date` | `str` | Date of the minimum price. |

```python
line: str = result.to_csv_line(decimal_sep=',')
# → "BOUYGUES;12,345;02/01/2024;13,500;15/12/2023;11,200;"
```

## Output CSV format

Filename: `indices_YYYYMMDD_HHMM_<suffix>.csv`

```
Indice;Cours;Date with max;Max;Date with min;Min
BOUYGUES;12.345;02/01/2024;13.500;15/12/2023;11.200;
AXA;28.910;10/01/2024;30.000;05/12/2023;27.500;
```

| Column | Description |
|--------|-------------|
| **Indice** | Stock/index name. |
| **Cours** | Latest daily closing price. |
| **Date with max** | Date on which the maximum price was recorded. |
| **Max** | Maximum price in the scraped history. |
| **Date with min** | Date on which the minimum price was recorded. |
| **Min** | Minimum price in the scraped history. |

Numeric values are written with three decimal places; the decimal character is
controlled by the `-s / --sep` option (CLI) or the `decimal_sep` parameter
(library).

## Project structure

```
bsoup/
├── __init__.py     # Public exports: Scraper, ScrapeResult, CSV_HEADER
├── __main__.py     # Enables `python -m bsoup`
├── scraper.py      # Core library: Scraper class + ScrapeResult dataclass
└── cli.py          # Command-line interface

tests/
├── test_parser.py  # parse_html + ScrapeResult.to_csv_line
├── test_fetcher.py # fetch_html retry/error paths
├── test_scraper.py # scrape / scrape_to_csv integration tests
└── test_cli.py     # CLI argument parsing + get_output_path
```

## Running the tests

```bash
pip install -r requirements.txt
pytest --cov=bsoup --cov-report=term-missing
```

## Notes

- Use `python3` on Linux systems for best compatibility.
- The URLs must point to Boursorama historical price pages
  (`https://www.boursorama.com/cours/historique/<id>`).

