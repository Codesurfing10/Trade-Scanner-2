"""Unit tests for scanner/data.py."""
import unittest
from unittest.mock import patch

import pandas as pd

from scanner.data import fetch_history


class TestFetchHistory(unittest.TestCase):
    @patch("scanner.data.yf.download")
    def test_multiindex_download_is_flattened(self, mock_download):
        index = pd.date_range("2025-01-01", periods=3, freq="B")
        columns = pd.MultiIndex.from_arrays(
            [
                ["Open", "High", "Low", "Close", "Volume"],
                ["TEST", "TEST", "TEST", "TEST", "TEST"],
            ]
        )
        mock_download.return_value = pd.DataFrame(
            [
                [10.0, 11.0, 9.0, 10.5, 1_000_000],
                [10.5, 11.5, 9.5, 11.0, 1_200_000],
                [11.0, 12.0, 10.0, 11.5, 1_100_000],
            ],
            index=index,
            columns=columns,
        )

        result = fetch_history("TEST")

        self.assertListEqual(list(result.columns), ["Open", "High", "Low", "Close", "Volume"])
        self.assertEqual(result.index[-1].strftime("%Y-%m-%d"), "2025-01-03")


if __name__ == "__main__":
    unittest.main()
