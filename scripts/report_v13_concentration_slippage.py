"""V13.7 historical profit concentration and slippage robustness.

All runs use the unchanged $1000 shared-cash portfolio and alphabetical
priority. Exclusions rerun the complete simulation, not P/L subtraction.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS

CAPITAL = 1000.0
OUT = Path("reports/v13_concentration_slippage.csv")


def simulate(frames, label, slippage_bps=5.0):
    r = run_portfolio(
        frames, capital=CAPITAL, risk_pct=1.0,
        max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
        max_positions=5, commission=0.005, slippage_bps=slippage_bps,
        record_daily=True, entry_priority="alphabetical",
    )
    d = r["diagnostics"]
    pl = sum(t["pl"] for t in r["trades"])
    assert d["signals"] == d["accepted"] + sum(
        v for k, v in d.items() if k.startswith("rejected_")
    )
    assert d["accepted"] == len(r["trades"]) + len(r["positions"])
    assert abs(r["cash"] + sum(
        p["shares"] * (p["entry"] + 0.005) for p in r["positions"].values()
    ) - CAPITAL - pl) < 1e-6
    assert abs(r["daily"][-1]["equity"] - r["equity_marked"]) < 1e-6
    peak, dd = CAPITAL, 0.0
    for day in r["daily"]:
        peak = max(peak, day["equity"])
        dd = min(dd, 100 * (day["equity"] / peak - 1))
        assert day["cash"] >= -1e-8
        assert day["open_risk"] <= 30 + 1e-8
        assert day["entry_exposure"] <= 400 + 1e-8
        assert day["open_positions"] <= 5
    row = {
        "scenario": label, "slippage_bps": slippage_bps,
        "stocks": len(frames), "signals": d["signals"],
        "accepted": d["accepted"], "closed": len(r["trades"]),
        "open": len(r["positions"]), "realized_pl": pl,
        "marked_equity": r["equity_marked"],
        "marked_pl": r["equity_marked"] - CAPITAL,
        "max_drawdown_pct": dd,
    }
    print(f"{label:20} slip={slippage_bps:4g}bps accepted={d['accepted']:3} "
          f"closed={len(r['trades']):3} open={len(r['positions'])} "
          f"realized=${pl:+.2f} marked=${row['marked_pl']:+.2f} "
          f"DD={dd:.2f}%")
    return row, r


def main():
    symbols = sorted(set(SYMBOLS) | set(NEW_SYMBOLS))
    frames = {s: prepared(s) for s in symbols}
    dates = frames[symbols[0]].index
    if any(not frames[s].index.equals(dates) for s in symbols):
        raise ValueError("Unaligned snapshot dates")
    print("V13.7 CONCENTRATION & SLIPPAGE | $1000 | 15 STOCKS")
    baseline, baseline_result = simulate(frames, "BASELINE", 5.0)
    assert baseline["accepted"] == 59 and baseline["closed"] == 57 and baseline["open"] == 2
    assert abs(baseline["realized_pl"] - 80.79) < 0.015
    assert abs(baseline["marked_equity"] - 1078.81) < 0.015
    closed = baseline_result["trades"]
    if not closed:
        raise AssertionError("No closed trades to audit")
    biggest = max(closed, key=lambda t: t["pl"])
    accounting_only = baseline["realized_pl"] - biggest["pl"]
    print(f"LARGEST WIN (accounting only): {biggest['symbol']} "
          f"entry={biggest['entry_date']} exit={biggest['exit_date']} "
          f"P/L=${biggest['pl']:+.2f} remaining_closed_P/L=${accounting_only:+.2f}")
    print("NOTE: largest-winner removal is arithmetic only, NOT a replay.")
    rows = [baseline]
    for excluded in ("CSCO", "INTC"):
        row, _ = simulate(
            {s: df for s, df in frames.items() if s != excluded},
            f"EXCLUDE_{excluded}", 5.0,
        )
        rows.append(row)
    for slip in (10.0, 20.0):
        row, _ = simulate(frames, f"SLIPPAGE_{int(slip)}BPS", slip)
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS {len(rows)}/{len(rows)} shared-cash scenario checks and baseline regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: excluding stocks changes cash competition and subsequent trades.")
    print("NOTE: higher slippage can alter position sizing and trade paths non-monotonically.")
    print("NOTE: open positions are marked at close without hypothetical liquidation costs.")
    print("NOTE: reused historical period, not out-of-sample validation.")
    print("NOTE: no broker orders, live portfolio, or database writes.")


if __name__ == "__main__":
    main()
