"""
Module for fetching stock data using yfinance.
"""

import pandas as pd
import yfinance as yf

# Data center & infrastructure stocks
DATACENTER_SYMBOLS = [
    "DLR",   # Digital Realty Trust
    "EQIX",  # Equinix
    "CTRE",  # CyrusOne
    "QTS",   # QTS Realty Trust
    "CONE",  # CyrusOne (formerly)
    "PGRE",  # Paramount Group
    "CCI",   # Crown Castle International
    "SBAC",  # SBA Communications
    "AMT",   # American Tower
    "PLD",   # Prologis
    "AIR",   # AAR Corp (indirectly related)
    "REXR",  # Rexford Industrial Realty
]

DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "META", "TSLA", "CRM", "ORCL", "QCOM", "JPM", "BAC",
    "GS", "V", "MA", "WMT", "TGT", "HD", "PG", "PEP", "KMB", "PFE",
    "DIS", "BA", "RGTI", "LIN", "APD", "SHW", "ECL", "GLD", "SLV", "PPLT",
    "XME", "COPX", "COST", "NKE", "MCD", "CL", "GIS", "KHC", "CLX", "PM",
    "ABBV", "HII", "DBA", "USO", "NFLX", "KO", "MDLZ", "MO", "JNJ", "MRK",
    "XOM", "CVX", "OXY", "T", "VZ", "LMT", "NOC", "RTX", "GD", "LHX",
    "UNG", "XLE", "NVDA", "AMD", "AMZN", "INTC", "TXN", "AVGO", "MS", "PYPL",
    "UNH", "IRDM", "IONQ", "QTUM", "FCX",
] + DATACENTER_SYMBOLS


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


def fetch_insider_data(symbol):
    """
    Fetch insider trading data for a symbol.
    Returns a dict with insider_net_buying (positive) or insider_net_selling (negative).
    """
    try:
        ticker = yf.Ticker(symbol)
        # yfinance provides insider transactions via the info dict
        info = ticker.info
        
        # Try to get insider transaction data
        # Note: This is a best-effort approach; not all symbols have this data readily available
        net_insider = info.get('insiderTransactions', 0) or info.get('netInsiderBuys', 0)
        
        return {
            "insider_net_buying": net_insider if net_insider > 0 else 0,
            "insider_net_selling": abs(net_insider) if net_insider < 0 else 0,
            "insider_net": net_insider,  # Can be positive (buying) or negative (selling)
        }
    except Exception:
        return {
            "insider_net_buying": 0,
            "insider_net_selling": 0,
            "insider_net": 0,
        }
