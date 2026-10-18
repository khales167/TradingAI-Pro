"""V12.4 read-only shared-$2000 portfolio equity and drawdown audit."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from scripts.report_shared_portfolio import SYMBOLS, prepared, run_portfolio

CAPITAL = 2000.0
OUT = Path("reports")
EQUITY_CSV = OUT / "shared_portfolio_equity_curve.csv"
TRADES_CSV = OUT / "shared_portfolio_trade_audit.csv"


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    frames = {s: prepared(s) for s in SYMBOLS}
    result = run_portfolio(frames, capital=CAPITAL, record_daily=True)
    daily = result["daily"]
    trades = result["trades"]
    assert daily, "Missing daily equity history"
    assert len(trades) == result["diagnostics"]["accepted"] - len(result["positions"])
    assert abs(daily[-1]["equity"] - result["equity_marked"]) < 1e-7
    assert all(x["cash"] >= -1e-8 for x in daily)
    assert all(x["open_positions"] <= 5 for x in daily)
    assert all(x["open_risk"] <= CAPITAL * 0.03 + 1e-8 for x in daily)
    assert all(x["entry_exposure"] <= CAPITAL * 0.40 + 1e-8 for x in daily)

    peak = CAPITAL
    peak_date = "INITIAL"
    max_drawdown = 0.0
    drawdown_peak = "INITIAL"
    drawdown_trough = "INITIAL"
    for row in daily:
        if row["equity"] > peak:
            peak = row["equity"]
            peak_date = row["date"]
        row["peak_equity"] = peak
        row["drawdown_usd"] = row["equity"] - peak
        row["drawdown_pct"] = (row["equity"] / peak - 1) * 100
        if row["drawdown_pct"] < max_drawdown:
            max_drawdown = row["drawdown_pct"]
            drawdown_peak = peak_date
            drawdown_trough = row["date"]

    by_symbol = defaultdict(lambda: {"trades": 0, "pl": 0.0})
    for trade in trades:
        item = by_symbol[trade["symbol"]]
        item["trades"] += 1
        item["pl"] += trade["pl"]
    closed_pl = sum(t["pl"] for t in trades)
    open_entry_fees = sum(p["shares"] * 0.005 for p in result["positions"].values())
    assert abs(result["cash"] + sum(p["entry"] * p["shares"] for p in result["positions"].values())
               - CAPITAL - closed_pl + open_entry_fees) < 1e-6

    OUT.mkdir(parents=True, exist_ok=True)
    save_csv(EQUITY_CSV, daily, list(daily[0]))
    if trades:
        save_csv(TRADES_CSV, trades, list(trades[0]))
    print("V12.4 SHARED PORTFOLIO EQUITY & DRAWDOWN AUDIT")
    print(f"capital=${CAPITAL:.2f} closed={len(trades)} open={len(result['positions'])}")
    print(f"closed_P/L=${closed_pl:+.2f} final_equity=${result['equity_marked']:.2f}")
    print(f"maximum_marked_drawdown={max_drawdown:.2f}% peak={drawdown_peak} trough={drawdown_trough}")
    if trades:
        winner = max(trades, key=lambda t: t["pl"])
        loser = min(trades, key=lambda t: t["pl"])
        print(f"largest_win={winner['symbol']} ${winner['pl']:+.2f} exit={winner['exit_date']}")
        print(f"largest_loss={loser['symbol']} ${loser['pl']:+.2f} exit={loser['exit_date']}")
        print(f"largest_win_share_of_net_P/L={winner['pl'] / closed_pl * 100:.1f}%"
              if abs(closed_pl) > 1e-10 else "largest_win_share_of_net_P/L=N/A")
    for symbol in SYMBOLS:
        item = by_symbol[symbol]
        print(f"{symbol:5} closed={item['trades']:2} P/L=${item['pl']:+.2f}")
    print(f"PASS daily risk/exposure limits and equity ledger | days={len(daily)}")
    print(f"CSV equity: {EQUITY_CSV.resolve()}")
    if trades:
        print(f"CSV trades: {TRADES_CSV.resolve()}")
    print("NOTE: drawdown uses daily adjusted close marks, not intraday equity or liquidation costs.")
    print("NOTE: fixed $2000 historical scenario selected for diagnosis, not optimized capital.")
    print("NOTE: no live orders, broker access, margin, or database writes.")


if __name__ == "__main__":
    main()
