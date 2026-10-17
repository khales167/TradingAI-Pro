"""V9 fixed-window backtest data reproducibility smoke test.

Fixed dates prevent a rolling 2y window from shifting between runs.
They do not freeze Yahoo revisions or corporate-action adjustments.
"""
from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester

SYMBOL = "NVDA"
START = "2024-10-01"
END = "2026-10-16"  # exclusive
CAPITAL = 2000.0


def main():
    first = load_backtest_data(SYMBOL, start=START, end=END)
    second = load_backtest_data(SYMBOL, start=START, end=END)
    if not first.equals(second):
        raise AssertionError("Two downloads returned different adjusted OHLCV data")
    if not (str(first.index.min().date()) >= START and str(first.index.max().date()) < END):
        raise AssertionError("Downloaded dates are outside the requested range")
    engine = DailyTechnicalBacktester()
    kwargs = dict(initial_cash=CAPITAL, commission_per_share=0.005, slippage_bps=5)
    a = engine.run(first, **kwargs)
    b = engine.run(second, **kwargs)
    if a["trades"] != b["trades"] or a["realized_cash"] != b["realized_cash"]:
        raise AssertionError("Identical OHLCV produced different backtest results")
    print(f"PASS: fixed date window {START} to {END} (end exclusive)")
    print(f"PASS: {len(first)} daily rows; {first.index.min().date()} to {first.index.max().date()}")
    print("PASS: two downloads and backtest outputs match")
    print(f"Closed trades: {a['closed_trades']}; realized P/L: ${a['realized_cash'] - CAPITAL:+.2f}")
    for args in (
        {"start": START},
        {"start": END, "end": START},
        {"start": "bad-date", "end": END},
    ):
        try:
            load_backtest_data(SYMBOL, **args)
        except ValueError:
            continue
        raise AssertionError(f"Invalid date arguments accepted: {args}")
    print("PASS: invalid date arguments rejected")
    print("Caveat: repeat downloads can differ if upstream adjusted history is revised.")


if __name__ == "__main__":
    main()
