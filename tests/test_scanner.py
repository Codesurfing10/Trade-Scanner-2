"""Unit tests for scanner/scanner.py — uses mocked data, no network calls."""
import math
import unittest
from unittest.mock import patch

import pandas as pd

from scanner.scanner import (
    _action_signal,
    _classify_macd,
    _classify_rsi,
    _classify_stage,
    _classify_stage2_volume_confirmation,
    _classify_trend,
    _classify_volume,
    _determine_signal_type,
    scan_symbol,
)


def _make_df(close_values, n_extra=10):
    """Create a minimal OHLCV DataFrame with the given close values."""
    closes = list(close_values)
    size = len(closes)
    df = pd.DataFrame(
        {
            "Open":   [c - 0.5 for c in closes],
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * size,
        }
    )
    df.index = pd.date_range("2025-01-01", periods=size, freq="B")
    return df


class TestClassifyRSI(unittest.TestCase):
    def test_oversold(self):
        self.assertIn("Oversold", _classify_rsi(25.0))

    def test_overbought(self):
        self.assertIn("Overbought", _classify_rsi(75.0))

    def test_momentum(self):
        self.assertIn("Momentum", _classify_rsi(60.0))

    def test_neutral_range(self):
        self.assertEqual(_classify_rsi(45.0), [])

    def test_nan(self):
        self.assertEqual(_classify_rsi(float("nan")), [])


class TestClassifyTrend(unittest.TestCase):
    def test_bullish(self):
        # price > sma20 > sma50
        signals = _classify_trend(200, 180, 150)
        self.assertIn("Bullish", signals)

    def test_bearish(self):
        # price < sma20 < sma50
        signals = _classify_trend(100, 120, 150)
        self.assertIn("Bearish", signals)

    def test_mixed(self):
        signals = _classify_trend(130, 120, 150)
        self.assertEqual(signals, [])

    def test_nan_values(self):
        self.assertEqual(_classify_trend(150, float("nan"), 100), [])


class TestClassifyMACD(unittest.TestCase):
    def test_bullish(self):
        signals = _classify_macd({"macd": 1.0, "signal": 0.5, "histogram": 0.5})
        self.assertIn("MACD Bullish", signals)

    def test_bearish(self):
        signals = _classify_macd({"macd": -1.0, "signal": -0.5, "histogram": -0.5})
        self.assertIn("MACD Bearish", signals)

    def test_nan(self):
        nan = float("nan")
        self.assertEqual(_classify_macd({"macd": nan, "signal": nan, "histogram": nan}), [])


class TestClassifyVolume(unittest.TestCase):
    def test_high_volume(self):
        self.assertIn("High Volume", _classify_volume(2.5))

    def test_normal_volume(self):
        self.assertEqual(_classify_volume(1.0), [])

    def test_nan(self):
        self.assertEqual(_classify_volume(float("nan")), [])


class TestDetermineSignalType(unittest.TestCase):
    def test_oversold_priority(self):
        self.assertEqual(_determine_signal_type(["Oversold", "Bullish"]), "oversold")

    def test_overbought_priority(self):
        self.assertEqual(_determine_signal_type(["Overbought"]), "overbought")

    def test_bullish(self):
        self.assertEqual(_determine_signal_type(["Bullish", "MACD Bullish"]), "bullish")

    def test_bearish(self):
        self.assertEqual(_determine_signal_type(["Bearish", "MACD Bearish"]), "bearish")

    def test_neutral(self):
        self.assertEqual(_determine_signal_type([]), "neutral")


class TestStageAnalysis(unittest.TestCase):
    def test_stage2_advancing(self):
        self.assertEqual(_classify_stage(120.0, 100.0, 0.5), "Stage 2 (Advancing)")

    def test_stage4_declining(self):
        self.assertEqual(_classify_stage(90.0, 100.0, -0.5), "Stage 4 (Declining)")

    def test_stage_na(self):
        self.assertEqual(_classify_stage(100.0, float("nan"), 0.1), "N/A")

    def test_stage2_volume_confirmation(self):
        self.assertEqual(
            _classify_stage2_volume_confirmation("Stage 2 (Advancing)", 2_000_000, 1_500_000.0),
            "Strong Volume Confirmation",
        )

    def test_stage2_volume_not_confirmed(self):
        self.assertEqual(
            _classify_stage2_volume_confirmation("Stage 2 (Advancing)", 1_000_000, 1_500_000.0),
            "N/A",
        )

    def test_action_signal_rules(self):
        self.assertEqual(_action_signal("Stage 2 (Advancing)", "Strong Volume Confirmation"), "BUY")
        self.assertEqual(_action_signal("Stage 4 (Declining)", "N/A"), "SELL")
        self.assertEqual(_action_signal("Transitional", "N/A"), "HOLD")


class TestScanSymbol(unittest.TestCase):
    def _make_rising_df(self, size=260):
        closes = [100.0 + i * 0.5 for i in range(size)]
        return _make_df(closes)

    @patch("scanner.scanner.fetch_info", return_value={"shortName": "Test Corp"})
    @patch("scanner.scanner.fetch_history")
    def test_returns_expected_keys(self, mock_history, mock_info):
        mock_history.return_value = self._make_rising_df()
        result = scan_symbol("TEST")

        self.assertIsNotNone(result)
        for key in ("symbol", "name", "date", "price", "change_pct", "rsi", "sma20",
                    "sma50", "sma150", "slope_sma150", "stage_classification",
                    "confirms_stage2_volume", "action_signal", "volume_10week_ma",
                    "signals", "signal_type"):
            self.assertIn(key, result)
        self.assertRegex(result["date"], r"^\d{4}-\d{2}-\d{2}$")

    @patch("scanner.scanner.fetch_info", return_value={})
    @patch("scanner.scanner.fetch_history")
    def test_insufficient_history_returns_none(self, mock_history, _mock_info):
        mock_history.return_value = _make_df([100.0] * 10)
        result = scan_symbol("SHORT")
        self.assertIsNone(result)

    @patch("scanner.scanner.fetch_info", return_value={})
    @patch("scanner.scanner.fetch_history")
    def test_empty_df_returns_none(self, mock_history, _mock_info):
        mock_history.return_value = pd.DataFrame()
        result = scan_symbol("EMPTY")
        self.assertIsNone(result)

    @patch("scanner.scanner.fetch_info", return_value={"shortName": "Rising Corp"})
    @patch("scanner.scanner.fetch_history")
    def test_rising_stock_is_bullish(self, mock_history, _mock_info):
        mock_history.return_value = self._make_rising_df()
        result = scan_symbol("BULL")
        self.assertIsNotNone(result)
        self.assertNotEqual(result["signal_type"], "bearish")


if __name__ == "__main__":
    unittest.main()
