"""V10.8 read-only gap-risk analysis on verified daily snapshots.

Compares actual stop-gap fills with the planned stop and 1% risk budget.
No trading rule changes, orders, downloads, or live portfolio writes.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_snapshot_performance import metrics

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START, END = "2024-10-01", "2026-10-16"
CAPITAL = 2000.0
RISK_PCT = 1.0
COMMISSION = 0.005
SLIP_BPS = 5.0
OUT = Path("reports/backtest_gap_risk.csv")


def main():
    rows = []
    all_trades = []
    for symbol in SYMBOLS:
        path = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        result = DailyTechnicalBacktester().run(
            load_snapshot(path), initial_cash=CAPITAL,
            risk_per_trade_pct=RISK_PCT,
            commission_per_share=COMMISSION, slippage_bps=SLIP_BPS,
        )
        trades = result["trades"]
        all_trades.extend(trades)
        stop_gaps = 0
        target_gaps = 0
        risk_breaches = 0
        for i, t in enumerate(trades, 1):
            reason = t["reason"]
            stop_gaps += reason == "STOP_GAP"
            target_gaps += reason == "TARGET_GAP"
            shares = int(t["shares"])
            entry = float(t["entry"])
            exit_fill = float(t["exit"])
            stop = float(t["stop"])
            target = float(t["target"])
            pl = float(t["pl"])
            planned_stop_fill = stop * (1 - SLIP_BPS / 10000)
            planned_stop_loss = (entry - planned_stop_fill + 2 * COMMISSION) * shares
            actual_loss = max(0.0, -pl)
            risk_budget = CAPITAL * RISK_PCT / 100
            breach = actual_loss > risk_budget + 1e-7
            risk_breaches += breach
            if reason == "STOP_GAP":
                gap_extra_loss = (planned_stop_fill - exit_fill) * shares
                assert gap_extra_loss >= -1e-7
            else:
                gap_extra_loss = 0.0
            assert abs(pl - (exit_fill - entry - 2 * COMMISSION) * shares) < 1e-7
            rows.append({
                "symbol": symbol,
                "trade_number": i,
                "entry_date": t["entry_date"],
                "exit_date": t["exit_date"],
                "exit_reason": reason,
                "shares": shares,
                "entry_fill": entry,
                "planned_stop": stop,
                "planned_target": target,
                "exit_fill": exit_fill,
                "planned_stop_loss_usd": planned_stop_loss,
                "risk_budget_usd": risk_budget,
                "actual_net_pl_usd": pl,
                "actual_loss_usd": actual_loss,
                "risk_budget_breached": breach,
                "stop_gap_extra_loss_vs_planned_stop_usd": gap_extra_loss,
            })
        m = metrics(trades, CAPITAL)
        pf_text = "N/A" if m["profit_factor"] is None else ("Infinity" if m["profit_factor"] == float("inf") else f"{m['profit_factor']:.2f}")
        expectancy_text = "N/A" if m["expectancy"] is None else f"${m['expectancy']:+.2f}"
        print(
            f"{symbol:5} trades={len(trades):2} stop_gaps={stop_gaps:2} "
            f"target_gaps={target_gaps:2} risk_breaches={risk_breaches:2} "
            f"PF={pf_text} "
            f"expectancy={expectancy_text}"
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [
            "symbol", "trade_number", "entry_date", "exit_date", "exit_reason",
            "shares", "entry_fill", "planned_stop", "planned_target", "exit_fill",
            "planned_stop_loss_usd", "risk_budget_usd", "actual_net_pl_usd",
            "actual_loss_usd", "risk_budget_breached",
            "stop_gap_extra_loss_vs_planned_stop_usd",
        ])
        writer.writeheader()
        writer.writerows(rows)
    stop_rows = [r for r in rows if r["exit_reason"] == "STOP_GAP"]
    target_rows = [r for r in rows if r["exit_reason"] == "TARGET_GAP"]
    breaches = [r for r in rows if r["risk_budget_breached"]]
    print(f"Completed: {len(rows)} trades | STOP_GAP={len(stop_rows)} TARGET_GAP={len(target_rows)}")
    print(f"Risk-budget breaches: {len(breaches)} | largest actual loss: ${max((r['actual_loss_usd'] for r in rows), default=0):.2f}")
    print(f"Total extra stop-gap loss vs planned stop: ${sum(r['stop_gap_extra_loss_vs_planned_stop_usd'] for r in rows):.2f}")
    for r in sorted(breaches, key=lambda x: x["actual_loss_usd"], reverse=True)[:5]:
        print(f"  BREACH {r['symbol']} {r['exit_date']} {r['exit_reason']} loss=${r['actual_loss_usd']:.2f} budget=${r['risk_budget_usd']:.2f}")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: STOP_GAP excess is measured against a hypothetical planned-stop fill; it is not a realized alternate outcome.")
    print("NOTE: 1% risk budget is planned stop risk, not a guaranteed maximum loss.")
    print("NOTE: snapshots only; independent $2,000 accounts per stock; no live portfolio changes.")


if __name__ == "__main__":
    main()
