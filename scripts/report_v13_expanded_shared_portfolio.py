"""V13.4 compare original and expanded historical shared-cash portfolios.

Same fixed $1000 capital and trading rules. Full 15-stock portfolio uses
alphabetical entry priority, so a larger universe changes cash allocation.
No optimization or live trading.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS as ORIGINAL, prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS

CAPITAL = 1000.0
OUT = Path("reports/v13_expanded_shared_portfolio.csv")


def evaluate(label, frames):
    result = run_portfolio(
        frames,
        capital=CAPITAL,
        risk_pct=1.0,
        max_exposure_pct=40.0,
        max_portfolio_risk_pct=3.0,
        max_positions=5,
        commission=0.005,
        slippage_bps=5.0,
        record_daily=True,
    )
    d = result["diagnostics"]
    trades = result["trades"]
    pl = sum(float(t["pl"]) for t in trades)
    open_fees = sum(p["shares"] * 0.005 for p in result["positions"].values())
    open_cost = sum(p["shares"] * p["entry"] for p in result["positions"].values())
    assert abs(result["cash"] + open_cost - CAPITAL - pl + open_fees) < 1e-6
    assert d["signals"] == d["accepted"] + sum(
        v for k, v in d.items() if k.startswith("rejected_")
    )
    assert d["accepted"] == len(trades) + len(result["positions"])
    assert all(x["cash"] >= -1e-8 for x in result["daily"])
    assert all(x["open_risk"] <= CAPITAL * 0.03 + 1e-8 for x in result["daily"])
    assert all(x["entry_exposure"] <= CAPITAL * 0.40 + 1e-8 for x in result["daily"])
    assert all(x["open_positions"] <= 5 for x in result["daily"])
    assert abs(result["daily"][-1]["equity"] - result["equity_marked"]) < 1e-7
    by_symbol = {}
    for t in trades:
        s = t["symbol"]
        if s not in by_symbol:
            by_symbol[s] = {"trades": 0, "pl": 0.0}
        by_symbol[s]["trades"] += 1
        by_symbol[s]["pl"] += t["pl"]
    peak = CAPITAL
    max_dd = 0.0
    for day in result["daily"]:
        peak = max(peak, day["equity"])
        max_dd = min(max_dd, (day["equity"] / peak - 1) * 100)
    row = {
        "scenario": label,
        "stocks": len(frames),
        "signals": d["signals"],
        "accepted": d["accepted"],
        "closed": len(trades),
        "open": len(result["positions"]),
        "closed_pl_usd": pl,
        "closed_return_pct": 100 * pl / CAPITAL,
        "marked_equity_usd": result["equity_marked"],
        "max_daily_drawdown_pct": max_dd,
        **{k: d[k] for k in d if k.startswith("rejected_")},
    }
    print(
        f"{label:12} stocks={len(frames):2} signals={d['signals']:3} "
        f"accepted={d['accepted']:3} closed={len(trades):3} "
        f"open={len(result['positions'])} P/L=${pl:+.2f} "
        f"return={100 * pl / CAPITAL:+.2f}% "
        f"max_DD={max_dd:.2f}% equity=${result['equity_marked']:.2f}"
    )
    for symbol in sorted(by_symbol):
        x = by_symbol[symbol]
        print(f"  {symbol:5} trades={x['trades']:2} P/L=${x['pl']:+.2f}")
    return row


def main():
    all_symbols = tuple(sorted(set(ORIGINAL) | set(NEW_SYMBOLS)))
    frames = {symbol: prepared(symbol) for symbol in all_symbols}
    dates = frames[all_symbols[0]].index
    if any(not frames[s].index.equals(dates) for s in all_symbols):
        raise ValueError("Snapshot trading dates are not aligned; do not silently fill gaps")
    print("V13.4 SHARED $1000 PORTFOLIO | ORIGINAL 5 VS EXPANDED 15")
    baseline = evaluate("ORIGINAL_5", {s: frames[s] for s in ORIGINAL})
    assert baseline["closed"] == 10, "V12.3 baseline expected 10 closed trades"
    assert abs(baseline["closed_pl_usd"] - (-10.19)) < 0.015, (
        "V12.3 baseline P/L regression failed"
    )
    expanded = evaluate("EXPANDED_15", frames)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(baseline))
        writer.writeheader()
        writer.writerows((baseline, expanded))
    print(f"delta_expanded_vs_original=${expanded['closed_pl_usd'] - baseline['closed_pl_usd']:+.2f}")
    print("PASS 2/2 portfolio scenarios, accounting/risk limits, and original baseline regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: same $1000 shared cash; new tickers change priority and trade paths.")
    print("NOTE: historical adjusted daily bars; close-marked drawdown excludes intraday risk.")
    print("NOTE: no live portfolio/database writes, margin, or broker orders.")


if __name__ == "__main__":
    main()
