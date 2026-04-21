"""
Module for fetching stock data using yfinance.
"""

import pandas as pd
import yfinance as yf

DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "META", "TSLA", "CRM", "ORCL", "QCOM", "JPM", "BAC",
    "GS", "V", "MA", "WMT", "TGT", "HD", "PG", "PEP", "KMB", "PFE",
    "DIS", "BA", "RGTI", "LIN", "APD", "SHW", "ECL", "GLD", "SLV", "PPLT",
    "XME", "COPX", "COST", "NKE", "MCD", "CL", "GIS", "KHC", "CLX", "PM",
    "ABBV", "HII", "DBA", "USO", "NFLX", "KO", "MDLZ", "MO", "JNJ", "MRK",
    "XOM", "CVX", "OXY", "T", "VZ", "LMT", "NOC", "RTX", "GD", "LHX",
    "UNG", "XLE", "NVDA", "AMD", "AMZN", "INTC", "TXN", "AVGO", "MS", "PYPL",
    "UNH", "IRDM", "IONQ", "QTUM", "FCX",
]


def fetch_history(symbol, period='1y'):
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            symbols = data.columns.get_level_values(-1)
            if symbol in symbols:
                data = data.xs(symbol, axis=1, level=-1, drop_level=True)
            else:
                data = data.droplevel(-1, axis=1)

        result = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        return result
    except Exception:
        return pd.DataFrame()  # return empty DataFrame on failure


def fetch_info(symbol):
    try:
        info = yf.Ticker(symbol).info
        return {"shortName": info.get('shortName', None)}
    except Exception:
        return {}  # return empty dict on failure
