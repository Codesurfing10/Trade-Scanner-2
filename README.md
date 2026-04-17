# Trade-Scanner-2

A Python-powered technical stock scanner with a static GitHub Pages UI.

## Features

- Scans a curated universe of large-cap US stocks
- Computes RSI, SMA (20/50), EMA (9), MACD, ATR, and volume ratio
- Classifies each stock as **Bullish**, **Bearish**, **Oversold**, **Overbought**, **Momentum**, **Breakout**, or **High Volume**
- Outputs a static `docs/stocks.json` consumed by a dark-themed responsive web UI
- Deployable to GitHub Pages with a single command

## Setup

```bash
pip install -r requirements.txt
```

## Generate / refresh stock data

```bash
python build_pages.py
```

This fetches the latest data for all default symbols and writes `docs/stocks.json`.
Commit the updated file to publish fresh data to GitHub Pages.

You can also scan specific symbols:

```bash
python build_pages.py AAPL MSFT TSLA NVDA
```

## GitHub Pages setup

1. Push to GitHub.
2. Go to **Settings → Pages** and set the source to the `docs/` folder on your default branch.
3. Run `python build_pages.py`, commit `docs/stocks.json`, and push to update the live site.

## Running tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```
├── build_pages.py      # CLI: fetch data → docs/stocks.json
├── requirements.txt
├── scanner/
│   ├── __init__.py
│   ├── data.py         # symbol list + yfinance fetching
│   ├── indicators.py   # RSI, SMA, EMA, MACD, ATR, volume ratio
│   └── scanner.py      # scan logic + signal classification
├── docs/
│   ├── index.html      # static UI (loads stocks.json via fetch)
│   └── stocks.json     # generated — commit after running build_pages.py
└── tests/
    ├── test_indicators.py
    └── test_scanner.py
```