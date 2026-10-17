"""V10.2 independent multi-stock performance comparison.

Uses immutable local snapshots; downloads a fixed window only if a snapshot
does not yet exist. No live orders, portfolio writes, or strategy changes.
"""
from pathlib import Path

from core.backtest_snapshot import create_snapshot, load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics, fmt

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START = "2024-10-01"
END = "2026-10-16"  # exclusive
CAPITAL = 2000.0
SNAPSHOT_DIR = Path("data/backtest_snapshots")
REPORT = Path("reports/backtest_multistock_performance.csv")


def main():
    import csv

    rows = []
    for symbol in SYMBOLS:
        path = SNAPSHOT_DIR / f"{symbol}_{START}_{END}.csv"
        if not path.exists():
            print(f"{symbol}: creating fixed-window snapshot (first run only)")
            path = create_snapshot(symbol, START, END)
        df = load_snapshot(path)
        result = DailyTechnicalBacktester().run(
            df,
            initial_cash=CAPITAL,
            risk_per_trade_pct=1.0,
            commission_per_share=0.005,
            slippage_bps=5,
        )
        m = metrics(result["trades"], CAPITAL)
        if abs(m["realized_pl"] - (result["realized_cash"] - CAPITAL)) > 1e-7:
            raise AssertionError(f"{symbol}: ledger reconciliation failed")
        row = {
            "symbol": symbol,
            "first_date": str(df.index.min().date()),
            "last_date": str(df.index.max().date()),
            "bars": len(df),
            "signals": result["diagnostics"]["technical_signals"],
            "accepted": result["diagnostics"]["accepted_entries"],
            "rejected": result["diagnostics"]["rejected_by_risk"],
            **m,
            "open_position": bool(result["open_position"]),
        }
        rows.append(row)
        print(
            f"{symbol:5} trades={m['trades']:2} wins={m['wins']:2} "
            f"win_rate={fmt(m['win_rate_pct'], '%'):>7} "
            f"PF={fmt(m['profit_factor']):>7} "
            f"expectancy={fmt(m['expectancy'], '$'):>9} "
            f"realized_P/L={fmt(m['realized_pl'], '$'):>10}"
        )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS)} independent stock scenarios")
    print(f"CSV: {REPORT.resolve()}")
    print("NOTE: closed-trade drawdown excludes intratrade mark-to-market drawdown.")
    print("NOTE: each ticker uses its own $2000; these are NOT a combined portfolio.")
    print("NOTE: no out-of-sample evidence yet; snapshots use dividend-adjusted OHLC.")


if __name__ == "__main__":
    main()
