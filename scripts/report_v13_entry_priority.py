"""V13.5 test allocation-order robustness with identical historical signals/rules."""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS
from scripts.report_shared_portfolio import SYMBOLS as ORIGINAL

CAPITAL = 1000.0
OUT = Path("reports/v13_entry_priority_robustness.csv")


def main():
    symbols = sorted(set(ORIGINAL) | set(NEW_SYMBOLS))
    frames = {s: prepared(s) for s in symbols}
    print("V13.5 ENTRY PRIORITY ROBUSTNESS | $1000 | 15 STOCKS")
    rows = []
    for priority in ("alphabetical", "reverse", "adx"):
        r = run_portfolio(
            frames, capital=CAPITAL, risk_pct=1.0,
            max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
            max_positions=5, commission=0.005, slippage_bps=5.0,
            record_daily=True, entry_priority=priority,
        )
        d = r["diagnostics"]
        pl = sum(t["pl"] for t in r["trades"])
        peak, drawdown = CAPITAL, 0.0
        for day in r["daily"]:
            peak = max(peak, day["equity"])
            drawdown = min(drawdown, 100 * (day["equity"] / peak - 1))
            assert day["cash"] >= -1e-8
            assert day["open_risk"] <= 30 + 1e-8
            assert day["entry_exposure"] <= 400 + 1e-8
            assert day["open_positions"] <= 5
        assert d["signals"] == d["accepted"] + sum(v for k, v in d.items() if k.startswith("rejected_"))
        assert d["accepted"] == len(r["trades"]) + len(r["positions"])
        assert abs(r["cash"] + sum(p["shares"] * (p["entry"] + 0.005) for p in r["positions"].values()) - CAPITAL - pl) < 1e-6
        assert abs(r["daily"][-1]["equity"] - r["equity_marked"]) < 1e-6
        row = {
            "priority": priority, "signals": d["signals"],
            "accepted": d["accepted"], "closed": len(r["trades"]),
            "open": len(r["positions"]), "realized_pl": pl,
            "marked_equity": r["equity_marked"], "max_drawdown_pct": drawdown,
        }
        rows.append(row)
        print(f"{priority:12} signals={d['signals']:3} accepted={d['accepted']:3} "
              f"closed={len(r['trades']):3} open={len(r['positions'])} "
              f"P/L=${pl:+.2f} equity=${r['equity_marked']:.2f} max_DD={drawdown:.2f}%")
    base = rows[0]
    assert base["accepted"] == 59 and base["closed"] == 57 and base["open"] == 2
    assert abs(base["realized_pl"] - 80.79) < 0.015
    assert abs(base["marked_equity"] - 1078.81) < 0.015
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"realized_P/L_range=${min(x['realized_pl'] for x in rows):+.2f} "
          f"to ${max(x['realized_pl'] for x in rows):+.2f}")
    print("PASS 3/3 priority scenarios, limits, accounting, and V13.4 regression")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: ADX priority uses prior completed bar; no same-day lookahead.")
    print("NOTE: not out-of-sample; no live trading or portfolio changes.")


if __name__ == "__main__":
    main()
