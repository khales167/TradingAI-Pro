"""V14.3 historical Breakout 20d exit comparison: fixed stop vs +1R break-even.

Break-even arms only for the next session after a surviving candle reaches +1R.
Same-day activation is intentionally excluded due to daily OHLC path ambiguity.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS
from scripts.report_v14_entry_comparison import breakout

CAPITAL = 1000.0
OUT = Path("reports/v14_break_even_comparison.csv")


def evaluate(frames, label, break_even_r):
    result = run_portfolio(
        frames, capital=CAPITAL, risk_pct=1.0,
        max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
        max_positions=5, commission=0.005, slippage_bps=5.0,
        record_daily=True, entry_priority="alphabetical",
        signal_fn=breakout, break_even_r=break_even_r,
    )
    d, trades = result["diagnostics"], result["trades"]
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
    armed_exits = sum(bool(t.get("break_even_armed")) for t in trades)
    row = {
        "scenario": label, "signals": d["signals"], "accepted": d["accepted"],
        "closed": len(trades), "open": len(result["positions"]),
        "armed_closed": armed_exits,
        "win_rate_pct": 100 * len(wins) / len(trades) if trades else 0,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else ("inf" if wins else 0),
        "expectancy_usd": pl / len(trades) if trades else 0,
        "realized_pl": pl, "marked_equity": result["equity_marked"],
        "max_drawdown_pct": dd,
    }
    print(f"{label:15} accepted={d['accepted']:3} closed={len(trades):3} "
          f"open={len(result['positions'])} armed_exits={armed_exits:2} "
          f"win={row['win_rate_pct']:.1f}% PF={row['profit_factor']:.2f} "
          f"exp=${row['expectancy_usd']:+.2f} realized=${pl:+.2f} "
          f"equity=${result['equity_marked']:.2f} DD={dd:.2f}%")
    return row


def main():
    print("V14.3 BREAK-EVEN +1R | $1000 | BREAKOUT 20D | 15 STOCKS")
    symbols = sorted(set(SYMBOLS) | set(NEW_SYMBOLS))
    frames = {s: prepared(s) for s in symbols}
    dates = frames[symbols[0]].index
    if any(not frames[s].index.equals(dates) for s in symbols):
        raise ValueError("Unaligned snapshot dates")
    rows = [
        evaluate(frames, "BREAKOUT", None),
        evaluate(frames, "BREAKOUT_BE_1R", 1.0),
    ]
    base = rows[0]
    assert base["accepted"] == 38 and base["closed"] == 36 and base["open"] == 2
    assert abs(base["realized_pl"] - 89.90) < 0.015
    assert abs(base["marked_equity"] - 1087.92) < 0.015
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("PASS 2/2 break-even comparison, risk/accounting and baseline regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: +1R uses entry fill minus initial raw stop; arms NEXT session only.")
    print("NOTE: entry-price stop does NOT guarantee net zero due to gaps and execution costs.")
    print("NOTE: original per-position risk allocation is not released on break-even.")
    print("NOTE: in-sample research, not validated on unseen future data.")
    print("NOTE: no broker orders, live portfolio, or database writes.")


if __name__ == "__main__":
    main()
