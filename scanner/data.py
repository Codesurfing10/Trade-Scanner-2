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


def fetch_insider_net(symbol):
    """Best-effort: attempt to compute net insider buying (shares bought - shares sold)

    Yahoo/ yfinance does not provide a consistent insider-transactions structure for all
    tickers. This function tries a few common keys in the Ticker.info payload and
    will return an integer (positive => net buying, negative => net selling) when
    it can compute one, or ``None`` when the data isn't available or couldn't be
    parsed.
    """
    try:
        t = yf.Ticker(symbol)
        # yfinance exposes info as .info; some versions also provide get_info()
        info = getattr(t, "info", {}) or (getattr(t, "get_info", lambda: {})() )

        # Common keys to look for (best-effort): 'insiderTransactions', 'insider_transactions'
        transactions = info.get("insiderTransactions") or info.get("insider_transactions")

        if isinstance(transactions, list) and transactions:
            net = 0
            for tx in transactions:
                # tx might be a dict-like object
                typ = str(tx.get("transactionType") or tx.get("type") or tx.get("transaction") or "").lower()
                # try several possible fields for shares
                shares = tx.get("shares") if isinstance(tx.get("shares"), (int, float)) else None
                if shares is None:
                    shares = tx.get("shareCount") if isinstance(tx.get("shareCount"), (int, float)) else None
                if shares is None:
                    # Sometimes data uses string amounts
                    raw = tx.get("shares") or tx.get("shareCount") or tx.get("transactionShares") or tx.get("amount")
                    try:
                        if isinstance(raw, str):
                            raw = raw.replace(",", "")
                        shares = int(float(raw))
                    except Exception:
                        shares = None

                if shares is None:
                    # skip this transaction if we can't determine share count
                    continue

                if "sell" in typ:
                    net -= int(shares)
                elif "buy" in typ:
                    net += int(shares)
                else:
                    # If type not explicit, try to infer from 'transaction' field values
                    txn = str(tx.get("transaction") or "").lower()
                    if "sell" in txn:
                        net -= int(shares)
                    elif "buy" in txn:
                        net += int(shares)

            return int(net)

        # Fallbacks: some tickers expose a single aggregate like 'heldPercentInsiders'
        # which is a percentage and can't be converted to net shares here — return None
        return None
    except Exception:
        return None
