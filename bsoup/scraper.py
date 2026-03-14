"""Core scraping logic for bsoup."""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

VERSION = "1.1.0"
CSV_HEADER = "Indice;Cours;Date with max;Max;Date with min;Min"


@dataclass
class ScrapeResult:
    """Holds the scraped financial data for a single stock/index."""

    name: str
    daily_value: float
    max_value: float
    max_date: str
    min_value: float
    min_date: str

    def to_csv_line(self, decimal_sep: str = '.') -> str:
        """Format the result as a semicolon-separated CSV line.

        Args:
            decimal_sep: Decimal separator character, either ``'.'`` (default)
                or ``','``.

        Returns:
            A CSV line ending with a trailing semicolon.
        """
        def _fmt(value: float) -> str:
            s = format(value, '.3f')
            if decimal_sep == ',':
                s = s.replace('.', ',')
            return s

        return (
            f"{self.name};"
            f"{_fmt(self.daily_value)};"
            f"{self.max_date};"
            f"{_fmt(self.max_value)};"
            f"{self.min_date};"
            f"{_fmt(self.min_value)};"
        )


class Scraper:
    """Asynchronous web scraper for Boursorama financial data.

    Can be used as a library in external Python programs::

        import asyncio
        from bsoup import Scraper

        urls_config = [
            ("https://www.boursorama.com/cours/historique/1rPEN", "BOUYGUES", 1),
        ]

        scraper = Scraper(decimal_sep=',')
        results = asyncio.run(scraper.scrape(urls_config))

        for r in results:
            print(r.name, r.daily_value)

    Each entry in *urls_config* is a 3-element sequence ``(url, name, enabled)``
    where *enabled* is ``1`` to include the URL or ``0`` to skip it.
    """

    def __init__(
        self,
        max_connections: int = 20,
        decimal_sep: str = '.',
        request_timeout: int = 10,
        overall_timeout: int = 60,
        retries: int = 3,
    ) -> None:
        """Initialise the scraper.

        Args:
            max_connections: Maximum number of simultaneous HTTP connections.
            decimal_sep: Decimal separator used when formatting numeric values
                (``'.'`` or ``','``).
            request_timeout: Per-request HTTP timeout in seconds.
            overall_timeout: Total timeout in seconds for the whole batch.
            retries: Number of retry attempts for each failed request.
        """
        self.max_connections = max_connections
        self.decimal_sep = decimal_sep
        self.request_timeout = request_timeout
        self.overall_timeout = overall_timeout
        self.retries = retries

    async def fetch_html(
        self,
        session: aiohttp.ClientSession,
        url: str,
        semaphore: asyncio.Semaphore,
    ) -> str:
        """Fetch the HTML document from *url* with rate-limiting and retries.

        Args:
            session: The :class:`aiohttp.ClientSession` used for HTTP requests.
            url: The URL to fetch.
            semaphore: Semaphore that limits the number of concurrent connections.

        Returns:
            HTML content as a string, or an empty string when all retries
            are exhausted.
        """
        async with semaphore:
            for attempt in range(self.retries):
                try:
                    async with session.get(url, timeout=self.request_timeout) as response:
                        response.raise_for_status()
                        return await response.text()
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for {url}: {e}")
                    await asyncio.sleep(1)
        return ""

    def parse_html(self, html: str, indice_name: str) -> ScrapeResult:
        """Parse the HTML page and extract financial data.

        Args:
            html: HTML content of a Boursorama historical price page.
            indice_name: Display name of the stock/index.

        Returns:
            A :class:`ScrapeResult` populated with the extracted values.
        """
        soup = BeautifulSoup(html, 'html.parser')
        min_value: float = float('inf')
        max_value: float = float('-inf')
        min_date: Optional[str] = None
        max_date: Optional[str] = None

        for row in soup.find_all("tr", class_="c-table__row"):
            cells = row.find_all("td")
            if len(cells) >= 6:
                date = cells[0].get_text(strip=True)
                for cell in cells[1:]:
                    cell_text = cell.get_text(strip=True)
                    if '%' in cell_text:
                        continue
                    try:
                        value = float(cell_text.replace(',', '.'))
                        if value < min_value:
                            min_value = value
                            min_date = date
                        if value > max_value:
                            max_value = value
                            max_date = date
                    except ValueError:
                        continue

        if min_value == float('inf'):
            min_value = 0.0
            min_date = ''
        if max_value == float('-inf'):
            max_value = 0.0
            max_date = ''

        try:
            daily_indice = float(
                soup.find("span", {"class": "c-instrument c-instrument--last"})
                .text.strip()
                .replace(',', '.')
            )
        except (AttributeError, ValueError):
            print("Error extracting daily index value.")
            daily_indice = 0.0

        return ScrapeResult(
            name=indice_name,
            daily_value=daily_indice,
            max_value=max_value,
            max_date=max_date or '',
            min_value=min_value,
            min_date=min_date or '',
        )

    async def scrape(
        self,
        urls_config: List[Tuple[str, str, int]],
    ) -> List[ScrapeResult]:
        """Scrape all enabled URLs and return a list of results.

        Args:
            urls_config: List of ``(url, name, enabled)`` tuples.  Entries
                with *enabled* equal to ``0`` are silently skipped.

        Returns:
            List of :class:`ScrapeResult` objects, one per successfully
            scraped URL, in the original order.
        """
        filtered: List[Tuple[str, str]] = [
            (url, name)
            for url, name, enabled in urls_config
            if enabled == 1
        ]
        if not filtered:
            return []

        urls = [url for url, _ in filtered]
        names = [name for _, name in filtered]

        semaphore = asyncio.Semaphore(self.max_connections)
        client_timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(
            timeout=client_timeout,
            headers={'User-Agent': f'bsoup/{VERSION}'},
        ) as session:
            tasks = [
                asyncio.create_task(self.fetch_html(session, url, semaphore))
                for url in urls
            ]
            done, pending = await asyncio.wait(tasks, timeout=self.overall_timeout)
            for p in pending:
                p.cancel()

            html_documents = [''] * len(tasks)
            for i, task in enumerate(tasks):
                if task in done and not task.cancelled():
                    try:
                        html_documents[i] = task.result()
                    except Exception:
                        html_documents[i] = ''

        results: List[ScrapeResult] = []
        for html, name in zip(html_documents, names):
            print(f"Processing {name} ...")
            if html:
                results.append(self.parse_html(html, name))

        return results

    async def scrape_to_csv(
        self,
        urls_config: List[Tuple[str, str, int]],
        output_dir: str,
        filename_suffix: str = 'output',
    ) -> str:
        """Scrape all enabled URLs and write the results to a CSV file.

        Args:
            urls_config: List of ``(url, name, enabled)`` tuples.
            output_dir: Directory where the CSV file will be written.  The
                directory is created automatically if it does not exist.
            filename_suffix: Suffix appended to the CSV filename after the
                timestamp (e.g. ``'urls.json'`` → ``'urls'``).

        Returns:
            Absolute path to the created CSV file.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        suffix = filename_suffix.replace('.json', '')
        timestamp = datetime.today().strftime("%Y%m%d_%H%M")
        file_path = os.path.join(output_dir, f'indices_{timestamp}_{suffix}.csv')

        results = await self.scrape(urls_config)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(CSV_HEADER + "\n")
            for result in results:
                line = result.to_csv_line(self.decimal_sep)
                print(line)
                f.write(line + "\n")

        print("File created here: ", file_path, " \n")
        return file_path
