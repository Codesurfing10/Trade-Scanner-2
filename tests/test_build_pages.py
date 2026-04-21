"""Unit tests for build_pages helpers."""
import unittest

from build_pages import _ensure_row_dates


class TestBuildPagesHelpers(unittest.TestCase):
    def test_ensure_row_dates_uses_updated_fallback(self):
        payload = {
            "updated": "2026-04-21T06:02:41Z",
            "stocks": [
                {"symbol": "AAPL"},
                {"symbol": "MSFT", "date": "2026-04-20"},
            ],
        }

        _ensure_row_dates(payload)

        self.assertEqual(payload["stocks"][0]["date"], "2026-04-21")
        self.assertEqual(payload["stocks"][1]["date"], "2026-04-20")


if __name__ == "__main__":
    unittest.main()
