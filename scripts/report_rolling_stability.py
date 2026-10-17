"""V10.4 chronological rolling-window stability report from saved snapshots.

This is a fixed-rule rolling evaluation, NOT parameter-refitting walk-forward
optimization. Each window resets cash and positions; indicators get 209 prior
bars. No data downloads, live portfolio writes, or broker interactions.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics, fmt

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START = "2024-10-01"
END = "2026-10-16"
WARMUP_BARS = 209
WINDOW_BARS = 75
CAPITAL = 2000.0
OUT = Path("reports/backtest_rolling_windows.csv")


def main():
    rows = []
    for symbol in SYMBOLS:
        snapshot = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        df = load_snapshot(snapshot)
        if len(df) < WARMUP_BARS + WINDOW_BARS:
            raise ValueError(f"{symbol}: insufficient snapshot history")
        window_no = 0
        starts = list(range(WARMUP_BARS, len(df), WINDOW_BARS))
        # The engine requires 230 rows: 209 warm-up + 21 evaluation.
        # Merge a shorter trailing window into the preceding window.
        if len(starts) > 1 and len(df) - starts[-1] < 21:
            starts.pop()
        for index, start_idx in enumerate(starts):
            end_idx = len(df) if index == len(starts) - 1 else min(start_idx + WINDOW_BARS, len(df))
            # The engine's first eligible entry is at offset 209, i.e.
            # exactly the first date of the evaluation window.
            window = df.iloc[start_idx - WARMUP_BARS:end_idx]
            result = DailyTechnicalBacktester().run(
                window,
                initial_cash=CAPITAL,
                risk_per_trade_pct=1.0,
                commission_per_share=0.005,
                slippage_bps=5,
            )
            stats = metrics(result["trades"], CAPITAL)
            eval_start = str(df.index[start_idx].date())
            eval_end = str(df.index[end_idx - 1].date())
            assert all(eval_start <= t["entry_date"] <= eval_end for t in result["trades"])
            assert all(eval_start <= t["exit_date"] <= eval_end for t in result["trades"])
            assert abs(stats["realized_pl"] - (result["realized_cash"] - CAPITAL)) < 1e-7
            window_no += 1
            rows.append({
                "symbol": symbol,
                "window": window_no,
                "start": eval_start,
                "end": eval_end,
                "evaluation_bars": end_idx - start_idx,
                "technical_signals": result["diagnostics"]["technical_signals"],
                "accepted_entries": result["diagnostics"]["accepted_entries"],
                "rejected_entries": result["diagnostics"]["rejected_by_risk"],
                "closed_trades": stats["trades"],
                "win_rate_pct": stats["win_rate_pct"],
                "profit_factor": stats["profit_factor"],
                "expectancy": stats["expectancy"],
                "realized_pl": stats["realized_pl"],
                "open_position_at_boundary": bool(result["open_position"]),
            })
            print(
                f"{symbol:5} W{window_no} {eval_start}..{eval_end} "
                f"trades={stats['trades']:2} "
                f"PF={fmt(stats['profit_factor']):>6} "
                f"expectancy={fmt(stats['expectancy'], '$'):>9} "
                f"P/L={fmt(stats['realized_pl'], '$'):>9} "
                f"open_at_end={bool(result['open_position'])}"
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)} independent symbol-windows")
    print(f"CSV: {OUT.resolve()}")
    print("CAUTION: This is rolling-window stability, not walk-forward retraining or untouched out-of-sample validation.")
    print("CAUTION: Window resets can omit open trades and differ from continuous portfolio P/L.")
    print("CAUTION: PF/expectancy are unreliable in windows with very few closed trades.")


if __name__ == "__main__":
    main()
