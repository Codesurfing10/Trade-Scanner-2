import unittest

from trade_scanner.framework import evaluate_record, scan_records


class TestFramework(unittest.TestCase):
    def test_action_signal_and_high_conviction(self) -> None:
        row = {
            "ticker": "TEST",
            "date": "2026-04-01",
            "price": "50",
            "sma50": "45",
            "sma150": "30",
            "sma150_4w_ago": "29",
            "high_52w": "55",
            "current_volume": "3000000",
            "avg_volume_20": "1500000",
            "volume_10w_ma": "1800000",
            "volume_10w_ma_prev": "1700000",
            "resistance": "49",
            "ma_10w": "48.8",
            "rs_rating": "85",
            "pct_change": "3.2",
            "rvol": "2.4",
            "market_condition": "strong",
            "sector_strength": "true",
            "prior_base": "true",
            "higher_highs_higher_lows": "true",
            "obv_new_high": "true",
            "up_day_volume_expanding": "true",
        }
        result = evaluate_record(row)
        self.assertTrue(result["stage_2"])
        self.assertTrue(result["volume_confirmation"])
        self.assertTrue(result["action_signal"])
        self.assertEqual(result["entry_plan"]["conviction"], "high")
        self.assertEqual(result["entry_plan"]["blocks"], 4)
        self.assertEqual(result["entry_plan"]["hold_days"], 7)

    def test_weak_market_hold_days(self) -> None:
        row = {
            "ticker": "TEST2",
            "date": "2026-04-01",
            "price": "30",
            "sma50": "20",
            "sma150": "15",
            "sma150_4w_ago": "14",
            "high_52w": "32",
            "current_volume": "2000000",
            "avg_volume_20": "1000000",
            "volume_10w_ma": "1200000",
            "volume_10w_ma_prev": "1100000",
            "resistance": "29",
            "ma_10w": "29.4",
            "rs_rating": "75",
            "pct_change": "2.1",
            "rvol": "2.0",
            "market_condition": "weak",
            "sector_strength": "false",
            "prior_base": "false",
            "higher_highs_higher_lows": "true",
            "obv_new_high": "false",
            "up_day_volume_expanding": "true",
        }
        result = evaluate_record(row)
        self.assertEqual(result["entry_plan"]["hold_days"], 3)

    def test_scan_sorting(self) -> None:
        a = {
            "ticker": "AAA",
            "date": "2026-04-01",
            "price": "10",
            "sma50": "9",
            "sma150": "8",
            "sma150_4w_ago": "7.8",
            "high_52w": "12",
            "current_volume": "300000",
            "avg_volume_20": "100000",
            "volume_10w_ma": "110000",
            "volume_10w_ma_prev": "100000",
            "resistance": "9.8",
            "ma_10w": "9.9",
            "rs_rating": "80",
            "pct_change": "1",
            "rvol": "1.2",
            "market_condition": "neutral",
            "sector_strength": "false",
            "prior_base": "false",
            "higher_highs_higher_lows": "true",
            "obv_new_high": "false",
            "up_day_volume_expanding": "true",
        }
        b = dict(a)
        b["ticker"] = "BBB"
        b["sma50"] = "7"
        results = scan_records([b, a])
        self.assertEqual(results[0]["ticker"], "AAA")


if __name__ == "__main__":
    unittest.main()
