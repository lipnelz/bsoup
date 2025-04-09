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
    date_maximum = date_minimum = ""
    minimum_indice = float('inf')
    maximum_indice = float('-inf')

    for tableclass in soup.find_all("tr", {"class": "c-table__row"}):
        date_cell = tableclass.find("td", {"class": "c-table__cell c-table__cell--dotted"})
        price_cell = tableclass.find("td", {"class": "c-table__cell c-table__cell--dotted c-table__cell--neutral"})

        if date_cell and price_cell:
            date = date_cell.get_text().strip()
            price = price_cell.get_text().strip()
            try:
                fval = float(price.replace(',', '.').replace('%', '').replace(' ', ''))
            except ValueError:
                print(f"Invalid price value: {price}")
                continue
            if fval > maximum_indice:
                maximum_indice = fval
                date_maximum = date
            if 0 < fval < minimum_indice:
                minimum_indice = fval
                date_minimum = date

    try:
        daily_indice = float(soup.find("span", {"class": "c-instrument c-instrument--last"}).text.strip().replace(',', '.'))
    except (AttributeError, ValueError):
        print("Error extracting daily index value.")
        daily_indice = 0.0

    return (f"{indice_name};"
            f"{format(daily_indice, '.3f').replace('.',',')};"
            f"{date_minimum};"
            f"{format(minimum_indice, '.3f').replace('.',',')};"
            f"{date_maximum};"
            f"{format(maximum_indice, '.3f').replace('.',',')}")


async def process_url_data(url_to_scrape: list, local: bool) -> None:
    """
    Fetch data from the URLs asynchronously and write to a CSV file.

    Args:
        url_to_scrape (list): List of URLs and their corresponding names.
        local (bool): If the result is saved on desktop or next to the script.

    Returns:
        None
    """
    urls = [url[0] for url in url_to_scrape]
    indice_names = [ind[1] for ind in url_to_scrape]

    output_path = os.path.dirname(os.path.abspath(__file__)) if local else os.path.join(os.environ['USERPROFILE'], 'Desktop')
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_path = f'{output_path}/indices_{datetime.today().strftime("%Y%m%d_%H%M")}.csv'
    print("File created here: ", file_path, " \n")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_html_with_limit(session, url) for url in urls]
        try:
            html_documents = await asyncio.wait_for(asyncio.gather(*tasks), timeout=60)
        except asyncio.TimeoutError:
            print("Timeout: Some requests took too long to complete.")

        results = []
        for html, indice_name in zip(html_documents, indice_names):
            if html:
                csv_string = await parse_page(html, indice_name)
                results.append(csv_string)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("Indice;Cours;Date with min;Min;Date with max;Max\n")
            for result in results:
                if result:
                    print(result)
                    f.write(result + "\n")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fetch data from URLs and save to a CSV file.")
    parser.add_argument('-l', '--local', action='store_true', help="Create the CSV file in the local directory instead of the desktop.")
    args = parser.parse_args()

    try:
        # Open 'urls.json' file
        with open('urls.json', 'r', encoding='utf-8') as file:
            urls_list = json.load(file)
    except FileNotFoundError:
        print("The file 'urls.json' was not found.")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")
        exit(1)

    if not isinstance(urls_list, list) or not all(len(item) == 2 for item in urls_list):
        print("Invalid JSON format. Expected a list of [URL, indice_name].")
        exit(1)

    start_time = time.time()
    asyncio.run(process_url_data(urls_list, args.local))
    end_time = time.time()
    print(f"\nDuration: {end_time - start_time:.2f} sec")
