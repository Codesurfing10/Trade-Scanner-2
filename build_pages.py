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
from datetime import datetime, timezone

from scanner import scan_stocks
from scanner.data import DEFAULT_SYMBOLS

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


def main(symbols: list[str] | None = None) -> None:
    os.makedirs(DOCS_DIR, exist_ok=True)

    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    print(f"Scanning {len(symbols)} symbols …")
    stocks = scan_stocks(symbols)
    print(f"Done — {len(stocks)} result(s) written.")

    out_path = os.path.join(DOCS_DIR, "stocks.json")

    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(stocks),
        "stocks": stocks,
    }

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
                payload = existing
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
        _ensure_row_dates(payload)
        json.dump(payload, fh, indent=2)

    print(f"Output written to {out_path}")


if __name__ == "__main__":
    cli_symbols = sys.argv[1:] or None
    main(cli_symbols)
