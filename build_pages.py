"""
Build script: run the Trade Scanner and write output to docs/.

Usage:
    python build_pages.py [SYMBOL1 SYMBOL2 ...]

When no symbols are supplied the default universe is used.
The script writes:
  - docs/stocks.json  — machine-readable stock data consumed by the UI
"""
from __future__ import annotations

import json
import logging
import os
import sys
import math
from datetime import datetime, timezone

from scanner import scan_stocks
from scanner.data import DEFAULT_SYMBOLS, fetch_info, fetch_history

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


def _date_from_updated(updated: str) -> str | None:
    if not updated:
        return None
    return str(updated).split("T", 1)[0]


def _ensure_row_dates(payload: dict) -> None:
    fallback_date = _date_from_updated(str(payload.get("updated", "")))
    stocks = payload.get("stocks")
    if not isinstance(stocks, list):
        return
    for row in stocks:
        if not isinstance(row, dict):
            continue
        if row.get("date"):
            continue
        row["date"] = fallback_date


def _sanitize(obj):
    """Recursively replace NaN/Inf and non-JSON scalars with None or native Python types.

    This ensures json.dump emits valid JSON (no bare NaN/Infinity tokens).
    """
    # dict
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    # list/tuple
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    # numpy scalars or objects with .item()
    try:
        if hasattr(obj, "item") and not isinstance(obj, (str, bytes, bytearray)):
            return _sanitize(obj.item())
    except Exception:
        pass
    # numbers: guard against NaN/Inf
    try:
        if isinstance(obj, (int, bool)):
            return obj
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        # last-resort check: math.isnan will raise TypeError for non-numeric values
        if isinstance(obj, (str,)):
            return obj
        try:
            if math.isnan(obj):
                return None
        except Exception:
            pass
    except Exception:
        pass
    # everything else: keep as-is (json.dump will convert most primitives), but coerce to str for unknown types
    if obj is None:
        return None
    # final fallback: convert to native python scalar if possible
    try:
        return float(obj) if isinstance(obj, (int, float)) else str(obj)
    except Exception:
        return str(obj)


def main(symbols: list[str] | None = None) -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)

    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    print(f"Scanning {len(symbols)} symbols …")
    stocks = scan_stocks(symbols)
    print(f"Done — {len(stocks)} result(s) returned by scanner.")

    # Ensure every default symbol appears in the output (fallback placeholders)
    existing = {row.get("symbol") for row in stocks if isinstance(row, dict) and row.get("symbol")}
    added = 0
    for sym in DEFAULT_SYMBOLS:
        if sym in existing:
            continue
        try:
            info = fetch_info(sym)
        except Exception:
            info = {}
        name = info.get("shortName") or info.get("longName") or sym

        # Best-effort: try short history to populate price/date/change/volume
        price = None
        change = None
        change_pct = None
        row_date = None
        volume = None
        avg_volume = None
        try:
            hist = fetch_history(sym, period="5d")
            if hist is not None and not hist.empty and "Close" in hist.columns:
                closes = hist["Close"].dropna()
                if len(closes) >= 1:
                    last = float(closes.iloc[-1])
                    price = round(last, 2)
                    idx = hist.index[-1]
                    if hasattr(idx, "strftime"):
                        row_date = idx.strftime("%Y-%m-%d")
                    if len(closes) >= 2:
                        prev = float(closes.iloc[-2])
                        change = round(last - prev, 2)
                        change_pct = round((change / prev * 100) if prev != 0 else 0.0, 2)
            if hist is not None and not hist.empty and "Volume" in hist.columns:
                vols = hist["Volume"].dropna()
                if len(vols) >= 1:
                    volume = int(vols.iloc[-1])
                    try:
                        avg_volume = int(vols.mean())
                    except Exception:
                        avg_volume = None
        except Exception:
            # ignore history fetch errors and fall back to fetch_info
            pass

        # Fallback: try fetch_info for market price/previous close
        try:
            info2 = fetch_info(sym) or {}
            candidate = (
                info2.get("regularMarketPrice")
                or info2.get("currentPrice")
                or info2.get("previousClose")
            )
            if candidate is not None and price is None:
                p = float(candidate)
                price = round(p, 2)
                prev = info2.get("previousClose")
                if prev is not None:
                    prev = float(prev)
                    change = round(price - prev, 2)
                    change_pct = round((change / prev * 100) if prev != 0 else 0.0, 2)
            # prefer name from info2 if available
            name = info2.get("shortName") or info2.get("longName") or name
        except Exception:
            pass

        stocks.append({
            "symbol": sym,
            "name": name,
            "date": row_date,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "avg_volume": avg_volume,
            "insider_net": None,
            "insider_sentiment": "N/A",
            "volume_ratio": None,
            "rsi": None,
            "sma20": None,
            "sma50": None,
            "sma150": None,
            "slope_sma150": None,
            "ema9": None,
            "macd": None,
            "macd_signal": None,
            "macd_histogram": None,
            "atr": None,
            "volume_10week_ma": None,
            "stage_classification": "N/A",
            "confirms_stage2_volume": "N/A",
            "action_signal": "HOLD",
            "stage_analysis_summary": "HOLD",
            "position": "HOLD",
            "signals": [],
            "signal_type": "neutral",
        })
        added += 1

    if added:
        logging.info("Added %d placeholder stock(s) for missing DEFAULT_SYMBOLS.", added)

    out_path = os.path.join(DOCS_DIR, "stocks.json")

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(stocks),
        "stocks": stocks,
    }

    # Sanitize payload to ensure valid JSON (replace NaN/Infinity with null, coerce numpy types)
    safe_payload = _sanitize(payload)

    if not stocks and os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as fh:
                existing = json.load(fh)
            existing_stocks = existing.get("stocks")
            has_valid_stock_rows = (
                isinstance(existing_stocks, list)
                and existing_stocks
                and all(
                    isinstance(row, dict)
                    and isinstance(row.get("symbol"), str)
                    and bool(row.get("symbol").strip())
                    for row in existing_stocks
                )
            )
            if has_valid_stock_rows:
                logging.warning(
                    "No fresh stock data fetched; preserving existing docs/stocks.json with %d stock(s).",
                    len(existing_stocks),
                )
                safe_payload = existing
            else:
                logging.warning(
                    "No fresh stock data fetched, and existing docs/stocks.json has no valid non-empty 'stocks' list of stock objects.",
                )
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning(
                "No fresh stock data fetched, and existing docs/stocks.json could not be read as valid JSON: %s",
                exc,
            )

    with open(out_path, "w", encoding="utf-8") as fh:
        _ensure_row_dates(safe_payload)
        json.dump(safe_payload, fh, indent=2, ensure_ascii=False)

    print(f"Output written to {out_path}")


if __name__ == "__main__":
    cli_symbols = sys.argv[1:] or None
    main(cli_symbols)
