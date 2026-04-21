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
            if isinstance(existing_stocks, list) and existing_stocks:
                logging.warning(
                    "No fresh stock data fetched; preserving existing docs/stocks.json with %d stock(s).",
                    len(existing_stocks),
                )
                payload = existing
        except (OSError, json.JSONDecodeError):
            pass

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Output written to {out_path}")


if __name__ == "__main__":
    cli_symbols = sys.argv[1:] or None
    main(cli_symbols)
