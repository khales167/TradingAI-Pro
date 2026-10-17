"""V10.5 technical signal and risk rejection diagnostics.

Reads verified immutable snapshots only. Does not change strategy, risk
limits, orders, database, or live portfolio.
"""
import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START, END = "2024-10-01", "2026-10-16"
OUT = Path("reports/backtest_signal_diagnostics.csv")


def main():
    rows = []
    for symbol in SYMBOLS:
        path = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        result = DailyTechnicalBacktester().run(
            load_snapshot(path), initial_cash=2000.0,
            risk_per_trade_pct=1.0, commission_per_share=0.005,
            slippage_bps=5,
        )
        d = result["diagnostics"]
        reasons = d["rejection_reasons"]
        row = {
            "symbol": symbol,
            "evaluated_bars": d["evaluated_bars"],
            "technical_signals": d["technical_signals"],
            "accepted_entries": d["accepted_entries"],
            "rejected_by_risk": d["rejected_by_risk"],
            "trade_risk": reasons["trade_risk"],
            "exposure": reasons["exposure"],
            "cash": reasons["cash"],
            "position_size_zero": reasons["position_size_zero"],
            "closed_trades": result["closed_trades"],
            "open_position": bool(result["open_position"]),
        }
        assert row["technical_signals"] == row["accepted_entries"] + row["rejected_by_risk"]
        rows.append(row)
        print(
            f"{symbol:5} signals={row['technical_signals']:3} "
            f"accepted={row['accepted_entries']:3} rejected={row['rejected_by_risk']:3} "
            f"risk={row['trade_risk']:3} exposure={row['exposure']:3} "
            f"cash={row['cash']:3} zero={row['position_size_zero']:3} "
            f"closed={row['closed_trades']:2} open={row['open_position']}"
        )
        for sample in d["sample_rejections"]:
            print(f"  sample {sample['date']} entry=${sample['entry']:.2f} "
                  f"risk/share=${sample['risk_per_share']:.2f} "
                  f"reasons={','.join(sample['reasons'])}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS)} symbols")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: rejection reasons can overlap; do not add them to obtain rejected count.")
    print("NOTE: evaluated bars exclude bars while a position is open.")
    print("NOTE: immutable snapshots; no live portfolio or risk rule modifications.")


if __name__ == "__main__":
    main()
