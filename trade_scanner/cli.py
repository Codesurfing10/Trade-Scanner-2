from __future__ import annotations

import argparse
import json
from pathlib import Path

from .framework import scan_csv


def _render_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trade Scanner 2 — Alerts + Indicator + Hold</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background:#0f172a; color:#e2e8f0; }
    h1 { margin: 0 0 8px 0; }
    .muted { color:#94a3b8; margin-bottom:16px; }
    table { width:100%; border-collapse: collapse; margin-top: 16px; background:#111827; }
    th, td { border:1px solid #1f2937; padding:8px; text-align:left; font-size:14px; }
    th { background:#1f2937; }
    .yes { color:#22c55e; font-weight:700; }
    .no { color:#ef4444; font-weight:700; }
  </style>
</head>
<body>
  <h1>Momentum Trading Framework Scanner</h1>
  <div class="muted">Stage 2 + Volume Confirmation + Action Signal</div>
  <table id="signals">
    <thead>
      <tr>
        <th>Ticker</th><th>Date</th><th>Price</th><th>Stage 2</th><th>Vol Confirm</th><th>Action</th>
        <th>RVOL Alert</th><th>Conviction</th><th>Blocks</th><th>Hold Until</th><th>Hard Stop</th><th>Trim 1</th><th>Trim 2</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
  <script>
    const yesNo = (v) => `<span class="${v ? "yes" : "no"}">${v ? "YES" : "NO"}</span>`;
    fetch("./signals.json")
      .then(r => r.json())
      .then(rows => {
        const tbody = document.querySelector("#signals tbody");
        rows.forEach(row => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${row.ticker}</td>
            <td>${row.date}</td>
            <td>${row.price.toFixed(2)}</td>
            <td>${yesNo(row.stage_2)}</td>
            <td>${yesNo(row.volume_confirmation)}</td>
            <td>${yesNo(row.action_signal)}</td>
            <td>${yesNo(row.alerts.intraday_rvol)}</td>
            <td>${row.entry_plan.conviction}</td>
            <td>${row.entry_plan.blocks}</td>
            <td>${row.entry_plan.hold_until}</td>
            <td>${row.risk_management.hard_stop.toFixed(2)}</td>
            <td>${row.risk_management.trim_1_price.toFixed(2)}</td>
            <td>${row.risk_management.trim_2_price.toFixed(2)}</td>
          `;
          tbody.appendChild(tr);
        });
      });
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stock screener alerts and GitHub Pages outputs.")
    parser.add_argument("--input", default="data/sample_metrics.csv", help="Path to input CSV.")
    parser.add_argument("--output-json", default="docs/signals.json", help="Output JSON for generated signals.")
    parser.add_argument("--output-html", default="docs/index.html", help="Output HTML page.")
    args = parser.parse_args()

    results = scan_csv(args.input)

    output_json = Path(args.output_json)
    output_html = Path(args.output_html)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    output_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    output_html.write_text(_render_html(), encoding="utf-8")
    print(f"Generated {len(results)} records -> {output_json} and {output_html}")


if __name__ == "__main__":
    main()
