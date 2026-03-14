"""Integration-style tests for Scraper.scrape and Scraper.scrape_to_csv."""

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from bsoup.scraper import CSV_HEADER, ScrapeResult, Scraper

# ---------------------------------------------------------------------------
# Minimal HTML that parse_html can extract data from
# ---------------------------------------------------------------------------
VALID_HTML = """
<html><body>
<span class="c-instrument c-instrument--last">42,500</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>42,100</td><td>42,300</td>
    <td>41,900</td><td>42,000</td><td>1000</td>
  </tr>
</table>
</body></html>
"""


def _patched_fetch(html: str = VALID_HTML):
    """Return an AsyncMock that always resolves to *html*."""
    return AsyncMock(return_value=html)


# ---------------------------------------------------------------------------
# Scraper.scrape tests
# ---------------------------------------------------------------------------

class TestScrape:
    async def test_empty_config_returns_empty_list(self):
        scraper = Scraper()
        results = await scraper.scrape([])
        assert results == []

    async def test_all_disabled_returns_empty_list(self):
        scraper = Scraper()
        results = await scraper.scrape([
            ("http://example.com", "A", 0),
            ("http://example.com/b", "B", 0),
        ])
        assert results == []

    async def test_enabled_urls_are_fetched_and_parsed(self):
        scraper = Scraper()
        urls_config = [
            ("http://example.com/a", "A", 1),
            ("http://example.com/b", "B", 0),  # disabled
            ("http://example.com/c", "C", 1),
        ]

        with patch.object(scraper, 'fetch_html', new=_patched_fetch()):
            results = await scraper.scrape(urls_config)

        # Only 2 enabled URLs → 2 results
        assert len(results) == 2
        names = [r.name for r in results]
        assert "A" in names
        assert "C" in names
        assert "B" not in names

    async def test_failed_fetch_is_excluded_from_results(self):
        scraper = Scraper()
        urls_config = [("http://example.com", "FAIL", 1)]

        # fetch returns empty string → no result appended
        with patch.object(scraper, 'fetch_html', new=AsyncMock(return_value="")):
            results = await scraper.scrape(urls_config)

        assert results == []

    async def test_scrape_task_with_exception_is_handled(self):
        """A task that raises an exception is silently skipped."""
        scraper = Scraper()

        async def raising_fetch(session, url, semaphore):
            raise RuntimeError("unexpected task error")

        with patch.object(scraper, 'fetch_html', new=raising_fetch), \
             patch("bsoup.scraper.aiohttp.ClientSession") as MockCS:
            mock_cs = AsyncMock()
            MockCS.return_value.__aenter__ = AsyncMock(return_value=mock_cs)
            MockCS.return_value.__aexit__ = AsyncMock(return_value=False)
            results = await scraper.scrape([("http://example.com", "A", 1)])

        assert results == []

    async def test_scrape_cancels_pending_tasks_on_overall_timeout(self):
        """Tasks still running at overall_timeout are cancelled."""
        scraper = Scraper(overall_timeout=0.05)  # 50 ms

        async def slow_fetch(session, url, semaphore):
            await asyncio.sleep(5)  # Intentionally longer than the timeout
            return "<html/>"

        with patch.object(scraper, 'fetch_html', new=slow_fetch), \
             patch("bsoup.scraper.aiohttp.ClientSession") as MockCS:
            mock_cs = AsyncMock()
            MockCS.return_value.__aenter__ = AsyncMock(return_value=mock_cs)
            MockCS.return_value.__aexit__ = AsyncMock(return_value=False)
            results = await scraper.scrape([("http://example.com", "A", 1)])

        assert results == []

    async def test_result_fields_are_populated(self):
        scraper = Scraper()
        urls_config = [("http://example.com", "STOCK", 1)]

        with patch.object(scraper, 'fetch_html', new=_patched_fetch()):
            results = await scraper.scrape(urls_config)

        assert len(results) == 1
        r = results[0]
        assert isinstance(r, ScrapeResult)
        assert r.name == "STOCK"
        assert r.daily_value == pytest.approx(42.5)


# ---------------------------------------------------------------------------
# Scraper.scrape_to_csv tests
# ---------------------------------------------------------------------------

class TestScrapeToCSV:
    async def test_creates_csv_file(self, tmp_path):
        scraper = Scraper()
        mock_result = ScrapeResult(
            name="TEST", daily_value=42.5,
            max_value=43.5, max_date="02/01/2024",
            min_value=41.9, min_date="01/01/2024",
        )

        with patch.object(scraper, 'scrape', new=AsyncMock(return_value=[mock_result])):
            file_path = await scraper.scrape_to_csv(
                [("http://example.com", "TEST", 1)],
                output_dir=str(tmp_path),
                filename_suffix="test",
            )

        assert os.path.exists(file_path)
        assert file_path.endswith('.csv')

    async def test_csv_header_is_written(self, tmp_path):
        scraper = Scraper()
        with patch.object(scraper, 'scrape', new=AsyncMock(return_value=[])):
            file_path = await scraper.scrape_to_csv(
                [], output_dir=str(tmp_path), filename_suffix="empty"
            )

        with open(file_path, encoding='utf-8') as f:
            header = f.readline().strip()
        assert header == CSV_HEADER

    async def test_csv_contains_result_line(self, tmp_path):
        scraper = Scraper(decimal_sep=',')
        mock_result = ScrapeResult(
            name="IDX", daily_value=100.0,
            max_value=110.0, max_date="10/01/2024",
            min_value=90.0, min_date="05/01/2024",
        )
        with patch.object(scraper, 'scrape', new=AsyncMock(return_value=[mock_result])):
            file_path = await scraper.scrape_to_csv(
                [("http://example.com", "IDX", 1)],
                output_dir=str(tmp_path),
                filename_suffix="test",
            )

        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        assert "IDX;" in content
        assert "100,000" in content

    async def test_output_directory_is_created_if_missing(self, tmp_path):
        new_dir = str(tmp_path / "new" / "nested")
        scraper = Scraper()

        with patch.object(scraper, 'scrape', new=AsyncMock(return_value=[])):
            file_path = await scraper.scrape_to_csv(
                [], output_dir=new_dir, filename_suffix="nested"
            )

        assert os.path.isdir(new_dir)
        assert os.path.exists(file_path)

    async def test_json_suffix_is_stripped_from_filename(self, tmp_path):
        scraper = Scraper()
        with patch.object(scraper, 'scrape', new=AsyncMock(return_value=[])):
            file_path = await scraper.scrape_to_csv(
                [], output_dir=str(tmp_path), filename_suffix="urls.json"
            )

        assert 'urls.json' not in os.path.basename(file_path)
        assert 'urls' in os.path.basename(file_path)
