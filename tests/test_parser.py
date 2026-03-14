"""Tests for HTML parsing and ScrapeResult formatting."""

import pytest
from bsoup.scraper import Scraper, ScrapeResult

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>
<span class="c-instrument c-instrument--last">42,500</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>42,100</td><td>42,300</td>
    <td>41,900</td><td>42,000</td><td>+1,0%</td>
  </tr>
  <tr class="c-table__row">
    <td>02/01/2024</td><td>43,200</td><td>43,500</td>
    <td>42,800</td><td>43,000</td><td>+2,0%</td>
  </tr>
</table>
</body></html>
"""

HTML_WITH_PERCENTAGE = """
<html><body>
<span class="c-instrument c-instrument--last">10,000</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>10,000</td><td>+1,5%</td>
    <td>9,800</td><td>9,900</td><td>-0,5%</td>
  </tr>
</table>
</body></html>
"""

HTML_INSUFFICIENT_CELLS = """
<html><body>
<span class="c-instrument c-instrument--last">10,000</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>10,000</td>
  </tr>
</table>
</body></html>
"""

HTML_NON_NUMERIC_CELLS = """
<html><body>
<span class="c-instrument c-instrument--last">10,000</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>N/A</td><td>N/A</td>
    <td>N/A</td><td>N/A</td><td>N/A</td>
  </tr>
</table>
</body></html>
"""

HTML_MISSING_DAILY_SPAN = """
<html><body>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>42,100</td><td>42,300</td>
    <td>41,900</td><td>42,000</td><td>+1,0%</td>
  </tr>
</table>
</body></html>
"""

HTML_INVALID_DAILY_SPAN = """
<html><body>
<span class="c-instrument c-instrument--last">N/A</span>
<table>
  <tr class="c-table__row">
    <td>01/01/2024</td><td>42,100</td><td>42,300</td>
    <td>41,900</td><td>42,000</td><td>1000</td>
  </tr>
</table>
</body></html>
"""

EMPTY_HTML = "<html><body></body></html>"


# ---------------------------------------------------------------------------
# parse_html tests
# ---------------------------------------------------------------------------

class TestParseHtml:
    def setup_method(self):
        self.scraper = Scraper()

    def test_basic_extraction(self):
        result = self.scraper.parse_html(SAMPLE_HTML, "TEST")
        assert result.name == "TEST"
        assert result.daily_value == pytest.approx(42.5)
        assert result.max_value == pytest.approx(43.5)
        assert result.max_date == "02/01/2024"
        assert result.min_value == pytest.approx(41.9)
        assert result.min_date == "01/01/2024"

    def test_empty_html_returns_zeros(self):
        result = self.scraper.parse_html(EMPTY_HTML, "EMPTY")
        assert result.name == "EMPTY"
        assert result.daily_value == 0.0
        assert result.max_value == 0.0
        assert result.min_value == 0.0
        assert result.max_date == ''
        assert result.min_date == ''

    def test_percentage_cells_are_skipped(self):
        result = self.scraper.parse_html(HTML_WITH_PERCENTAGE, "PCT")
        # The '+1,5%' cell must not be treated as a numeric value
        assert result.max_value == pytest.approx(10.0)
        assert result.min_value == pytest.approx(9.8)

    def test_rows_with_fewer_than_6_cells_are_skipped(self):
        result = self.scraper.parse_html(HTML_INSUFFICIENT_CELLS, "SHORT")
        assert result.max_value == 0.0
        assert result.min_value == 0.0
        assert result.daily_value == pytest.approx(10.0)

    def test_non_numeric_cells_are_skipped(self):
        result = self.scraper.parse_html(HTML_NON_NUMERIC_CELLS, "NAN")
        assert result.max_value == 0.0
        assert result.min_value == 0.0

    def test_missing_daily_span_defaults_to_zero(self):
        result = self.scraper.parse_html(HTML_MISSING_DAILY_SPAN, "NOSPAN")
        assert result.daily_value == 0.0
        # Table data is still parsed
        assert result.max_value == pytest.approx(42.3)
        assert result.min_value == pytest.approx(41.9)

    def test_invalid_daily_span_text_defaults_to_zero(self):
        result = self.scraper.parse_html(HTML_INVALID_DAILY_SPAN, "BADSPAN")
        assert result.daily_value == 0.0


# ---------------------------------------------------------------------------
# ScrapeResult.to_csv_line tests
# ---------------------------------------------------------------------------

class TestScrapeResultToCsvLine:
    def _make_result(self):
        return ScrapeResult(
            name="TEST",
            daily_value=42.5,
            max_value=43.5,
            max_date="02/01/2024",
            min_value=41.9,
            min_date="01/01/2024",
        )

    def test_dot_separator(self):
        line = self._make_result().to_csv_line('.')
        assert line == "TEST;42.500;02/01/2024;43.500;01/01/2024;41.900;"

    def test_comma_separator(self):
        line = self._make_result().to_csv_line(',')
        assert line == "TEST;42,500;02/01/2024;43,500;01/01/2024;41,900;"

    def test_default_separator_is_dot(self):
        line = self._make_result().to_csv_line()
        assert '.' in line
        assert ',' not in line.split(';')[1]  # Only check numeric fields

    def test_zero_values(self):
        result = ScrapeResult(
            name="ZERO", daily_value=0.0,
            max_value=0.0, max_date='',
            min_value=0.0, min_date='',
        )
        line = result.to_csv_line('.')
        assert line == "ZERO;0.000;;0.000;;0.000;"
