# Trade Scanner

**Client-side CSV & Excel trade blotter / OHLCV scanner.**  
Drop a file → get buy/sell/short/cover signals, notional totals, and technical alerts.  
No server. No API keys. Files never leave the browser.

## Features

- **Upload** `.csv`, `.xlsx`, `.xls`, or `.xlsm`
- **Auto-detect columns** (Date, Symbol, Side, Qty, Price, OHLCV, Notes, …)
- **Blotter mode** — explicit BUY / SELL / SHORT / COVER / HOLD / WATCH
- **OHLCV mode** — RSI, 3-bar momentum, volume spikes
- **Multi-sheet Excel** — pick which sheet to scan
- **Fully static** — works on GitHub Pages, Netlify, S3, or `file://`

## Quick start (GitHub Pages)

1. Push this folder to a repo (or the `docs/` / root of an existing repo).
2. Enable **Settings → Pages → Deploy from branch**.
3. Open the published URL.

Or open `index.html` locally in any modern browser.

## Sample files

| File | Description |
|------|-------------|
| `samples/blotter.csv` | Explicit side blotter |
| `samples/ohlcv.csv` | SPY daily OHLCV (technical signals) |
| `samples/trades.xlsx` | Excel workbook with both sheets |

## How it works

1. **CSV** → native parser in `scanner.js`
2. **Excel** → [SheetJS](https://sheetjs.com) (CDN) converts the selected sheet to a 2-D array, then the same scan logic runs
3. Column aliases are fuzzy-matched (e.g. `Ticker` → Symbol, `FillPrice` → Price)
4. Side text is normalized with regex patterns

## API (for embedding)

```js
// CSV text
const result = TradeScanner.scanCsv(csvText, "myfile.csv");

// 2-D array (e.g. from SheetJS)
const result = TradeScanner.scanArray(arrayOfArrays, "myfile.xlsx");

// result.summary  → buys, sells, netNotional, mode, …
// result.signals  → array of { side, symbol, reason, strength, … }
// result.rows     → normalized rows with detected side
```

## Browser support

Chrome, Firefox, Safari, Edge (modern). Requires `FileReader` + ES6.
