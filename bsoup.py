import os
import requests
import time
import json
import argparse
from bs4 import BeautifulSoup
from datetime import datetime

def getHTMLdocument(url: str) -> str:
    """
    Get the HTML document from the given URL.

    Args:
        url (str): URL to be parsed.

    Returns:
        str: HTML document as a string.
    """
    try:
        # Request for HTML document of given URL
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""

def get_output_path(local: bool) -> str:
    """
    Get the output path for the CSV file.

    Args:
        local (bool): If True, use the local directory; otherwise, use the desktop path.

    Returns:
        str: Output path.
    """
    if local:
        return os.path.dirname(os.path.abspath(__file__))
    else:
        # Windows
        if os.name == 'nt':
            return os.path.join(os.environ['USERPROFILE'], 'Desktop')
        # Linux & MacOS
        else:
            return os.path.join(os.environ['HOME'], 'Desktop')

def process_url_data(url_to_scrape: list, local: bool) -> None:
    """
    Fetches data from the URLs and writes to a CSV file.

    Args:
        url_to_scrape (list): List of URLs and their corresponding names.

    Returns:
        None
    """
    urls = [url[0] for url in url_to_scrape]
    indice_names = [ind[1] for ind in url_to_scrape]

    output_path = get_output_path(local)

    # Check if the output directory exists, if not, create it
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_path = f'{output_path}/indices_{datetime.today().strftime("%Y%m%d_%H%M")}.csv'

    print("File created here: ", file_path, " \n")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("Indice;Cours;Date with min;Min;Date with max;Max\n")

        for url, indice_name in zip(urls, indice_names):
            # Create document
            html_document = getHTMLdocument(url)
            if html_document:
                # Create soup object
                soup = BeautifulSoup(html_document, 'html.parser')

                date_maximum = date_minimum = ""
                minimum_indice = float('inf')  # Initialize to the largest possible number
                maximum_indice = float('-inf')  # Initialize to the smallest possible number

                # Find all the table rows with class "c-table__row"
                for tableclass in soup.find_all("tr", {"class": "c-table__row"}):
                    date = tableclass.find("td", {"class": "c-table__cell c-table__cell--dotted"}).get_text().strip()
                    price = tableclass.find("td", {"class": "c-table__cell c-table__cell--dotted c-table__cell--neutral"}).get_text().strip()
                    fval = float(price.replace(',', '.').replace('%', '').replace(' ', ''))

                    # Update maximum and minimum indices
                    if fval > maximum_indice:
                        maximum_indice = fval
                        date_maximum = date
                    if 0 < fval < minimum_indice:
                        minimum_indice = fval
                        date_minimum = date

                # Get the daily index value
                daily_indice = soup.find("span", {"class": "c-instrument c-instrument--last"}).text.strip()
                current_indice_name = next((name for name in indice_names if name.lower() in soup.find("div", {"class": "u-text-bold"}).text.strip().lower()), "")

                # Format the CSV string
                csv_string = f"{current_indice_name};{daily_indice.replace('.',',')};{date_minimum};{str(minimum_indice).replace('.',',')};{date_maximum};{str(maximum_indice).replace('.',',')}"
                print(csv_string)
                f.write(csv_string + "\n")

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
    except json.JSONDecodeError:
        print("Error decoding the JSON file.")

    start_time = time.time()
    process_url_data(urls_list, args.local)
    end_time = time.time()
    print(f"\nDuration: {end_time - start_time:.2f} sec")
