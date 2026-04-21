"""Unit tests for scanner/indicators.py — no network calls required."""
import math
import unittest

import numpy as np
import pandas as pd

from scanner.indicators import atr, ema, macd, rsi, slope_sma150, sma, volume_ratio


def _series(values):
    return pd.Series(values, dtype=float)


class TestSMA(unittest.TestCase):
    def test_basic(self):
        s = _series([1, 2, 3, 4, 5])
        result = sma(s, 3)
        self.assertAlmostEqual(result, 4.0)  # mean of last 3: 3,4,5

    def test_insufficient_data(self):
        result = sma(_series([1, 2]), 5)
        self.assertTrue(math.isnan(result))

    def test_exact_period(self):
        result = sma(_series([10, 20, 30]), 3)
        self.assertAlmostEqual(result, 20.0)


class TestEMA(unittest.TestCase):
    def test_returns_float(self):
        s = _series(range(1, 30))
        result = ema(s, 9)
        self.assertIsInstance(result, float)
        self.assertFalse(math.isnan(result))

    def test_insufficient_data(self):
        result = ema(_series([1, 2]), 5)
        self.assertTrue(math.isnan(result))


class TestRSI(unittest.TestCase):
    def _flat_series(self, n=50):
        """Flat series → RSI should converge to ~50."""
        return _series([100.0] * n)

    def test_flat_series(self):
        result = rsi(self._flat_series())
        # RSI of a perfectly flat series produces NaN (no gains/losses)
        # or 50 depending on implementation; just check it doesn't crash
        self.assertIsInstance(result, float)

    def test_rising_series_overbought(self):
        """Strongly rising prices → RSI near 100."""
        prices = [float(i) for i in range(1, 60)]
        result = rsi(_series(prices))
        self.assertFalse(math.isnan(result))
        self.assertGreater(result, 70)

    def test_falling_series_oversold(self):
        """Strongly falling prices → RSI near 0."""
        prices = [float(60 - i) for i in range(60)]
        result = rsi(_series(prices))
        self.assertFalse(math.isnan(result))
        self.assertLess(result, 30)

    def test_insufficient_data(self):
        result = rsi(_series([1, 2, 3]))
        self.assertTrue(math.isnan(result))


class TestMACD(unittest.TestCase):
    def test_returns_dict_keys(self):
        s = _series([float(i) for i in range(1, 60)])
        result = macd(s)
        self.assertIn("macd", result)
        self.assertIn("signal", result)
        self.assertIn("histogram", result)

    def test_insufficient_data(self):
        result = macd(_series([1.0] * 10))
        self.assertTrue(math.isnan(result["macd"]))

    def test_histogram_equals_macd_minus_signal(self):
        s = _series([float(i) + 0.5 * (i % 3) for i in range(60)])
        result = macd(s)
        expected = result["macd"] - result["signal"]
        self.assertAlmostEqual(result["histogram"], expected, places=10)


class TestVolumeRatio(unittest.TestCase):
    def test_double_volume(self):
        vols = [1_000_000.0] * 20 + [2_000_000.0]
        result = volume_ratio(_series(vols))
        self.assertAlmostEqual(result, 2.0, places=1)

    def test_insufficient_data(self):
        result = volume_ratio(_series([1.0] * 5))
        self.assertTrue(math.isnan(result))

    def test_zero_avg(self):
        vols = [0.0] * 21
        result = volume_ratio(_series(vols))
        self.assertTrue(math.isnan(result))


class TestATR(unittest.TestCase):
    def test_constant_candles(self):
        n = 30
        high  = _series([110.0] * n)
        low   = _series([90.0]  * n)
        close = _series([100.0] * n)
        result = atr(high, low, close)
        self.assertFalse(math.isnan(result))
        self.assertGreater(result, 0)

    def test_insufficient_data(self):
        h = _series([1.0] * 5)
        l = _series([0.9] * 5)
        c = _series([1.0] * 5)
        result = atr(h, l, c)
        self.assertTrue(math.isnan(result))


class TestSlopeSMA150(unittest.TestCase):
    def test_returns_positive_for_rising_series(self):
        s = _series([100.0 + i for i in range(200)])
        result = slope_sma150(s)
        self.assertFalse(math.isnan(result))
        self.assertGreater(result, 0)

    def test_insufficient_data(self):
        result = slope_sma150(_series([100.0] * 100))
        self.assertTrue(math.isnan(result))


if __name__ == "__main__":
    unittest.main()
