"""V10.3 chronological holdout using immutable local OHLCV snapshots.

No parameter tuning, no broker orders, no live portfolio/database writes.
The holdout is evaluated with 209 preceding bars for indicator warm-up.
"""
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics, fmt

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START, END = "2024-10-01", "2026-10-16"
CAPITAL = 2000.0
SPLIT_FRACTION = 0.65
WARMUP = 209


def evaluate(df):
    result = DailyTechnicalBacktester().run(
        df, initial_cash=CAPITAL, risk_per_trade_pct=1.0,
        commission_per_share=0.005, slippage_bps=5,
    )
    return result, metrics(result["trades"], CAPITAL)


def main():
    import csv

    rows = []
    for symbol in SYMBOLS:
        path = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        df = load_snapshot(path)
        split = int(len(df) * SPLIT_FRACTION)
        if split < 230 or len(df) - split < 1:
            raise ValueError(f"{symbol}: insufficient data for split")
        train = df.iloc[:split]
        # Last 209 training bars are used only to warm up indicators.
        # The engine's first possible entry is at index 209, the
        # first day of the holdout. No trade is carried across boundary.
        test = df.iloc[split - WARMUP:]
        train_result, train_m = evaluate(train)
        test_result, test_m = evaluate(test)
        cutoff = df.index[split]
        assert all(t["entry_date"] < str(cutoff.date()) for t in train_result["trades"])
        assert all(t["entry_date"] >= str(cutoff.date()) for t in test_result["trades"])
        for label, result, m, segment in (
            ("train", train_result, train_m, train),
            ("holdout", test_result, test_m, test),
        ):
            rows.append({
                "symbol": symbol, "segment": label,
                "cutoff": str(cutoff.date()),
                "segment_first": str(segment.index.min().date()),
                "segment_last": str(segment.index.max().date()),
                "closed_trades": m["trades"],
                "win_rate_pct": m["win_rate_pct"],
                "profit_factor": m["profit_factor"],
                "expectancy": m["expectancy"],
                "realized_pl": m["realized_pl"],
                "open_position": bool(result["open_position"]),
            })
        print(
            f"{symbol:5} cutoff={cutoff.date()} "
            f"TRAIN trades={train_m['trades']:2} P/L={fmt(train_m['realized_pl'], '$'):>9} PF={fmt(train_m['profit_factor']):>6} | "
            f"HOLDOUT trades={test_m['trades']:2} P/L={fmt(test_m['realized_pl'], '$'):>9} PF={fmt(test_m['profit_factor']):>6}"
        )
    out = Path("reports/backtest_holdout_comparison.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(SYMBOLS)}/{len(SYMBOLS)} symbols")
    print(f"CSV: {out.resolve()}")
    print("NOTE: chronological holdout, not a genuinely untouched dataset if these dates were already inspected.")
    print("NOTE: indicators warm up from prior 209 bars; no trades carried across split.")
    print("NOTE: no strategy optimization; closed trades only, open-position P/L excluded.")
    print("NOTE: split changes trade opportunities and resets independent segment capital to $2000.")


if __name__ == "__main__":
    main()
