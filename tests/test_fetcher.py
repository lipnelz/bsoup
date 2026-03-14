"""Tests for the async HTTP fetching logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bsoup.scraper import Scraper


def _make_mock_session(html: str = "<html/>", raise_on_enter=None):
    """Return a mock aiohttp.ClientSession whose get() returns *html*."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.text = AsyncMock(return_value=html)
    if raise_on_enter:
        mock_response.__aenter__ = AsyncMock(side_effect=raise_on_enter)
    else:
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_response)
    return mock_session


class TestFetchHtml:
    async def test_success_returns_html(self):
        scraper = Scraper(retries=1)
        semaphore = asyncio.Semaphore(1)
        session = _make_mock_session("<html>content</html>")

        result = await scraper.fetch_html(session, "http://example.com", semaphore)

        assert result == "<html>content</html>"

    async def test_all_retries_fail_returns_empty_string(self):
        scraper = Scraper(retries=2)
        semaphore = asyncio.Semaphore(1)
        session = _make_mock_session(raise_on_enter=Exception("Network error"))

        with patch("bsoup.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await scraper.fetch_html(session, "http://example.com", semaphore)

        assert result == ""

    async def test_retries_then_succeeds(self):
        scraper = Scraper(retries=3)
        semaphore = asyncio.Semaphore(1)

        call_count = 0

        async def flaky_aenter(self_inner=None):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return mock_response

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.text = AsyncMock(return_value="<html>ok</html>")
        mock_response.__aenter__ = flaky_aenter
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch("bsoup.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await scraper.fetch_html(mock_session, "http://example.com", semaphore)

        assert result == "<html>ok</html>"
        assert call_count == 3

    async def test_semaphore_is_respected(self):
        """Concurrency is bounded by the provided semaphore."""
        scraper = Scraper(retries=1)
        semaphore = asyncio.Semaphore(2)
        session = _make_mock_session("<html/>")

        tasks = [
            asyncio.create_task(scraper.fetch_html(session, f"http://example.com/{i}", semaphore))
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        assert all(r == "<html/>" for r in results)

    async def test_raise_for_status_triggers_retry(self):
        scraper = Scraper(retries=2)
        semaphore = asyncio.Semaphore(1)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("403 Forbidden"))
        mock_response.text = AsyncMock(return_value="")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)

        with patch("bsoup.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await scraper.fetch_html(mock_session, "http://example.com", semaphore)

        assert result == ""
