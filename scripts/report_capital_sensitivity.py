"""V10.6 capital sensitivity using verified fixed-window snapshots.

Each stock/capital scenario is independent; no parameter tuning or live writes.
Risk stays 1% and exposure stays 40%; only initial cash changes.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics, fmt

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
CAPITALS = (500.0, 1000.0, 2000.0, 3000.0, 5000.0)
START, END = "2024-10-01", "2026-10-16"
OUT = Path("reports/backtest_capital_sensitivity.csv")


def main():
    rows = []
    for symbol in SYMBOLS:
        df = load_snapshot(Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv"))
        for capital in CAPITALS:
            result = DailyTechnicalBacktester().run(
                df, initial_cash=capital, risk_per_trade_pct=1.0,
                commission_per_share=0.005, slippage_bps=5,
            )
            d = result["diagnostics"]
            m = metrics(result["trades"], capital)
            assert d["technical_signals"] == d["accepted_entries"] + d["rejected_by_risk"]
            row = {
                "symbol": symbol,
                "initial_capital": capital,
                "risk_pct": 1.0,
                "risk_budget": capital * 0.01,
                "exposure_limit": capital * 0.40,
                "technical_signals": d["technical_signals"],
                "accepted_entries": d["accepted_entries"],
                "rejected_entries": d["rejected_by_risk"],
                "rejected_trade_risk": d["rejection_reasons"]["trade_risk"],
                "rejected_exposure": d["rejection_reasons"]["exposure"],
                "rejected_cash": d["rejection_reasons"]["cash"],
                "rejected_zero_size": d["rejection_reasons"]["position_size_zero"],
                "closed_trades": m["trades"],
                "win_rate_pct": m["win_rate_pct"],
                "profit_factor": m["profit_factor"],
                "expectancy": m["expectancy"],
                "realized_pl": m["realized_pl"],
                "return_on_initial_capital_pct": m["realized_pl"] / capital * 100,
                "open_position": bool(result["open_position"]),
            }
            rows.append(row)
            print(
                f"{symbol:5} capital=${capital:,.0f} "
                f"signals={d['technical_signals']:3} "
                f"accepted={d['accepted_entries']:3} "
                f"rejected={d['rejected_by_risk']:3} "
                f"closed={m['trades']:2} "
                f"PF={fmt(m['profit_factor']):>6} "
                f"P/L={fmt(m['realized_pl'], '$'):>10} "
                f"return={row['return_on_initial_capital_pct']:+.2f}%"
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS) * len(CAPITALS)} independent scenarios")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: independent initial capital per ticker/scenario, NOT pooled portfolio performance.")
    print("NOTE: signal counts can change as open positions suppress later signal evaluations.")
    print("NOTE: only closed-trade P/L included; no unrealized P/L or mark-to-market drawdown.")
    print("NOTE: fixed historical snapshots; this is sensitivity analysis, not out-of-sample proof.")


if __name__ == "__main__":
    main()
