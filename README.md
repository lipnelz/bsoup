# URL Data Scraper

This Python script fetches data from a list of URLs and saves the data to a CSV file. The URLs and their corresponding names are provided in a JSON file (`urls.json`). The script can create the CSV file either on the desktop or in the same directory as the script, based on a command-line argument. The URLs must be from https://www.boursorama.com because the scraper targets that site's history pages.

## Requirements

- Python 3.x
- `aiohttp`
- `beautifulsoup4`

## Installation

1. Clone the repository or download the script files.
2. Install the required libraries with pip:

```bash
pip install aiohttp beautifulsoup4
# or, if you use the requirements.txt file:
pip install -r requirements.txt
```

## Usage

Create a `urls.json` file in the same directory as the script. The file should contain a list of URL entries in the following format (valid JSON array):

```json
[
    ["https://www.boursorama.com/cours/historique/<id1>", "Name1", 1],
    ["https://www.boursorama.com/cours/historique/<id2>", "Name2", 1],
    ["https://www.boursorama.com/cours/historique/<id3>", "Name3", 0]
]
```

Each entry is: `[URL, display_name, enabled]` where `enabled` is `1` to include the URL or `0` to skip it.

The expected URL format is:

```
https://www.boursorama.com/cours/historique/<id>
```

## Execution

By default the CSV file is created on the desktop. To create it in the same directory as the script, use `-l` / `--local`:

```bash
python3 bsoup.py -l
```

Other useful options:

- `-f, --file <path>`: Path to the JSON file (default: `urls.json`).
- `-s, --sep {.,,}`: Decimal separator to use inside numeric values in the CSV (choose `.` or `,`). This option requires a value; calling `-s` without value will error.
- `-v, --version`: Print the script version and exit.

Examples:

```bash
python3 bsoup.py -f my_urls.json
python3 bsoup.py -s , -l -f urls.json
python3 bsoup.py -v
```

## Output

The script creates a semicolon-separated CSV named `indices_YYYYMMDD_HHMM_<suffix>.csv` (timestamp and source file suffix). Column order matches the file header written by the script:

```
Indice;Cours;Date with max;Max;Date with min;Min
```

Column descriptions:

| Column            | Description                               |
|-------------------|-------------------------------------------|
| **Indice**        | The name of the index.                    |
| **Cours**         | The daily index value (formatted with the chosen decimal separator). |
| **Date with max** | The date with the maximum index value.    |
| **Max**           | The maximum index value.                  |
| **Date with min** | The date with the minimum index value.    |
| **Min**           | The minimum index value.                  |

## Notes

- Use `python3` on Linux systems for best compatibility.
- The script writes numeric values with three decimals; the decimal character is controlled by the `-s/--sep` option.
