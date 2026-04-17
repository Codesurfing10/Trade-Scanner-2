# Trade-Scanner-2

Python stock screener + trade alert generator implementing the **Alert + Indicator + Hold** momentum framework:

- Stage 2 trend filter
- Volume confirmation
- Breakout / pullback action signal
- Entry, hold-window, trim, trailing stop, and hard-stop levels
- $1,000 block deployment model

## Input model

Provide a CSV with one row per ticker snapshot using this schema:

`ticker,date,price,sma50,sma150,sma150_4w_ago,high_52w,current_volume,avg_volume_20,volume_10w_ma,volume_10w_ma_prev,resistance,ma_10w,rs_rating,pct_change,rvol,market_condition,sector_strength,prior_base,higher_highs_higher_lows,obv_new_high,up_day_volume_expanding`

A sample file is included at:

- `data/sample_metrics.csv`

## Build outputs for GitHub Pages

Run:

```bash
cd <repo-root>
python build_pages.py
```

This generates:

- `docs/index.html`
- `docs/signals.json`

To publish on GitHub Pages, configure Pages to serve from the repository branch `/docs` folder.

## Tests

```bash
cd <repo-root>
python -m unittest discover -s tests -v
```
