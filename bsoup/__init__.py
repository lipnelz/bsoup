"""bsoup – Boursorama financial data scraper.

Public interface::

    import asyncio
    from bsoup import Scraper, ScrapeResult

    urls_config = [
        ("https://www.boursorama.com/cours/historique/1rPEN", "BOUYGUES", 1),
        ("https://www.boursorama.com/cours/historique/1rPAXA", "AXA", 1),
    ]

    scraper = Scraper(decimal_sep=',')
    results: list[ScrapeResult] = asyncio.run(scraper.scrape(urls_config))

    for r in results:
        print(r.name, r.daily_value, r.max_value, r.min_value)
"""

from bsoup.scraper import CSV_HEADER, VERSION, ScrapeResult, Scraper

__version__ = VERSION
__all__ = ["Scraper", "ScrapeResult", "CSV_HEADER", "__version__"]
