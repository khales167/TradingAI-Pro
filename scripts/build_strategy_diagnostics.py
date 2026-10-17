"""Independent technical strategy diagnostics for the 10-stock backtest.

Each symbol has its own $2,000 simulation. No live database writes.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_daily_equity import daily_equity

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "PLTR", "META", "MSFT", "AMZN", "NFLX", "AVGO")
CAPITAL = 2000.0
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUTPUT = Path("reports")


def diagnose(symbol):
    data = load_backtest_data(symbol)
    result = DailyTechnicalBacktester().run(
        data, initial_cash=CAPITAL,
        commission_per_share=COMMISSION, slippage_bps=SLIPPAGE_BPS,
    )
    diagnostics = result["diagnostics"]
    reasons = diagnostics["rejection_reasons"]
    trades = result["trades"]
    curve = daily_equity(data, result, initial_cash=CAPITAL, commission=COMMISSION)
    last = curve[-1]
    # realized_cash adds back open-position entry notional; use it only
    # as an accounting basis for realized P/L, not as available cash.
    realized_pl = result["realized_cash"] - CAPITAL
    unrealized_pl = (
        result["open_position"]["shares"]
        * (last["close"] - result["open_position"]["entry"])
        if result["open_position"] else 0.0
    )
    total_pl = last["equity"] - CAPITAL
    if abs(realized_pl + unrealized_pl - total_pl) > 0.000001:
        raise AssertionError(f"{symbol}: P/L reconciliation failed")
    wins = [t["pl"] for t in trades if t["pl"] > 0]
    losses = [t["pl"] for t in trades if t["pl"] < 0]
    pf = (sum(wins) / abs(sum(losses))) if losses else (
        float("inf") if wins else None
    )
    return {
        "symbol": symbol,
        "signals": diagnostics["technical_signals"],
        "accepted": diagnostics["accepted_entries"],
        "rejected": diagnostics["rejected_by_risk"],
        "risk_rejections": reasons["trade_risk"],
        "exposure_rejections": reasons["exposure"],
        "cash_rejections": reasons["cash"],
        "closed": len(trades),
        "open_shares": result["open_position"]["shares"] if result["open_position"] else 0,
        "win_rate_pct": round(100 * len(wins) / len(trades), 2) if trades else None,
        "profit_factor": round(pf, 2) if pf is not None and pf != float("inf") else ("INF" if pf == float("inf") else None),
        "realized_pl": round(realized_pl, 2),
        "unrealized_pl": round(unrealized_pl, 2),
        "total_pl": round(total_pl, 2),
    }


def main():
    rows = []
    for symbol in SYMBOLS:
        try:
            row = diagnose(symbol)
            rows.append(row)
            print(
                f"{symbol:5} | signals={row['signals']:2} accepted={row['accepted']:2} "
                f"rejected={row['rejected']:2} | risk={row['risk_rejections']:2} "
                f"exposure={row['exposure_rejections']:2} cash={row['cash_rejections']:2} "
                f"| realized=${row['realized_pl']:+.2f} unrealized=${row['unrealized_pl']:+.2f}"
            )
        except Exception as exc:
            print(f"{symbol:5} | ERROR: {exc}")
    if not rows:
        raise RuntimeError("No symbols completed successfully")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "backtest_diagnostics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    fields = list(rows[0])
    headings = {
        "symbol": "Symbol", "signals": "Signals", "accepted": "Accepted",
        "rejected": "Rejected", "risk_rejections": "Trade risk",
        "exposure_rejections": "Exposure", "cash_rejections": "Cash",
        "closed": "Closed", "open_shares": "Open shares",
        "win_rate_pct": "Win %", "profit_factor": "PF",
        "realized_pl": "Realized P/L", "unrealized_pl": "Unrealized P/L",
        "total_pl": "Total P/L",
    }
    headers = "".join(f"<th>{html.escape(headings[key])}</th>" for key in fields)
    body = "".join(
        "<tr>" + "".join(
            f"<td class='{('negative' if key.endswith('_pl') and isinstance(row[key], (float, int)) and row[key] < 0 else '')}'>{html.escape(str(row[key]) if row[key] is not None else 'N/A')}</td>"
            for key in fields
        ) + "</tr>"
        for row in rows
    )
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradingAI-Pro | Strategy Diagnostics V6</title>
<style>
:root{{color-scheme:dark;font-family:system-ui;background:#0b1220;color:#e8edf7}}
body{{max-width:1500px;margin:36px auto;padding:0 20px}}
p{{color:#aab8ce}}.panel{{background:#142036;border:1px solid #263850;border-radius:12px;padding:18px;overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px;text-align:right;border-bottom:1px solid #263850;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}th{{color:#aab8ce}}.negative{{color:#fb7185}}
</style></head><body><h1>TradingAI-Pro | Strategy Diagnostics V6</h1>
<p>Technical-only independent backtests · $2,000 per symbol · 1% risk · 5 bps slippage/side · $0.005/share commission/side</p>
<div class="panel"><table><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>
<p>Rejection reasons may overlap: a rejected signal can breach several constraints. Signals count only days evaluated while flat. Realized P/L excludes open-position mark-to-market; unrealized P/L uses last adjusted close. No live database writes.</p>
</body></html>"""
    html_path = OUTPUT / "backtest_diagnostics.html"
    html_path.write_text(document, encoding="utf-8")
    print(f"Completed: {len(rows)}/{len(SYMBOLS)} symbols")
    print(f"HTML: {html_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")


if __name__ == "__main__":
    main()
