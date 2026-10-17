"""Independent multi-stock daily backtest comparison.

Each ticker receives its own $2,000 starting cash. This is NOT a shared
portfolio backtest. Outputs a local HTML dashboard and CSV summary.
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


def evaluate(symbol):
    data = load_backtest_data(symbol)
    result = DailyTechnicalBacktester().run(
        data, initial_cash=CAPITAL,
        commission_per_share=COMMISSION,
        slippage_bps=SLIPPAGE_BPS,
    )
    curve = daily_equity(data, result, initial_cash=CAPITAL, commission=COMMISSION)
    end = curve[-1]
    peak = CAPITAL
    drawdown = 0.0
    for point in curve:
        peak = max(peak, point["equity"])
        drawdown = max(drawdown, 100 * (peak - point["equity"]) / peak)
    expected = result["realized_cash"]
    if result["open_position"]:
        expected += result["open_position"]["shares"] * (
            end["close"] - result["open_position"]["entry"]
        )
    if abs(end["equity"] - expected) > 0.000001:
        raise AssertionError(f"{symbol}: equity reconciliation failed")
    trades = result["trades"]
    wins = [t["pl"] for t in trades if t["pl"] > 0]
    losses = [t["pl"] for t in trades if t["pl"] < 0]
    profit_factor = sum(wins) / abs(sum(losses)) if losses else (
        float("inf") if wins else None
    )
    return {
        "symbol": symbol,
        "signals": result["diagnostics"]["technical_signals"],
        "closed_trades": len(trades),
        "open_shares": result["open_position"]["shares"] if result["open_position"] else 0,
        "win_rate_pct": round(100 * len(wins) / len(trades), 2) if trades else None,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None and profit_factor != float("inf") else ("INF" if profit_factor == float("inf") else None),
        "net_pl": round(end["equity"] - CAPITAL, 2),
        "return_pct": round(100 * (end["equity"] / CAPITAL - 1), 2),
        "max_drawdown_pct": round(drawdown, 2),
        "end_equity": round(end["equity"], 2),
    }


def main():
    rows = []
    for symbol in SYMBOLS:
        try:
            row = evaluate(symbol)
            rows.append(row)
            print(f"{symbol:5} | trades={row['closed_trades']:2} | P/L=${row['net_pl']:+8.2f} | return={row['return_pct']:+6.2f}% | DD={row['max_drawdown_pct']:.2f}%")
        except Exception as exc:
            print(f"{symbol:5} | ERROR: {exc}")
    if not rows:
        raise RuntimeError("No symbols completed successfully")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    csv_path = OUTPUT / "backtest_stocks.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    headings = {
        "symbol": "Symbol", "signals": "Signals", "closed_trades": "Closed",
        "open_shares": "Open shares", "win_rate_pct": "Win %",
        "profit_factor": "Profit factor", "net_pl": "Net P/L ($)",
        "return_pct": "Return %", "max_drawdown_pct": "Max DD %",
        "end_equity": "End equity ($)",
    }
    header = "".join(f"<th>{html.escape(headings[k])}</th>" for k in fields)
    body = "".join(
        "<tr>" + "".join(
            f"<td class='{('neg' if isinstance(row[k], (int,float)) and row[k]<0 else '')}'>{html.escape(str(row[k]) if row[k] is not None else 'N/A')}</td>"
            for k in fields
        ) + "</tr>"
        for row in rows
    )
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradingAI-Pro | Multi-Stock Backtest</title>
<style>
:root{{color-scheme:dark;font-family:system-ui;background:#0b1220;color:#e8edf7}}
body{{max-width:1300px;margin:36px auto;padding:0 20px}}
p{{color:#aab8ce}}.panel{{background:#142036;border:1px solid #263850;border-radius:12px;padding:18px;overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px;text-align:right;border-bottom:1px solid #263850;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}th{{color:#aab8ce}}.neg{{color:#fb7185}}
</style></head><body><h1>TradingAI-Pro | Multi-Stock Backtesting V5</h1>
<p>Independent technical-only backtests · $2,000 per ticker · 1% risk · 5 bps slippage per side · $0.005/share commission per side</p>
<div class="panel"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>
<p>Not a combined portfolio. Open positions marked to last adjusted close; win rate and profit factor use closed trades only. N/A means no closed trades. Historical results do not predict future returns.</p>
</body></html>"""
    html_path = OUTPUT / "backtest_stocks.html"
    html_path.write_text(document, encoding="utf-8")
    print(f"Completed: {len(rows)}/{len(SYMBOLS)} symbols")
    print(f"HTML: {html_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")


if __name__ == "__main__":
    main()
