"""V12.5 shared-portfolio concentration and leave-one-symbol-out robustness.

Each exclusion is a FRESH shared-cash simulation: removing a ticker can change
allocation and trade sequencing. The largest-win deletion is accounting-only,
NOT a new backtest. Historical, read-only, no live/broker interaction.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio

CAPITAL = 2000.0
OUT = Path("reports/portfolio_concentration_robustness.csv")


def run(frames):
    result = run_portfolio(
        frames, capital=CAPITAL, risk_pct=1.0, max_exposure_pct=40.0,
        max_portfolio_risk_pct=3.0, max_positions=5,
        commission=0.005, slippage_bps=5.0,
    )
    trades = result["trades"]
    closed_pl = sum(float(t["pl"]) for t in trades)
    # Existing V12.4 runs have no open positions, but account for open-entry
    # commissions correctly in the ledger if a new scenario leaves any open.
    entry_fees_open = sum(p["shares"] * 0.005 for p in result["positions"].values())
    open_cost = sum(p["shares"] * p["entry"] for p in result["positions"].values())
    assert abs(result["cash"] + open_cost - CAPITAL - closed_pl + entry_fees_open) < 1e-6
    assert result["diagnostics"]["accepted"] == len(trades) + len(result["positions"])
    return result, closed_pl


def main():
    frames = {s: prepared(s) for s in SYMBOLS}
    baseline, baseline_pl = run(frames)
    by_symbol = defaultdict(float)
    for trade in baseline["trades"]:
        by_symbol[trade["symbol"]] += float(trade["pl"])
    print("V12.5 PORTFOLIO CONCENTRATION & ROBUSTNESS")
    print(f"BASELINE all 5 stocks | trades={len(baseline['trades'])} "
          f"open={len(baseline['positions'])} P/L=${baseline_pl:+.2f}")
    for symbol in SYMBOLS:
        contribution = by_symbol[symbol]
        print(f"  {symbol:5} baseline_contribution=${contribution:+.2f}")
    assert abs(sum(by_symbol.values()) - baseline_pl) < 1e-7
    if baseline["trades"]:
        biggest = max(baseline["trades"], key=lambda t: t["pl"])
        accounting_pl = baseline_pl - biggest["pl"]
        print(f"ACCOUNTING ONLY remove biggest winner: {biggest['symbol']} "
              f"exit={biggest['exit_date']} winner=${biggest['pl']:+.2f} "
              f"adjusted_P/L=${accounting_pl:+.2f}")
        print("  Not a rerun: ignores cash, exposure, and subsequent path changes.")

    rows = []
    for omitted in (None, *SYMBOLS):
        subset = {s: df for s, df in frames.items() if s != omitted}
        result, pl = run(subset)
        label = "BASELINE" if omitted is None else f"EXCLUDE_{omitted}"
        row = {
            "scenario": label,
            "omitted_symbol": omitted or "",
            "stock_count": len(subset),
            "signals": result["diagnostics"]["signals"],
            "accepted": result["diagnostics"]["accepted"],
            "closed": len(result["trades"]),
            "open": len(result["positions"]),
            "closed_pl_usd": pl,
            "closed_return_pct": pl / CAPITAL * 100,
            "marked_equity_usd": result["equity_marked"],
            "delta_pl_vs_baseline_usd": pl - baseline_pl,
        }
        rows.append(row)
        print(f"{label:15} accepted={row['accepted']:2} closed={row['closed']:2} "
              f"open={row['open']} P/L=${pl:+8.2f} "
              f"delta=${row['delta_pl_vs_baseline_usd']:+8.2f} "
              f"equity=${result['equity_marked']:.2f}")
    assert rows[0]["closed"] == 23, "V12.4 baseline regression: expected 23 closed trades"
    assert abs(rows[0]["closed_pl_usd"] - 85.71) < 0.015, (
        "V12.4 baseline regression: expected +$85.71"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS {len(rows)}/{len(rows)} portfolio scenarios and baseline regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: exclusions are full independent simulations with reallocated shared cash.")
    print("NOTE: concentration and performance on this historical sample do not establish future edge.")
    print("NOTE: no margin, live portfolio/database writes, or broker orders.")


if __name__ == "__main__":
    main()
