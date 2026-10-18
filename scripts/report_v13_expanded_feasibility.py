"""V13.3 feasibility comparison across 15 SHA-verified historical stock snapshots.

Per-signal whole-share feasibility only; NOT portfolio execution or P/L.
Uses the unchanged V13.1 $1000 cash, 1% risk, 40% exposure assumptions.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean

from core.daily_backtester import risk_limited_shares
from scripts.report_shared_portfolio import prepared, technical_signal
from scripts.prepare_v13_universe import NEW_SYMBOLS

ORIGINAL = ("AAPL", "AMD", "AVGO", "NVDA", "TSLA")
SYMBOLS = tuple(sorted(set(ORIGINAL + NEW_SYMBOLS)))
CAPITAL = 1000.0
RISK_BUDGET = CAPITAL * 0.01
EXPOSURE_LIMIT = CAPITAL * 0.40
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUT = Path("reports/v13_expanded_stock_feasibility.csv")


def main():
    slip = SLIPPAGE_BPS / 10000
    rows = []
    print("V13.3 EXPANDED STOCK FEASIBILITY | $1000 | 15 HISTORICAL SNAPSHOTS")
    for symbol in SYMBOLS:
        df = prepared(symbol)
        signals = 0
        feasible = 0
        blocked_risk = blocked_exposure = blocked_cash = 0
        risks = []
        for i in range(209, len(df)):
            previous = df.iloc[i - 1]
            if not technical_signal(previous):
                continue
            today = df.iloc[i]
            reference_open = float(today["Open"])
            atr = float(previous["ATR"])
            entry = reference_open * (1 + slip)
            stop = reference_open - 1.5 * atr
            unit_risk = entry - stop * (1 - slip) + 2 * COMMISSION
            if not all(math.isfinite(x) for x in (entry, atr, unit_risk)):
                raise AssertionError(f"{symbol} invalid candidate {df.index[i]}")
            if entry <= 0 or unit_risk <= 0:
                raise AssertionError(f"{symbol} nonpositive entry/risk")
            risk_shares = risk_limited_shares(RISK_BUDGET, unit_risk)
            exposure_shares = int((EXPOSURE_LIMIT + 1e-10) // entry)
            cash_shares = int((CAPITAL + 1e-10) // (entry + COMMISSION))
            signals += 1
            risks.append(unit_risk)
            blocked_risk += risk_shares == 0
            blocked_exposure += exposure_shares == 0
            blocked_cash += cash_shares == 0
            feasible += min(risk_shares, exposure_shares, cash_shares) >= 1
        row = {
            "symbol": symbol,
            "group": "NEW" if symbol in NEW_SYMBOLS else "ORIGINAL",
            "signals": signals,
            "feasible": feasible,
            "feasible_pct": 100 * feasible / signals if signals else 0,
            "blocked_risk": blocked_risk,
            "blocked_exposure": blocked_exposure,
            "blocked_cash": blocked_cash,
            "min_risk_per_share": min(risks) if risks else None,
            "avg_risk_per_share": mean(risks) if risks else None,
        }
        rows.append(row)
        print(
            f"{symbol:5} {row['group']:8} signals={signals:3} "
            f"feasible={feasible:3} ({row['feasible_pct']:5.1f}%) "
            f"risk_block={blocked_risk:3} exposure_block={blocked_exposure:3} "
            f"cash_block={blocked_cash:3}"
        )
    assert len(rows) == 15 and len({r["symbol"] for r in rows}) == 15
    assert sum(r["signals"] for r in rows if r["group"] == "ORIGINAL") == 131, (
        "V13.1 regression failed: original 5 stocks must total 131 signals"
    )
    assert sum(r["feasible"] for r in rows if r["group"] == "ORIGINAL") == 37, (
        "V13.1 regression failed: original 5 stocks must total 37 feasible signals"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS {len(rows)}/15 stock checks and original-universe regression")
    print(f"ALL: signals={sum(r['signals'] for r in rows)} "
          f"feasible={sum(r['feasible'] for r in rows)}")
    print(f"NEW: signals={sum(r['signals'] for r in rows if r['group']=='NEW')} "
          f"feasible={sum(r['feasible'] for r in rows if r['group']=='NEW')}")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: independent candidate feasibility, not simultaneous shared-cash trades.")
    print("NOTE: block counts overlap; daily OHLCV cannot verify bid-ask spread.")
    print("NOTE: this does not measure profitability or establish a trading edge.")
    print("NOTE: no margin, broker orders, live portfolio changes, or database writes.")


if __name__ == "__main__":
    main()
