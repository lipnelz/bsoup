# URL Data Scraper

This Python script fetches data from a list of URLs and saves the data to a CSV file. The URLs and their corresponding names are provided in a JSON file (`urls.json`). The script can create the CSV file either on the desktop or in the same directory as the script, based on a command-line argument. The URLs must be from https://www.boursorama.com website as it scraps specific history data.

## Requirements

- Python 3.x
- `requests` library
- `beautifulsoup4` library
- `argparse` library (included in the Python standard library)
- `aiohttp` library

## Installation

1. Clone the repository or download the script files.
2. Install the required libraries using pip:

## Usage

Create a urls.json file in the same directory as the script. The file should contain a list of URLs and their corresponding names in the following format:
json
[
    ["https://www.example.com/url1", "Name1", 1],
    ["https://www.example.com/url2", "Name2"], 1,
    ...
    ["https://www.example.com/urln", "NameN"], 0,
    ...
]

The URLs format must be  https://www.boursorama.com/cours/historique/<id> where <id> is the company identifier used on website codebase.

## Execution

By default, the CSV file will be created on the desktop. To create the CSV file in the same directory as the script, use the -l or --local argument:

>$ python bsoup.py -l

To pass a specific .json file you can use -f or --file argument:

>$ python bsoup.py -f my_file.json

## Output

The script will create a CSV file named indices_YYYYMMDD_HHMM.csv (where YYYYMMDD_HHMM is the current date and time) with the following columns:


| Column            | Description                               |
|-------------------|-------------------------------------------|
| **Indice**        | The name of the index.                    |
| **Cours**         | The daily index value.                    |
| **Date with min** | The date with the minimum index value.    |
| **Min**           | The minimum index value.                  |
| **Date with max** | The date with the maximum index value.    |
| **Max**           | The maximum index value.                  |
