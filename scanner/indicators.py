"""
Technical indicators used by the Trade Scanner.

All functions accept a pandas Series (or DataFrame column) and return a single
float value representing the most recent indicator reading.  Returns float('nan')
when there is insufficient data.
"""
from __future__ import annotations

import math

import pandas as pd


def _require(series: pd.Series, n: int) -> bool:
    """Return True when *series* has at least *n* non-NaN values."""
    return series.dropna().shape[0] >= n


def rsi(series: pd.Series, period: int = 14) -> float:
    """Relative Strength Index (Wilder smoothing)."""
    if not _require(series, period + 1):
        return float("nan")
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    gain_last = float(gain.iloc[-1])
    loss_last = float(loss.iloc[-1])
    if math.isnan(gain_last) or math.isnan(loss_last):
        return float("nan")
    if loss_last == 0:
        return 100.0 if gain_last > 0 else 50.0
    rs = gain_last / loss_last
    return float(100 - (100 / (1 + rs)))


def sma(series: pd.Series, period: int) -> float:
    """Simple Moving Average."""
    if not _require(series, period):
        return float("nan")
    return float(series.rolling(window=period).mean().iloc[-1])


def slope_sma150(series: pd.Series, window: int = 20) -> float:
    """Slope of SMA150 over *window* sessions.

    Definition:
        (sma150_today - sma150_[window]_sessions_ago) / window
    """
    period = 150
    if not _require(series, period + window):
        return float("nan")
    sma150_series = series.rolling(window=period).mean()
    current = float(sma150_series.iloc[-1])
    past = float(sma150_series.iloc[-(window + 1)])
    if math.isnan(current) or math.isnan(past):
        return float("nan")
    return float((current - past) / window)


def ema(series: pd.Series, period: int) -> float:
    """Exponential Moving Average."""
    if not _require(series, period):
        return float("nan")
    return float(series.ewm(span=period, adjust=False).mean().iloc[-1])


def macd(series: pd.Series) -> dict[str, float]:
    """MACD line, signal line, and histogram (12/26/9 defaults).

    Returns a dict with keys ``macd``, ``signal``, and ``histogram``.
    All values are ``nan`` when there is insufficient data.
    """
    nan = float("nan")
    if not _require(series, 35):
        return {"macd": nan, "signal": nan, "histogram": nan}
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1]),
    }


def volume_ratio(volume: pd.Series, period: int = 20) -> float:
    """Current volume divided by the average of the previous *period* sessions."""
    if not _require(volume, period + 1):
        return float("nan")
    avg = float(volume.shift(1).rolling(window=period).mean().iloc[-1])
    if avg == 0 or math.isnan(avg):
        return float("nan")
    return float(volume.iloc[-1] / avg)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Average True Range."""
    if not _require(close, period + 1):
        return float("nan")
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return float(tr.rolling(window=period).mean().iloc[-1])
