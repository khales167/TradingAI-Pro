"""V13.1 $1,000 cash-account historical stock feasibility baseline.

Uses only existing SHA-verified local snapshots. This is NOT a live screener
and does not download or silently invent an expanded stock universe.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean

from core.daily_backtester import risk_limited_shares
from scripts.report_shared_portfolio import SYMBOLS, prepared, technical_signal

CAPITAL = 1000.0
RISK_BUDGET = CAPITAL * 0.01
EXPOSURE_LIMIT = CAPITAL * 0.40
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUT = Path("reports/v13_1000_stock_feasibility.csv")


def main():
    slip = SLIPPAGE_BPS / 10000
    rows = []
    print("V13.1 $1000 HISTORICAL STOCK FEASIBILITY | EXISTING SNAPSHOTS")
    for symbol in SYMBOLS:
        df = prepared(symbol)
        candidates = []
        for i in range(209, len(df)):
            prior = df.iloc[i - 1]
            if not technical_signal(prior):
                continue
            bar = df.iloc[i]
            raw_open = float(bar["Open"])
            atr = float(prior["ATR"])
            entry = raw_open * (1 + slip)
            stop = raw_open - 1.5 * atr
            unit_risk = entry - stop * (1 - slip) + 2 * COMMISSION
            volume = float(prior["Volume"])
            rvol = float(prior["RVOL"])
            if not all(math.isfinite(x) for x in (entry, atr, unit_risk, volume, rvol)):
                raise AssertionError(f"Invalid candidate for {symbol} on {df.index[i]}")
            if entry <= 0 or unit_risk <= 0:
                raise AssertionError(f"Nonpositive entry or risk for {symbol}")
            risk_shares = risk_limited_shares(RISK_BUDGET, unit_risk)
            exposure_shares = int((EXPOSURE_LIMIT + 1e-10) // entry)
            cash_shares = int((CAPITAL + 1e-10) // (entry + COMMISSION))
            feasible = min(risk_shares, exposure_shares, cash_shares) >= 1
            candidates.append({
                "risk": unit_risk, "entry": entry, "volume": volume,
                "rvol": rvol, "feasible": feasible,
                "risk_block": risk_shares == 0,
                "exposure_block": exposure_shares == 0,
                "cash_block": cash_shares == 0,
            })
        row = {
            "symbol": symbol,
            "technical_signals": len(candidates),
            "individually_feasible_signals": sum(c["feasible"] for c in candidates),
            "risk_blocked": sum(c["risk_block"] for c in candidates),
            "exposure_blocked": sum(c["exposure_block"] for c in candidates),
            "cash_blocked": sum(c["cash_block"] for c in candidates),
            "minimum_risk_per_share": min((c["risk"] for c in candidates), default=None),
            "average_risk_per_share": mean(c["risk"] for c in candidates) if candidates else None,
            "average_signal_volume": mean(c["volume"] for c in candidates) if candidates else None,
            "average_signal_rvol": mean(c["rvol"] for c in candidates) if candidates else None,
        }
        rows.append(row)
        print(
            f"{symbol:5} signals={row['technical_signals']:3} "
            f"feasible={row['individually_feasible_signals']:3} "
            f"risk_block={row['risk_blocked']:3} "
            f"exposure_block={row['exposure_blocked']:3} "
            f"cash_block={row['cash_blocked']:3} "
            + (f"min_risk/share=${row['minimum_risk_per_share']:.2f} "
               f"avg_risk/share=${row['average_risk_per_share']:.2f}"
               if candidates else "no technical signals")
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS {len(rows)}/{len(SYMBOLS)} historical stock feasibility checks")
    print(f"Total signals={sum(r['technical_signals'] for r in rows)} "
          f"individually feasible={sum(r['individually_feasible_signals'] for r in rows)}")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: feasibility is assessed per candidate with full $1000 available, not shared-portfolio acceptance.")
    print("NOTE: risk, exposure, and cash blocking counts can overlap.")
    print("NOTE: daily volume/RVOL are descriptive; bid-ask spread and intraday liquidity are NOT verified.")
    print("NOTE: only 5 existing historical snapshots; no new stocks downloaded or screened yet.")
    print("NOTE: no live orders, margin, database writes, or portfolio changes.")


if __name__ == "__main__":
    main()
