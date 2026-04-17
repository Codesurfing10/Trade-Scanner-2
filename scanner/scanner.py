"""
Core scanner logic.

``scan_symbol`` processes a single ticker and returns a structured dict.
``scan_stocks`` runs the scanner across a list of symbols in sequence.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from .data import DEFAULT_SYMBOLS, fetch_history, fetch_info
from .indicators import atr, ema, macd, rsi, sma, volume_ratio

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------

def _classify_rsi(rsi_val: float) -> list[str]:
    signals: list[str] = []
    if math.isnan(rsi_val):
        return signals
    if rsi_val < 30:
        signals.append("Oversold")
    elif rsi_val > 70:
        signals.append("Overbought")
    elif 50 < rsi_val <= 70:
        signals.append("Momentum")
    return signals


def _classify_trend(price: float, sma20: float, sma50: float) -> list[str]:
    signals: list[str] = []
    if math.isnan(sma20) or math.isnan(sma50):
        return signals
    if price > sma20 > sma50:
        signals.append("Bullish")
    elif price < sma20 < sma50:
        signals.append("Bearish")
    return signals


def _classify_macd(macd_data: dict[str, float]) -> list[str]:
    signals: list[str] = []
    histogram = macd_data.get("histogram", float("nan"))
    macd_val = macd_data.get("macd", float("nan"))
    signal_val = macd_data.get("signal", float("nan"))
    if math.isnan(histogram) or math.isnan(macd_val) or math.isnan(signal_val):
        return signals
    if macd_val > signal_val and histogram > 0:
        signals.append("MACD Bullish")
    elif macd_val < signal_val and histogram < 0:
        signals.append("MACD Bearish")
    return signals


def _classify_volume(vol_ratio: float) -> list[str]:
    if math.isnan(vol_ratio):
        return []
    if vol_ratio >= 2.0:
        return ["High Volume"]
    return []


def _determine_signal_type(signals: list[str]) -> str:
    """Roll up individual signals into a top-level category for UI colouring."""
    if "Oversold" in signals:
        return "oversold"
    if "Overbought" in signals:
        return "overbought"
    bullish_count = sum(1 for s in signals if "Bullish" in s or s == "Momentum")
    bearish_count = sum(1 for s in signals if "Bearish" in s)
    if bullish_count > bearish_count:
        return "bullish"
    if bearish_count > bullish_count:
        return "bearish"
    return "neutral"


# ---------------------------------------------------------------------------
# Single-symbol scanner
# ---------------------------------------------------------------------------

def scan_symbol(symbol: str) -> dict[str, Any] | None:
    """Fetch data for *symbol* and return a result dict, or ``None`` on failure."""
    df = fetch_history(symbol, period="3mo")
    if df.empty or len(df) < 20:
        logger.warning("Skipping %s — insufficient price history", symbol)
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    price = float(close.iloc[-1])
    prev_close = float(close.iloc[-2]) if len(close) >= 2 else price
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close != 0 else 0.0

    rsi_val = rsi(close)
    sma20_val = sma(close, 20)
    sma50_val = sma(close, 50)
    ema9_val = ema(close, 9)
    macd_data = macd(close)
    vol_ratio = volume_ratio(volume)
    atr_val = atr(high, low, close)

    current_volume = int(volume.iloc[-1])
    avg_volume = int(volume.shift(1).rolling(window=20).mean().iloc[-1]) if len(volume) >= 21 else current_volume

    signals: list[str] = []
    signals.extend(_classify_rsi(rsi_val))
    signals.extend(_classify_trend(price, sma20_val, sma50_val))
    signals.extend(_classify_macd(macd_data))
    signals.extend(_classify_volume(vol_ratio))

    # Breakout: price > SMA20 with high volume and positive MACD
    if (
        not math.isnan(sma20_val)
        and price > sma20_val
        and not math.isnan(vol_ratio)
        and vol_ratio >= 1.5
        and macd_data.get("histogram", 0) > 0
    ):
        if "Breakout" not in signals:
            signals.append("Breakout")

    signal_type = _determine_signal_type(signals)

    # Fetch company name (best-effort)
    info = fetch_info(symbol)
    name = info.get("shortName") or info.get("longName") or symbol

    def _safe(value: float) -> float | None:
        return None if math.isnan(value) else round(value, 4)

    return {
        "symbol": symbol,
        "name": name,
        "price": round(price, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume": current_volume,
        "avg_volume": avg_volume,
        "volume_ratio": _safe(vol_ratio),
        "rsi": _safe(rsi_val),
        "sma20": _safe(sma20_val),
        "sma50": _safe(sma50_val),
        "ema9": _safe(ema9_val),
        "macd": _safe(macd_data["macd"]),
        "macd_signal": _safe(macd_data["signal"]),
        "macd_histogram": _safe(macd_data["histogram"]),
        "atr": _safe(atr_val),
        "signals": signals,
        "signal_type": signal_type,
    }


# ---------------------------------------------------------------------------
# Multi-symbol scanner
# ---------------------------------------------------------------------------

def scan_stocks(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    """Scan all *symbols* and return a list of result dicts.

    Failed or data-insufficient symbols are silently skipped.
    """
    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    results: list[dict[str, Any]] = []
    total = len(symbols)
    for i, symbol in enumerate(symbols, start=1):
        logger.info("[%d/%d] Scanning %s …", i, total, symbol)
        result = scan_symbol(symbol)
        if result is not None:
            results.append(result)

    # Sort: oversold first, then bullish, then neutral, then bearish, then overbought
    order = {"oversold": 0, "bullish": 1, "neutral": 2, "bearish": 3, "overbought": 4}
    results.sort(key=lambda r: order.get(r["signal_type"], 2))
    return results
