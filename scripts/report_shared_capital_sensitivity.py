"""V12.3 shared-portfolio capital sensitivity on verified historical snapshots.

Six independent simulations, each with ONE shared cash balance across five
stocks. No live account, broker, or strategy modifications.
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio

CAPITAL_LEVELS = (500, 750, 1000, 1500, 2000, 3000)
OUT = Path("reports/shared_portfolio_capital_sensitivity.csv")


def main():
    frames = {symbol: prepared(symbol) for symbol in SYMBOLS}
    rows = []
    print("V12.3 SHARED PORTFOLIO CAPITAL SENSITIVITY")
    for capital in CAPITAL_LEVELS:
        result = run_portfolio(
            frames, capital=float(capital), risk_pct=1.0,
            max_exposure_pct=40.0, max_portfolio_risk_pct=3.0,
            max_positions=5, commission=0.005, slippage_bps=5,
        )
        d = result["diagnostics"]
        closed_pl = sum(float(t["pl"]) for t in result["trades"])
        open_cost = sum(p["shares"] * p["entry"] for p in result["positions"].values())
        assert abs(result["cash"] + open_cost - capital - closed_pl) < 1e-6, (
            f"Cash ledger mismatch at capital={capital}"
        )
        rejected_total = sum(value for key, value in d.items() if key.startswith("rejected_"))
        assert d["signals"] == d["accepted"] + rejected_total, (
            f"Signal accounting mismatch at capital={capital}"
        )
        assert len(result["trades"]) + len(result["positions"]) == d["accepted"], (
            f"Entry/exit accounting mismatch at capital={capital}"
        )
        assert result["cash"] >= -1e-8, f"Negative cash at capital={capital}"
        assert len(result["positions"]) <= 5
        open_risk = sum(p["shares"] * p["unit_risk"] for p in result["positions"].values())
        assert open_risk <= capital * 0.03 + 1e-9
        assert open_cost <= capital * 0.40 + 1e-9
        row = {
            "initial_capital": capital,
            "risk_per_trade_usd": capital * 0.01,
            "max_exposure_usd": capital * 0.40,
            "max_portfolio_risk_usd": capital * 0.03,
            "signals": d["signals"],
            "accepted": d["accepted"],
            "closed": len(result["trades"]),
            "open": len(result["positions"]),
            "rejected_risk": d["rejected_risk"],
            "rejected_exposure": d["rejected_exposure"],
            "rejected_cash": d["rejected_cash"],
            "rejected_portfolio_risk": d["rejected_portfolio_risk"],
            "rejected_positions": d["rejected_positions"],
            "closed_trade_pl_usd": closed_pl,
            "closed_trade_return_pct": closed_pl / capital * 100,
            "ending_cash_usd": result["cash"],
            "ending_marked_equity_usd": result["equity_marked"],
        }
        rows.append(row)
        print(
            f"capital=${capital:4} signals={d['signals']:3} "
            f"accepted={d['accepted']:2} closed={len(result['trades']):2} "
            f"open={len(result['positions'])} "
            f"closed_P/L=${closed_pl:+8.2f} "
            f"return={row['closed_trade_return_pct']:+6.2f}% "
            f"equity=${result['equity_marked']:.2f}"
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(CAPITAL_LEVELS)} shared-portfolio scenarios")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: closed-trade return excludes unrealized P/L; marked equity includes unliquidated holdings.")
    print("NOTE: fixed alphabetical entry priority, same-day exit cash not recycled.")
    print("NOTE: adjusted historical bars; no real broker settlement or order-book modeling.")
    print("NOTE: no margin, broker orders, live portfolio writes, or database changes.")


if __name__ == "__main__":
    main()
