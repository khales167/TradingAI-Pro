"""V10.9 slippage stress test using immutable daily stock snapshots.

Fixed strategy, fixed 1% risk, fixed 40% exposure, fixed $2,000
independent capital per symbol. Only slippage varies.
No network calls, broker actions, or live portfolio/database writes.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
SLIPPAGE_BPS = (5, 10, 20, 50)
START, END = "2024-10-01", "2026-10-16"
CAPITAL = 2000.0
COMMISSION = 0.005
OUT = Path("reports/backtest_slippage_stress.csv")


def display_pf(value):
    if value is None:
        return "N/A"
    if value == float("inf"):
        return "Infinity"
    return f"{value:.2f}"


def main():
    rows = []
    for symbol in SYMBOLS:
        snapshot = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        df = load_snapshot(snapshot)
        for bps in SLIPPAGE_BPS:
            result = DailyTechnicalBacktester().run(
                df,
                initial_cash=CAPITAL,
                risk_per_trade_pct=1.0,
                commission_per_share=COMMISSION,
                slippage_bps=bps,
            )
            d = result["diagnostics"]
            trades = result["trades"]
            m = metrics(trades, CAPITAL)
            budget = CAPITAL * 0.01
            breaches = sum(float(t["pl"]) < -budget - 1e-7 for t in trades)
            stop_gaps = sum(t["reason"] == "STOP_GAP" for t in trades)
            target_gaps = sum(t["reason"] == "TARGET_GAP" for t in trades)
            assert d["technical_signals"] == d["accepted_entries"] + d["rejected_by_risk"]
            assert len(trades) == result["closed_trades"]
            if result["open_position"] is None:
                assert abs(sum(float(t["pl"]) for t in trades) - (result["realized_cash"] - CAPITAL)) < 1e-7
            row = {
                "symbol": symbol,
                "slippage_bps_per_side": bps,
                "initial_capital": CAPITAL,
                "risk_pct": 1.0,
                "commission_per_share_per_side": COMMISSION,
                "signals": d["technical_signals"],
                "accepted_entries": d["accepted_entries"],
                "rejected_entries": d["rejected_by_risk"],
                "closed_trades": len(trades),
                "stop_gaps": stop_gaps,
                "target_gaps": target_gaps,
                "risk_budget_breaches": breaches,
                "profit_factor": m["profit_factor"],
                "expectancy_usd": m["expectancy"],
                "realized_pl_usd": m["realized_pl"],
                "return_pct": 100 * m["realized_pl"] / CAPITAL,
                "open_position": result["open_position"] is not None,
            }
            rows.append(row)
            print(
                f"{symbol:5} slip={bps:2}bps "
                f"signals={row['signals']:2} accepted={row['accepted_entries']:2} "
                f"closed={row['closed_trades']:2} gaps={stop_gaps + target_gaps:2} "
                f"breaches={breaches:2} PF={display_pf(m['profit_factor']):>8} "
                f"P/L=${m['realized_pl']:+.2f} "
                f"return={row['return_pct']:+.2f}%"
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS) * len(SLIPPAGE_BPS)} independent scenarios")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: higher slippage can change share sizing and entry acceptance; trades may differ between scenarios.")
    print("NOTE: these are independent per-stock accounts, not a pooled portfolio.")
    print("NOTE: closed-trade P/L excludes unrealized P/L; snapshots are historical, not untouched holdout data.")
    print("NOTE: read-only analysis; no live risk, strategy or broker changes.")


if __name__ == "__main__":
    main()
