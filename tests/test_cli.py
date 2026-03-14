"""Tests for the CLI entry-point (bsoup/cli.py)."""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from bsoup.cli import get_output_path, main


# ---------------------------------------------------------------------------
# get_output_path tests
# ---------------------------------------------------------------------------

class TestGetOutputPath:
    def test_local_returns_script_dir(self, tmp_path):
        result = get_output_path(local=True, script_dir=str(tmp_path))
        assert result == str(tmp_path)

    def test_desktop_exists_returns_desktop(self, tmp_path):
        desktop = tmp_path / "Desktop"
        desktop.mkdir()

        with patch("os.path.expanduser", return_value=str(tmp_path)), \
             patch("os.name", "posix"), \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=FileNotFoundError):
            result = get_output_path(local=False, script_dir=str(tmp_path))

        # Desktop exists → should use it
        assert "Desktop" in result

    def test_desktop_missing_falls_back_to_home(self, tmp_path):
        with patch("os.path.expanduser", return_value=str(tmp_path)), \
             patch("os.name", "posix"), \
             patch("os.path.exists", return_value=False), \
             patch("builtins.open", side_effect=FileNotFoundError):
            result = get_output_path(local=False, script_dir=str(tmp_path))

        assert result == str(tmp_path)

    def test_windows_uses_userprofile(self, tmp_path):
        desktop = tmp_path / "Desktop"
        desktop.mkdir()

        with patch("os.name", "nt"), \
             patch("os.path.expanduser", return_value=str(tmp_path)), \
             patch.dict("os.environ", {"USERPROFILE": str(tmp_path)}), \
             patch("os.path.exists", return_value=True):
            result = get_output_path(local=False, script_dir=str(tmp_path))

        assert "Desktop" in result

    def test_windows_fallback_to_home_when_no_desktop(self, tmp_path):
        with patch("os.name", "nt"), \
             patch("os.path.expanduser", return_value=str(tmp_path)), \
             patch.dict("os.environ", {"USERPROFILE": str(tmp_path)}), \
             patch("os.path.exists", return_value=False):
            result = get_output_path(local=False, script_dir=str(tmp_path))

        assert result == str(tmp_path)

    def test_xdg_desktop_dir_is_used_when_present(self, tmp_path):
        xdg_desktop = tmp_path / "XDGDesktop"
        xdg_desktop.mkdir()
        xdg_content = f'XDG_DESKTOP_DIR="$HOME/XDGDesktop"\n'

        with patch("os.name", "posix"), \
             patch("os.path.expanduser", return_value=str(tmp_path)), \
             patch("builtins.open", mock_open(read_data=xdg_content)), \
             patch("os.path.exists", return_value=True):
            result = get_output_path(local=False, script_dir=str(tmp_path))

        assert "XDGDesktop" in result


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------

VALID_URLS_JSON = json.dumps([
    ["https://example.com/a", "A", 1],
])

INVALID_JSON = "not valid json"

INVALID_FORMAT = json.dumps([["only", "two"]])


class TestMain:
    def _run_main(self, argv):
        with patch.object(sys, 'argv', ['bsoup'] + argv):
            main()

    def test_file_not_found_exits_with_1(self):
        with patch.object(sys, 'argv', ['bsoup', '-f', 'nonexistent.json']):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_invalid_json_exits_with_1(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text(INVALID_JSON)

        with patch.object(sys, 'argv', ['bsoup', '-f', str(bad_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_invalid_format_exits_with_1(self, tmp_path):
        bad_file = tmp_path / "bad_format.json"
        bad_file.write_text(INVALID_FORMAT)

        with patch.object(sys, 'argv', ['bsoup', '-f', str(bad_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1

    def test_success_calls_scrape_to_csv(self, tmp_path):
        urls_file = tmp_path / "urls.json"
        urls_file.write_text(VALID_URLS_JSON)

        mock_scraper = MagicMock()
        mock_scraper.scrape_to_csv = AsyncMock(return_value=str(tmp_path / "out.csv"))

        with patch.object(sys, 'argv', ['bsoup', '-f', str(urls_file), '-l']), \
             patch('bsoup.cli.Scraper', return_value=mock_scraper):
            main()

        mock_scraper.scrape_to_csv.assert_awaited_once()

    def test_local_flag_is_forwarded(self, tmp_path):
        urls_file = tmp_path / "urls.json"
        urls_file.write_text(VALID_URLS_JSON)

        captured_output_dir = {}

        async def capture_call(urls, output_dir, filename_suffix):
            captured_output_dir['dir'] = output_dir
            return str(tmp_path / "out.csv")

        mock_scraper = MagicMock()
        mock_scraper.scrape_to_csv = capture_call

        with patch.object(sys, 'argv', ['bsoup', '-f', str(urls_file), '-l']), \
             patch('bsoup.cli.Scraper', return_value=mock_scraper):
            main()

        # When --local, output_dir must equal the package directory
        assert captured_output_dir.get('dir') is not None

    def test_sep_comma_is_forwarded(self, tmp_path):
        urls_file = tmp_path / "urls.json"
        urls_file.write_text(VALID_URLS_JSON)

        mock_scraper = MagicMock()
        mock_scraper.scrape_to_csv = AsyncMock(return_value=str(tmp_path / "out.csv"))

        with patch.object(sys, 'argv', ['bsoup', '-f', str(urls_file), '-l', '-s', ',']), \
             patch('bsoup.cli.Scraper', return_value=mock_scraper) as MockScraper:
            main()

        MockScraper.assert_called_once_with(decimal_sep=',')
