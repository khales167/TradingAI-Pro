"""V11 execution consistency audit across fixed slippage scenarios.

Matches closed trades by (entry_date, exit_date, exit_reason), reports
changed trade paths, share counts, and per-share execution P/L.
Read-only verified snapshots; no strategy or live-account changes.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
BPS_LEVELS = (5, 10, 20, 50)
START, END = "2024-10-01", "2026-10-16"
CAPITAL = 2000.0
COMMISSION = 0.005
OUT = Path("reports/backtest_execution_consistency.csv")


def trade_key(trade):
    return (trade["entry_date"], trade["exit_date"], trade["reason"])


def net_per_share(trade):
    return float(trade["exit"]) - float(trade["entry"]) - 2 * COMMISSION


def run_case(df, bps):
    return DailyTechnicalBacktester().run(
        df, initial_cash=CAPITAL, risk_per_trade_pct=1.0,
        commission_per_share=COMMISSION, slippage_bps=bps,
    )


def main():
    rows = []
    for symbol in SYMBOLS:
        snapshot = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        df = load_snapshot(snapshot)
        base = run_case(df, 5)
        base_trades = base["trades"]
        base_by_key = {trade_key(t): t for t in base_trades}
        assert len(base_by_key) == len(base_trades), "Duplicate baseline trade keys"
        base_pl = sum(float(t["pl"]) for t in base_trades)

        for bps in BPS_LEVELS:
            result = run_case(df, bps)
            trades = result["trades"]
            current_by_key = {trade_key(t): t for t in trades}
            assert len(current_by_key) == len(trades), "Duplicate scenario trade keys"
            shared = sorted(base_by_key.keys() & current_by_key.keys())
            baseline_only = sorted(base_by_key.keys() - current_by_key.keys())
            scenario_only = sorted(current_by_key.keys() - base_by_key.keys())
            sizing_effect = 0.0
            per_share_execution_effect = 0.0
            for key in shared:
                a, b = base_by_key[key], current_by_key[key]
                a_shares, b_shares = int(a["shares"]), int(b["shares"])
                a_unit, b_unit = net_per_share(a), net_per_share(b)
                assert abs(float(a["pl"]) - a_shares * a_unit) < 1e-7
                assert abs(float(b["pl"]) - b_shares * b_unit) < 1e-7
                # Exact additive decomposition for matched trades:
                # P/L(b) - P/L(a) = (shares_b - shares_a)*unit_a
                #                    + shares_b*(unit_b - unit_a)
                sizing_effect += (b_shares - a_shares) * a_unit
                per_share_execution_effect += b_shares * (b_unit - a_unit)
            path_effect = (
                sum(float(current_by_key[k]["pl"]) for k in scenario_only)
                - sum(float(base_by_key[k]["pl"]) for k in baseline_only)
            )
            current_pl = sum(float(t["pl"]) for t in trades)
            delta = current_pl - base_pl
            assert abs(delta - (sizing_effect + per_share_execution_effect + path_effect)) < 1e-6
            changed_shares = sum(
                int(base_by_key[k]["shares"]) != int(current_by_key[k]["shares"])
                for k in shared
            )
            row = {
                "symbol": symbol,
                "baseline_bps": 5,
                "scenario_bps": bps,
                "baseline_closed": len(base_trades),
                "scenario_closed": len(trades),
                "matched_trades": len(shared),
                "baseline_only_trades": len(baseline_only),
                "scenario_only_trades": len(scenario_only),
                "matched_with_changed_shares": changed_shares,
                "baseline_pl_usd": base_pl,
                "scenario_pl_usd": current_pl,
                "delta_pl_usd": delta,
                "sizing_effect_usd": sizing_effect,
                "per_share_execution_effect_usd": per_share_execution_effect,
                "changed_trade_path_effect_usd": path_effect,
                "baseline_open_position": base["open_position"] is not None,
                "scenario_open_position": result["open_position"] is not None,
            }
            rows.append(row)
            print(
                f"{symbol:5} slip={bps:2}bps "
                f"matched={len(shared):2} removed={len(baseline_only):2} "
                f"added={len(scenario_only):2} resized={changed_shares:2} "
                f"delta=${delta:+.2f} sizing=${sizing_effect:+.2f} "
                f"execution=${per_share_execution_effect:+.2f} "
                f"path=${path_effect:+.2f}"
            )
            if bps != 5 and (baseline_only or scenario_only):
                for key in baseline_only[:3]:
                    print(f"  baseline_only {key[0]} -> {key[1]} {key[2]}")
                for key in scenario_only[:3]:
                    print(f"  scenario_only {key[0]} -> {key[1]} {key[2]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS) * len(BPS_LEVELS)} comparisons")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: execution effect includes changed per-share fill P/L on matched trades; not a pure fee-only estimate.")
    print("NOTE: changed-path effect compares unmatched closed trades; open positions excluded.")
    print("NOTE: independent $2,000 per stock; immutable snapshots; no live portfolio or broker changes.")


if __name__ == "__main__":
    main()
