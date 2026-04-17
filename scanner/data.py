"""
Curated list of stock symbols and yfinance-based data fetching.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Default universe: large-cap US stocks across major sectors
DEFAULT_SYMBOLS: list[str] = [
    # Technology
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "TSLA", "AMZN",
    "NFLX", "CRM", "ORCL", "INTC", "QCOM", "TXN", "AVGO",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL",
    # Consumer
    "WMT", "COST", "TGT", "HD", "NKE", "MCD",
    # Healthcare
    "JNJ", "PFE", "ABBV", "MRK", "UNH",
    # Energy
    "XOM", "CVX", "OXY",
    # Communication / Media
    "DIS", "T", "VZ",
]


def fetch_history(symbol: str, period: str = "3mo") -> pd.DataFrame:
    """Return OHLCV DataFrame for *symbol* over *period*.

    Returns an empty DataFrame on any error.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            logger.warning("No data returned for %s", symbol)
        return df
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch %s: %s", symbol, exc)
        return pd.DataFrame()


def fetch_info(symbol: str) -> dict[str, Any]:
    """Return a dict of fundamental info for *symbol*.

    Falls back to an empty dict on error.
    """
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info or {}
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch info for %s: %s", symbol, exc)
        return {}
