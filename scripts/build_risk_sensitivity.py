"""V7 isolated risk sensitivity study: fixed $2,000 starting capital per run.

The 1% default in DailyTechnicalBacktester remains unchanged.
Each scenario is a separate simulation, not a shared portfolio.
"""
from __future__ import annotations

import csv
import html
from pathlib import Path

from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_daily_equity import daily_equity

SYMBOLS = ("TSLA", "AMD", "AVGO", "NVDA")
RISK_LEVELS = (0.5, 1.0, 1.5, 2.0)
CAPITAL = 2000.0
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUTPUT = Path("reports")


def evaluate(symbol, data, risk_pct):
    result = DailyTechnicalBacktester().run(
        data, initial_cash=CAPITAL,
        commission_per_share=COMMISSION,
        slippage_bps=SLIPPAGE_BPS,
        risk_per_trade_pct=risk_pct,
    )
    curve = daily_equity(data, result, initial_cash=CAPITAL, commission=COMMISSION)
    peak = CAPITAL
    max_dd = 0.0
    for point in curve:
        peak = max(peak, point["equity"])
        max_dd = max(max_dd, (peak - point["equity"]) / peak * 100)
    last = curve[-1]
    expected = result["realized_cash"]
    if result["open_position"]:
        expected += result["open_position"]["shares"] * (
            last["close"] - result["open_position"]["entry"]
        )
    if abs(last["equity"] - expected) > 0.000001:
        raise AssertionError(f"{symbol} at {risk_pct}%: reconciliation failed")
    d = result["diagnostics"]
    return {
        "symbol": symbol,
        "risk_pct": risk_pct,
        "signals": d["technical_signals"],
        "accepted": d["accepted_entries"],
        "rejected": d["rejected_by_risk"],
        "trade_risk_rejections": d["rejection_reasons"]["trade_risk"],
        "exposure_rejections": d["rejection_reasons"]["exposure"],
        "closed": result["closed_trades"],
        "open_shares": result["open_position"]["shares"] if result["open_position"] else 0,
        "net_pl": round(last["equity"] - CAPITAL, 2),
        "return_pct": round((last["equity"] / CAPITAL - 1) * 100, 2),
        "max_dd_pct": round(max_dd, 2),
    }


def main():
    rows = []
    for symbol in SYMBOLS:
        try:
            data = load_backtest_data(symbol)
        except Exception as exc:
            print(f"{symbol}: data error: {exc}")
            continue
        for risk_pct in RISK_LEVELS:
            try:
                row = evaluate(symbol, data, risk_pct)
                rows.append(row)
                print(
                    f"{symbol:5} risk={risk_pct:>3.1f}% "
                    f"signals={row['signals']:2} accepted={row['accepted']:2} "
                    f"rejected={row['rejected']:2} trades={row['closed']:2} "
                    f"P/L=${row['net_pl']:+.2f} DD={row['max_dd_pct']:.2f}%"
                )
            except Exception as exc:
                print(f"{symbol} risk={risk_pct}%: ERROR: {exc}")
    if not rows:
        raise RuntimeError("No risk scenarios completed")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "backtest_risk_sensitivity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    keys = list(rows[0])
    header = "".join(f"<th>{html.escape(k.replace('_',' ').title())}</th>" for k in keys)
    body = "".join("<tr>" + "".join(
        f"<td>{html.escape(str(row[k]))}</td>" for k in keys
    ) + "</tr>" for row in rows)
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradingAI-Pro | Risk Sensitivity V7</title>
<style>
:root{{color-scheme:dark;font-family:system-ui;background:#0b1220;color:#e8edf7}}
body{{max-width:1400px;margin:36px auto;padding:0 20px}}p{{color:#aab8ce}}
.panel{{background:#142036;border:1px solid #263850;border-radius:12px;padding:18px;overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:11px;text-align:right;border-bottom:1px solid #263850;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}th{{color:#aab8ce}}
</style></head><body>
<h1>TradingAI-Pro | Risk Sensitivity V7</h1>
<p>Independent technical-only simulations · $2,000 per scenario · 40% exposure cap · 5 bps slippage/side · $0.005/share commission/side</p>
<div class="panel"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>
<p>Risk percentage is a historical sensitivity parameter, not a recommendation. Stop gaps can exceed planned risk. Signals may change because time spent in positions changes. All equity values include open positions at last adjusted close.</p>
</body></html>"""
    html_path = OUTPUT / "backtest_risk_sensitivity.html"
    html_path.write_text(document, encoding="utf-8")
    print(f"Completed: {len(rows)}/{len(SYMBOLS) * len(RISK_LEVELS)} scenarios")
    print(f"HTML: {html_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")


if __name__ == "__main__":
    main()
