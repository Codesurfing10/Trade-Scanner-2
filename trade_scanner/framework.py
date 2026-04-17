from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RiskConfig:
    hard_stop_pct: float = 0.08
    trim_1_pct: float = 0.20
    trim_2_pct: float = 0.30
    block_size_usd: int = 1000


def _to_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _to_bool(row: dict[str, str], key: str, default: bool = False) -> bool:
    value = str(row.get(key, str(default))).strip().lower()
    return value in {"1", "true", "yes", "y"}


def _hold_days(market_condition: str) -> int:
    condition = market_condition.strip().lower()
    if condition == "strong":
        return 7
    if condition == "neutral":
        return 5
    return 3


def evaluate_record(row: dict[str, str], risk: RiskConfig | None = None) -> dict[str, Any]:
    risk = risk or RiskConfig()
    ticker = row.get("ticker", "").strip().upper()
    as_of = row.get("date", "").strip()
    price = _to_float(row, "price")
    sma_50 = _to_float(row, "sma50")
    sma_150 = _to_float(row, "sma150")
    sma_150_4w_ago = _to_float(row, "sma150_4w_ago")
    high_52w = _to_float(row, "high_52w")
    current_volume = _to_float(row, "current_volume")
    avg_volume_20 = _to_float(row, "avg_volume_20")
    volume_10w_ma = _to_float(row, "volume_10w_ma")
    volume_10w_ma_prev = _to_float(row, "volume_10w_ma_prev")
    resistance = _to_float(row, "resistance")
    ma_10w = _to_float(row, "ma_10w")
    rs_rating = _to_float(row, "rs_rating")
    pct_change = _to_float(row, "pct_change")
    rvol = _to_float(row, "rvol")
    market_condition = row.get("market_condition", "weak")
    sector_strength = _to_bool(row, "sector_strength")
    prior_base = _to_bool(row, "prior_base")
    higher_highs_higher_lows = _to_bool(row, "higher_highs_higher_lows")
    obv_new_high = _to_bool(row, "obv_new_high")
    up_day_volume_expanding = _to_bool(row, "up_day_volume_expanding")

    stage_2 = all(
        [
            price > sma_150,
            sma_50 > sma_150,
            sma_150 > sma_150_4w_ago,
            higher_highs_higher_lows,
            price >= high_52w * 0.70 if high_52w > 0 else False,
        ]
    )

    volume_confirmation = all(
        [
            current_volume >= (avg_volume_20 * 1.5) if avg_volume_20 > 0 else False,
            up_day_volume_expanding,
            volume_10w_ma >= volume_10w_ma_prev if volume_10w_ma_prev > 0 else True,
        ]
    )

    breakout = price > resistance if resistance > 0 else False
    pullback = abs(price - ma_10w) / ma_10w <= 0.03 if ma_10w > 0 else False
    rs_ok = rs_rating > 70
    action_signal = stage_2 and volume_confirmation and (breakout or pullback) and rs_ok

    daily_eod_alert = action_signal
    intraday_rvol_alert = stage_2 and rvol >= 2.0 and pct_change >= 2.0
    premarket_candidate = (price >= high_52w * 0.98 if high_52w > 0 else False) and (
        current_volume >= avg_volume_20 * 1.5 if avg_volume_20 > 0 else False
    ) and (price > sma_150)

    if action_signal and rs_rating > 80 and sector_strength and prior_base:
        blocks = 4 if rvol >= 2 else 3
        conviction = "high"
    elif action_signal:
        blocks = 2
        conviction = "standard"
    elif stage_2 and volume_confirmation:
        blocks = 1
        conviction = "starter"
    else:
        blocks = 0
        conviction = "no_trade"

    deployed_capital = blocks * risk.block_size_usd
    risk_usd = deployed_capital * risk.hard_stop_pct

    hold_days = _hold_days(market_condition)
    hold_until = ""
    buy_window = ""
    try:
        buy_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        buy_window = f"{buy_date.isoformat()} to {(buy_date + timedelta(days=2)).isoformat()}"
        hold_until = (buy_date + timedelta(days=hold_days)).isoformat()
    except ValueError:
        pass

    hard_stop = price * (1 - risk.hard_stop_pct)
    trim_1 = price * (1 + risk.trim_1_pct)
    trim_2 = price * (1 + risk.trim_2_pct)
    trailing_stop = max(price * 0.90, sma_50 * 0.98 if sma_50 > 0 else 0)

    return {
        "ticker": ticker,
        "date": as_of,
        "price": round(price, 4),
        "stage_2": stage_2,
        "volume_confirmation": volume_confirmation,
        "breakout": breakout,
        "pullback": pullback,
        "obv_new_high_bonus": obv_new_high,
        "action_signal": action_signal,
        "alerts": {
            "daily_eod_scan": daily_eod_alert,
            "intraday_rvol": intraday_rvol_alert,
            "pre_market_shortlist": premarket_candidate,
        },
        "entry_plan": {
            "buy_window": buy_window,
            "hold_days": hold_days,
            "hold_until": hold_until,
            "conviction": conviction,
            "blocks": blocks,
            "capital_deployed_usd": deployed_capital,
            "max_risk_usd": round(risk_usd, 2),
        },
        "risk_management": {
            "hard_stop": round(hard_stop, 4),
            "trailing_stop": round(trailing_stop, 4),
            "trim_1_price": round(trim_1, 4),
            "trim_2_price": round(trim_2, 4),
        },
        "metrics": {
            "sma50": sma_50,
            "sma150": sma_150,
            "high_52w": high_52w,
            "rvol": rvol,
            "pct_change": pct_change,
            "rs_rating": rs_rating,
        },
    }


def scan_records(records: list[dict[str, str]], risk: RiskConfig | None = None) -> list[dict[str, Any]]:
    risk = risk or RiskConfig()
    evaluated = [evaluate_record(row, risk=risk) for row in records]
    return sorted(
        evaluated,
        key=lambda x: (
            int(x["action_signal"]),
            int(x["alerts"]["intraday_rvol"]),
            x["entry_plan"]["blocks"],
            x["ticker"],
        ),
        reverse=True,
    )


def scan_csv(path: str | Path, risk: RiskConfig | None = None) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        records = list(reader)
    return scan_records(records, risk=risk)
