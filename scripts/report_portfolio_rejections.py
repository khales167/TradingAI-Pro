"""V12.2 shared-$500 portfolio rejection diagnostics from verified snapshots.

Read-only: reproduces the V12.1 prior-day technical signal and candidate
next-day entry. Reports both independent risk and exposure barriers; these
can overlap, so counts are not additive.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean

from scripts.report_shared_portfolio import SYMBOLS, prepared, technical_signal

CAPITAL = 500.0
RISK_PCT = 1.0
EXPOSURE_PCT = 40.0
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUT = Path("reports/portfolio_rejection_diagnostics.csv")


def main():
    slip = SLIPPAGE_BPS / 10000.0
    rows = []
    print("V12.2 PORTFOLIO REJECTION DIAGNOSTICS | shared capital $500")
    for symbol in SYMBOLS:
        data = prepared(symbol)
        candidates = []
        for i in range(209, len(data)):
            previous = data.iloc[i - 1]
            if not technical_signal(previous):
                continue
            today = data.iloc[i]
            reference_open = float(today["Open"])
            atr = float(previous["ATR"])
            entry = reference_open * (1 + slip)
            stop = reference_open - 1.5 * atr
            stop_fill = stop * (1 - slip)
            unit_risk = entry - stop_fill + 2 * COMMISSION
            if not all(math.isfinite(v) for v in (entry, atr, unit_risk)) or entry <= 0 or unit_risk <= 0:
                raise AssertionError(f"{symbol}: invalid candidate at {data.index[i]}")
            budget = CAPITAL * RISK_PCT / 100
            exposure_limit = CAPITAL * EXPOSURE_PCT / 100
            # With a whole share, both conditions must hold:
            # capital >= unit_risk / risk_fraction
            # capital >= entry / exposure_fraction.
            risk_capital = unit_risk / (RISK_PCT / 100)
            exposure_capital = entry / (EXPOSURE_PCT / 100)
            cash_capital = entry + COMMISSION
            candidates.append({
                "date": str(data.index[i].date()),
                "entry": entry,
                "atr": atr,
                "risk_per_share": unit_risk,
                "risk_rejected": unit_risk > budget + 1e-10,
                "exposure_rejected": entry > exposure_limit + 1e-10,
                "cash_rejected": entry + COMMISSION > CAPITAL + 1e-10,
                "minimum_capital_for_one_share": max(risk_capital, exposure_capital, cash_capital),
            })
        risks = [c["risk_per_share"] for c in candidates]
        required = [c["minimum_capital_for_one_share"] for c in candidates]
        row = {
            "symbol": symbol,
            "technical_signals": len(candidates),
            "risk_rejections": sum(c["risk_rejected"] for c in candidates),
            "exposure_rejections": sum(c["exposure_rejected"] for c in candidates),
            "cash_rejections": sum(c["cash_rejected"] for c in candidates),
            "both_risk_and_exposure": sum(c["risk_rejected"] and c["exposure_rejected"] for c in candidates),
            "minimum_risk_per_share": min(risks) if risks else None,
            "average_risk_per_share": mean(risks) if risks else None,
            "minimum_capital_any_signal": min(required) if required else None,
            "average_minimum_capital": mean(required) if required else None,
        }
        rows.append(row)
        if candidates:
            print(
                f"{symbol:5} signals={len(candidates):3} "
                f"risk>{CAPITAL*RISK_PCT/100:.0f}={row['risk_rejections']:3} "
                f"exposure>{CAPITAL*EXPOSURE_PCT/100:.0f}={row['exposure_rejections']:3} "
                f"both={row['both_risk_and_exposure']:3} "
                f"min_risk/share=${row['minimum_risk_per_share']:.2f} "
                f"avg_risk/share=${row['average_risk_per_share']:.2f} "
                f"min_capital_one_share=${row['minimum_capital_any_signal']:.2f}"
            )
        else:
            print(f"{symbol:5} signals=0")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(SYMBOLS)} stock diagnostics")
    print(f"Total technical signals: {sum(r['technical_signals'] for r in rows)}")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: barriers overlap; counts are NOT additive.")
    print("NOTE: minimum capital is per historical signal, for ONE whole share only; not a viable portfolio recommendation.")
    print("NOTE: candidates ignore occupied-position suppression; at $500 V12.1 accepted zero trades.")
    print("NOTE: no margin, fractional shares, live portfolio writes, or broker orders.")


if __name__ == "__main__":
    main()
