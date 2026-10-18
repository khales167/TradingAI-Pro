"""V14.2 historical SPY 200-day market-regime gate, long entries only.

Predeclared rule: allow an entry at day t open only if SPY's completed
day t-1 close is strictly above its 200-day simple moving average.
Compare baseline and 20-day breakout, each with and without the gate.
Unchanged portfolio risk, exit, costs, and priority; historical only.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ta.trend import SMAIndicator
from core.backtest_snapshot import create_snapshot, load_snapshot
from scripts.report_shared_portfolio import SYMBOLS, START, END, prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS
from scripts.report_v14_entry_comparison import breakout

CAPITAL = 1000.0
SNAPSHOT_DIR = Path("data/backtest_snapshots")
SPY_PATH = SNAPSHOT_DIR / f"SPY_{START}_{END}.csv"
OUT = Path("reports/v14_market_regime.csv")


def load_spy():
    meta = SPY_PATH.with_suffix(".json")
    if SPY_PATH.exists() != meta.exists():
        raise RuntimeError("SPY snapshot pair incomplete; inspect before rerunning")
    if not SPY_PATH.exists():
        create_snapshot("SPY", START, END, directory=str(SNAPSHOT_DIR))
        print("SPY immutable snapshot CREATED")
    else:
        print("SPY immutable snapshot VERIFIED")
    spy = load_snapshot(SPY_PATH)
    spy["SMA200"] = SMAIndicator(spy["Close"], window=200).sma_indicator()
    return spy


def evaluate(frames, spy, label, signal_fn, use_regime):
    # All inputs are from completed bars: i-1 is the signal day.
    def gated(frame, i):
        signal = True if signal_fn is None else signal_fn(frame, i)
        if not signal:
            return False
        if not use_regime:
            from scripts.report_shared_portfolio import technical_signal
            return technical_signal(frame.iloc[i - 1]) if signal_fn is None else True
        yesterday = spy.iloc[i - 1]
        if not (yesterday["Close"] > yesterday["SMA200"]):
            return False
        if signal_fn is None:
            from scripts.report_shared_portfolio import technical_signal
            return technical_signal(frame.iloc[i - 1])
        return True

    result = run_portfolio(
        frames, capital=CAPITAL, risk_pct=1.0,
        max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
        max_positions=5, commission=0.005, slippage_bps=5.0,
        record_daily=True, entry_priority="alphabetical",
        signal_fn=gated if use_regime else signal_fn,
    )
    d = result["diagnostics"]
    trades = result["trades"]
    pl = sum(t["pl"] for t in trades)
    wins = [t["pl"] for t in trades if t["pl"] > 0]
    losses = [t["pl"] for t in trades if t["pl"] < 0]
    peak, dd = CAPITAL, 0.0
    for day in result["daily"]:
        peak = max(peak, day["equity"])
        dd = min(dd, 100 * (day["equity"] / peak - 1))
        assert day["cash"] >= -1e-8
        assert day["open_risk"] <= 30 + 1e-8
        assert day["entry_exposure"] <= 400 + 1e-8
        assert day["open_positions"] <= 5
    assert d["signals"] == d["accepted"] + sum(
        value for key, value in d.items() if key.startswith("rejected_")
    )
    assert d["accepted"] == len(trades) + len(result["positions"])
    assert abs(result["cash"] + sum(
        p["shares"] * (p["entry"] + 0.005) for p in result["positions"].values()
    ) - CAPITAL - pl) < 1e-6
    assert abs(result["daily"][-1]["equity"] - result["equity_marked"]) < 1e-6
    row = {
        "scenario": label, "signals": d["signals"],
        "accepted": d["accepted"], "closed": len(trades),
        "open": len(result["positions"]),
        "win_rate_pct": 100 * len(wins) / len(trades) if trades else 0,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else ("inf" if wins else 0),
        "expectancy_usd": pl / len(trades) if trades else 0,
        "realized_pl": pl, "marked_equity": result["equity_marked"],
        "max_drawdown_pct": dd,
    }
    print(f"{label:20} signals={d['signals']:3} accepted={d['accepted']:3} "
          f"closed={len(trades):3} open={len(result['positions'])} "
          f"win={row['win_rate_pct']:.1f}% PF={row['profit_factor']:.2f} "
          f"exp=${row['expectancy_usd']:+.2f} realized=${pl:+.2f} "
          f"equity=${result['equity_marked']:.2f} DD={dd:.2f}%")
    return row


def main():
    print("V14.2 MARKET REGIME | SPY CLOSE > SMA200 | $1000 | 15 STOCKS")
    spy = load_spy()
    symbols = sorted(set(SYMBOLS) | set(NEW_SYMBOLS))
    frames = {symbol: prepared(symbol) for symbol in symbols}
    dates = frames[symbols[0]].index
    if not spy.index.equals(dates):
        raise ValueError("SPY snapshot dates differ from stock snapshots; no silent forward-fill")
    if any(not frames[symbol].index.equals(dates) for symbol in symbols):
        raise ValueError("Stock snapshot dates not aligned")
    assert spy["SMA200"].iloc[208:].notna().all()
    rows = [
        evaluate(frames, spy, "BASELINE", None, False),
        evaluate(frames, spy, "BASELINE_SPY200", None, True),
        evaluate(frames, spy, "BREAKOUT", breakout, False),
        evaluate(frames, spy, "BREAKOUT_SPY200", breakout, True),
    ]
    assert rows[0]["accepted"] == 59 and rows[0]["closed"] == 57 and rows[0]["open"] == 2
    assert abs(rows[0]["realized_pl"] - 80.79) < 0.015
    assert rows[2]["accepted"] == 38 and rows[2]["closed"] == 36 and rows[2]["open"] == 2
    assert abs(rows[2]["realized_pl"] - 89.90) < 0.015
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("PASS 4/4 market-regime scenarios, risk/accounting and prior baseline regressions")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: SPY signal uses prior completed close and SMA200, never today's close.")
    print("NOTE: regime blocks NEW long entries only; existing exits remain unchanged.")
    print("NOTE: fixed historical snapshots, reused in-sample period; not out-of-sample.")
    print("NOTE: no live state, broker orders, or database writes.")


if __name__ == "__main__":
    main()
