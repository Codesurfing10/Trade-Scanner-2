"""
Module for fetching stock data using yfinance.
"""

import pandas as pd
import yfinance as yf


def fetch_history(symbol, period='1y'):
    try:
        data = yf.download(symbol, period=period)
        result = data[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index(drop=True)
        return result
    except Exception:
        return pd.DataFrame()  # return empty DataFrame on failure


def fetch_info(symbol):
    try:
        info = yf.Ticker(symbol).info
        return {"shortName": info.get('shortName', None)}
    except Exception:
        return {}  # return empty dict on failure