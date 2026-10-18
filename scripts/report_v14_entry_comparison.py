"""V14.1 predeclared entry hypotheses, identical historical execution and risk.

Pullback: prior close <= prior MA19, latest completed close crosses above
MA19 within the existing uptrend. Breakout: latest completed close strictly
exceeds the preceding 20 completed session highs. Neither uses entry-day bars.
These are research hypotheses, NOT validated profitable strategies.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio, technical_signal
from scripts.prepare_v13_universe import NEW_SYMBOLS

CAPITAL = 1000.0
OUT = Path("reports/v14_entry_comparison.csv")


def pullback(frame, i):
    y = frame.iloc[i - 1]
    before = frame.iloc[i - 2]
    return bool(
        technical_signal(y)
        and before["Close"] <= before["MA19"]
        and y["Close"] > y["MA19"]
    )


def breakout(frame, i):
    y = frame.iloc[i - 1]
    # i-21 through i-2: the 20 sessions before signal day i-1.
    preceding_high = frame["High"].iloc[i - 21:i - 1].max()
    return bool(technical_signal(y) and y["Close"] > preceding_high)


def run_case(frames, name, signal_fn):
    result = run_portfolio(
        frames, capital=CAPITAL, risk_pct=1.0,
        max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
        max_positions=5, commission=0.005, slippage_bps=5.0,
        record_daily=True, entry_priority="alphabetical",
        signal_fn=signal_fn,
    )
    d = result["diagnostics"]
    trades = result["trades"]
    wins = [t["pl"] for t in trades if t["pl"] > 0]
    losses = [t["pl"] for t in trades if t["pl"] < 0]
    realized = sum(t["pl"] for t in trades)
    peak, drawdown = CAPITAL, 0.0
    for day in result["daily"]:
        peak = max(peak, day["equity"])
        drawdown = min(drawdown, 100 * (day["equity"] / peak - 1))
        assert day["cash"] >= -1e-8
        assert day["open_risk"] <= 30 + 1e-8
        assert day["entry_exposure"] <= 400 + 1e-8
        assert day["open_positions"] <= 5
    assert d["signals"] == d["accepted"] + sum(
        v for k, v in d.items() if k.startswith("rejected_")
    )
    assert d["accepted"] == len(trades) + len(result["positions"])
    assert abs(result["cash"] + sum(
        p["shares"] * (p["entry"] + 0.005) for p in result["positions"].values()
    ) - CAPITAL - realized) < 1e-6
    assert abs(result["daily"][-1]["equity"] - result["equity_marked"]) < 1e-6
    row = {
        "strategy": name, "signals": d["signals"],
        "accepted": d["accepted"], "closed": len(trades),
        "open": len(result["positions"]),
        "win_rate_pct": 100 * len(wins) / len(trades) if trades else 0,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else ("inf" if wins else 0),
        "expectancy_usd": realized / len(trades) if trades else 0,
        "realized_pl": realized,
        "marked_equity": result["equity_marked"],
        "max_drawdown_pct": drawdown,
    }
    print(f"{name:10} signals={d['signals']:3} accepted={d['accepted']:3} "
          f"closed={len(trades):3} open={len(result['positions'])} "
          f"win={row['win_rate_pct']:.1f}% PF={row['profit_factor']:.2f} "
          f"exp=${row['expectancy_usd']:+.2f} realized=${realized:+.2f} "
          f"equity=${result['equity_marked']:.2f} DD={drawdown:.2f}%")
    return row


def main():
    symbols = sorted(set(SYMBOLS) | set(NEW_SYMBOLS))
    frames = {s: prepared(s) for s in symbols}
    dates = frames[symbols[0]].index
    if any(not frames[s].index.equals(dates) for s in symbols):
        raise ValueError("Snapshot trading dates not aligned")
    print("V14.1 ENTRY COMPARISON | $1000 | 15 STOCKS | fixed exit/risk")
    rows = [
        run_case(frames, "BASELINE", None),
        run_case(frames, "PULLBACK", pullback),
        run_case(frames, "BREAKOUT", breakout),
    ]
    base = rows[0]
    assert base["accepted"] == 59 and base["closed"] == 57 and base["open"] == 2
    assert abs(base["realized_pl"] - 80.79) < 0.015
    assert abs(base["marked_equity"] - 1078.81) < 0.015
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("PASS 3/3 entry strategy accounting/risk checks and V13.4 baseline regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: pullback requires a one-day reclaim of MA19, not any touch of MA19.")
    print("NOTE: breakout requires close above previous 20-session high; no future bars.")
    print("NOTE: closed-trade metrics exclude open positions; marked equity includes them.")
    print("NOTE: hypotheses are tested on previously examined data; NOT out-of-sample.")
    print("NOTE: no live portfolio/database changes or broker orders.")


if __name__ == "__main__":
    main()
