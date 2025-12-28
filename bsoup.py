import os
import json
import time
import argparse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime


# Limit to 20 simultaneous connexions
semaphore = asyncio.Semaphore(20)

async def fetch_html_with_limit(session: aiohttp.ClientSession, url: str) -> str:
    """
    Fetch the HTML document from the given URL asynchronously,
    respecting a limit on the number of simultaneous connections.

    Args:
        session (aiohttp.ClientSession): The aiohttp session used for making HTTP requests.
        url (str): The URL to fetch.

    Returns:
        str: The HTML document as a string if the request is successful,
             or an empty string if the request fails.
    """
    async with semaphore: # Limit the number of simultaneous connections
        return await fetch_html(session, url)

async def fetch_html(session: aiohttp.ClientSession, url: str, retries: int = 3) -> str:
    """
    Fetch the HTML document from the given URL asynchronously.

    Args:
        session (aiohttp.ClientSession): The aiohttp session.
        url (str): URL to fetch.

    Returns:
        str: HTML document as a string.
    """
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            await asyncio.sleep(1)  # Wait before retry
    return ""

async def parse_page(html: str, indice_name: str) -> str:
    """
    Parse the HTML document and extract relevant data.

    Args:
        html (str): HTML content of the page.
        indice_name (str): Name of the indice.

    Returns:
        str: Formatted CSV string with extracted data.
    """
    soup = BeautifulSoup(html, 'html.parser')
    min_value = float('inf')
    max_value = float('-inf')
    min_date = None
    max_date = None

    for row in soup.find_all("tr", class_="c-table__row"):
        cells = row.find_all("td")
        if len(cells) >= 6:  # Check there is at least 6 cells
            date = cells[0].get_text(strip=True)
            for cell in cells[1:]:  # Ignore the first cell (date)
                cell_text = cell.get_text(strip=True)
                if '%' in cell_text:
                    continue  # Ignore percentage cells (%)
                try:
                    value = float(cell_text.replace(',', '.'))
                    if value < min_value:
                        min_value = value
                        min_date = date
                    if value > max_value:
                        max_value = value
                        max_date = date
                except ValueError:
                    continue  # Ignore non-numeric values

    # Guard against not-found min/max values
    if min_value == float('inf'):
        min_value = 0.0
        min_date = ''
    if max_value == float('-inf'):
        max_value = 0.0
        max_date = ''

    try:
        daily_indice = float(soup.find("span", {"class": "c-instrument c-instrument--last"}).text.strip().replace(',', '.'))
    except (AttributeError, ValueError):
        print("Error extracting daily index value.")
        daily_indice = 0.0

    return (f"{indice_name};"
            f"{format(daily_indice, '.3f').replace('.',',')};"
            f"{max_date};"
            f"{format(max_value, '.3f').replace('.',',')};"
            f"{min_date};"
            f"{format(min_value, '.3f').replace('.',',')};")


async def process_url_data(url_to_scrape: list, local: bool, filename: str) -> None:
    """
    Fetch data from the URLs asynchronously and write to a CSV file.

    Args:
        url_to_scrape (list): List of URLs and their corresponding names.
        local (bool): If the result is saved on desktop or next to the script.

    Returns:
        None
    """
    filtered_data = [item for item in url_to_scrape if item[2] == 1]
    urls = [url[0] for url in filtered_data]
    indice_names = [ind[1] for ind in filtered_data]

    if local:
        output_path = os.path.dirname(os.path.abspath(__file__))
    else:
        home = os.path.expanduser('~')
        desktop = None
        if os.name == 'nt':
            desktop = os.path.join(os.environ.get('USERPROFILE', home), 'Desktop')
        else:
            # Try XDG user-dirs config for localized Desktop path
            try:
                cfg = os.path.join(home, '.config', 'user-dirs.dirs')
                with open(cfg, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('XDG_DESKTOP_DIR'):
                            path = line.split('=', 1)[1].strip().strip('"')
                            desktop = path.replace('$HOME', home)
                            break
            except Exception:
                pass
            if not desktop:
                desktop = os.path.join(home, 'Desktop')
        output_path = desktop if os.path.exists(desktop) else home

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    suffix = filename.replace('.json', '')
    file_path = f'{output_path}/indices_{datetime.today().strftime("%Y%m%d_%H%M")}_{suffix}.csv'
    print("File created here: ", file_path, " \n")

    # Use a client timeout and a simple User-Agent header
    client_timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=client_timeout, headers={'User-Agent': 'bsoup/1.0'}) as session:
        # create tasks so we can detect which completed within the overall timeout
        tasks = [asyncio.create_task(fetch_html_with_limit(session, url)) for url in urls]
        done, pending = await asyncio.wait(tasks, timeout=60)
        for p in pending:
            p.cancel()
        # preserve original ordering; fill missing results with empty strings
        html_documents = [''] * len(tasks)
        for i, task in enumerate(tasks):
            if task in done and not task.cancelled():
                try:
                    html_documents[i] = task.result()
                except Exception:
                    html_documents[i] = ''

        results = []
        for html, indice_name in zip(html_documents, indice_names):
            print(f"Processing {indice_name} ...")
            if html:
                csv_string = await parse_page(html, indice_name)
                results.append(csv_string)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Indice;Cours;Date with max;Max;Date with min;Min\n")
            for result in results:
                if result:
                    print(result)
                    f.write(result + "\n")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fetch data from URLs and save to a CSV file.")
    parser.add_argument('-l', '--local', action='store_true', help="Create the CSV file in the local directory instead of the desktop.")
    parser.add_argument('-f', '--file', type=str, default='urls.json', help="JSON file to use (default: urls.json)")
    args = parser.parse_args()

    try:
        # Open 'urls.json' file
        with open(args.file, 'r', encoding='utf-8') as file:
            urls_list = json.load(file)
    except FileNotFoundError:
        print("The file 'urls.json' was not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error decoding the JSON file '{args.file}'.")
        exit(1)

    if not isinstance(urls_list, list) or not all(len(item) == 3 for item in urls_list):
        print("Invalid JSON format. Expected a list of [URL, indice_name, is_enabled].")
        exit(1)

    start_time = time.time()
    asyncio.run(process_url_data(urls_list, args.local, args.file))
    end_time = time.time()
    print(f"\nDuration: {end_time - start_time:.2f} sec")
