"""V13.6 chronological non-overlapping priority stability windows.

Each window starts with fresh $1000 cash and 209 precomputed warmup bars.
Open positions are marked to last close, not force-liquidated.
Historical sensitivity only; not untouched out-of-sample evidence.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio
from scripts.prepare_v13_universe import NEW_SYMBOLS

CAPITAL = 1000.0
WARMUP = 209
WINDOW = 75
MIN_FINAL_WINDOW = 30
PRIORITIES = ("alphabetical", "reverse", "adx")
OUT = Path("reports/v13_priority_stability.csv")


def main():
    symbols = tuple(sorted(set(SYMBOLS) | set(NEW_SYMBOLS)))
    frames = {s: prepared(s) for s in symbols}
    dates = frames[symbols[0]].index
    if any(not frames[s].index.equals(dates) for s in symbols):
        raise ValueError("Snapshots must share aligned dates")
    rows = []
    print("V13.6 PRIORITY STABILITY | $1000 | non-overlapping chronological windows")
    window_no = 0
    for begin in range(WARMUP, len(dates), WINDOW):
        end = min(begin + WINDOW, len(dates))
        if end - begin < MIN_FINAL_WINDOW:
            print(f"SKIP trailing {end-begin} trading days (minimum {MIN_FINAL_WINDOW})")
            break
        window_no += 1
        # All indicator values were computed on full historical data with past-only rolling windows.
        # Local backtester starts at row 209, i.e. the first trading day of this window.
        local = {s: df.iloc[begin-WARMUP:end].copy() for s, df in frames.items()}
        assert len(next(iter(local.values()))) >= WARMUP + MIN_FINAL_WINDOW
        print(f"WINDOW {window_no} {dates[begin].date()} to {dates[end-1].date()} "
              f"days={end-begin}")
        for priority in PRIORITIES:
            r = run_portfolio(
                local, capital=CAPITAL, risk_pct=1.0, max_exposure_pct=40.0,
                max_portfolio_risk_pct=3.0, max_positions=5,
                commission=0.005, slippage_bps=5.0,
                record_daily=True, entry_priority=priority,
            )
            d = r["diagnostics"]
            pl = sum(t["pl"] for t in r["trades"])
            peak, max_dd = CAPITAL, 0.0
            for day in r["daily"]:
                peak = max(peak, day["equity"])
                max_dd = min(max_dd, (day["equity"] / peak - 1) * 100)
                assert day["cash"] >= -1e-8
                assert day["open_risk"] <= 30 + 1e-8
                assert day["entry_exposure"] <= 400 + 1e-8
                assert day["open_positions"] <= 5
            assert d["signals"] == d["accepted"] + sum(
                v for k, v in d.items() if k.startswith("rejected_")
            )
            assert d["accepted"] == len(r["trades"]) + len(r["positions"])
            open_entry_fees = sum(p["shares"] * 0.005 for p in r["positions"].values())
            assert abs(r["cash"] + sum(
                p["shares"] * p["entry"] for p in r["positions"].values()
            ) + open_entry_fees - CAPITAL - pl) < 1e-6
            assert abs(r["daily"][-1]["equity"] - r["equity_marked"]) < 1e-6
            marked_pl = r["equity_marked"] - CAPITAL
            rows.append({
                "window": window_no, "start": str(dates[begin].date()),
                "end": str(dates[end-1].date()), "days": end-begin,
                "priority": priority, "signals": d["signals"],
                "accepted": d["accepted"], "closed": len(r["trades"]),
                "open": len(r["positions"]), "realized_pl": pl,
                "marked_pl": marked_pl, "marked_equity": r["equity_marked"],
                "max_drawdown_pct": max_dd,
            })
            print(f"  {priority:12} accepted={d['accepted']:2} "
                  f"closed={len(r['trades']):2} open={len(r['positions'])} "
                  f"realized=${pl:+.2f} marked=${marked_pl:+.2f} "
                  f"DD={max_dd:.2f}%")
    if window_no < 2:
        raise AssertionError("Not enough independent chronological windows")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("WINDOW WINNERS (marked P/L; ties possible)")
    wins = {p: 0 for p in PRIORITIES}
    for n in range(1, window_no + 1):
        group = [x for x in rows if x["window"] == n]
        best = max(x["marked_pl"] for x in group)
        winners = [x["priority"] for x in group if abs(x["marked_pl"]-best) < 1e-8]
        for p in winners:
            wins[p] += 1
        print(f"  window={n} winner={','.join(winners)}")
    print("wins: " + ", ".join(f"{p}={wins[p]}" for p in PRIORITIES))
    print(f"PASS {len(rows)}/{window_no*3} window-priority accounting and risk checks")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: windows reset cash and positions; window results do not sum to full-period P/L.")
    print("NOTE: final open positions are marked, not liquidated; marked values exclude exit costs.")
    print("NOTE: historical data already examined; NOT an untouched out-of-sample test.")
    print("NOTE: no broker orders, live portfolio, or database writes.")


if __name__ == "__main__":
    main()
