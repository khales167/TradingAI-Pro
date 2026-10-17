"""Generate an offline NVDA equity/drawdown dashboard (no extra dependencies).

Outputs are written to reports/backtest_equity.html and .csv.
No live trading database is accessed.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester
from scripts.report_daily_equity import daily_equity

CAPITAL = 2000.0
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0
OUTPUT = Path("reports")


def main():
    data = load_backtest_data("NVDA")
    result = DailyTechnicalBacktester().run(
        data, initial_cash=CAPITAL,
        commission_per_share=COMMISSION, slippage_bps=SLIPPAGE_BPS
    )
    curve = daily_equity(data, result, initial_cash=CAPITAL, commission=COMMISSION)
    peak = CAPITAL
    for point in curve:
        peak = max(peak, point["equity"])
        point["drawdown_pct"] = 100 * (point["equity"] / peak - 1)
    end = curve[-1]
    expected = result["realized_cash"]
    if result["open_position"]:
        expected += result["open_position"]["shares"] * (
            end["close"] - result["open_position"]["entry"]
        )
    if abs(end["equity"] - expected) > 0.000001:
        raise AssertionError("Equity and trade ledger do not reconcile")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "backtest_equity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "date", "cash", "shares", "close", "equity", "drawdown_pct"
        ])
        writer.writeheader()
        writer.writerows(curve)
    points = json.dumps([{
        "date": p["date"],
        "equity": round(p["equity"], 4),
        "drawdown": round(p["drawdown_pct"], 4),
    } for p in curve])
    max_dd = abs(min(p["drawdown_pct"] for p in curve))
    pnl = end["equity"] - CAPITAL
    html = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TradingAI-Pro | Backtest Equity</title>
<style>
:root{color-scheme:dark;font-family:system-ui,Arial;background:#0b1220;color:#e8edf7}
body{max-width:1100px;margin:30px auto;padding:0 18px}
h1{margin-bottom:4px}p{color:#aab8ce}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:24px 0}
.stat,.panel{background:#142036;border:1px solid #263850;border-radius:12px;padding:18px}
.stat small{display:block;color:#aab8ce}.stat strong{font-size:24px}
.panel{margin:16px 0}canvas{width:100%;height:280px;display:block}
.negative{color:#fb7185}footer{font-size:13px;color:#aab8ce;margin:25px 0}
</style></head><body>
<h1>TradingAI-Pro | Daily Backtest Equity</h1>
<p>NVDA · Technical-only · $2,000 initial · 1% risk · 5 bps/side · $0.005/share/side</p>
<div class="stats">
<div class="stat"><small>End equity</small><strong id="equity"></strong></div>
<div class="stat"><small>Net P/L</small><strong id="pnl"></strong></div>
<div class="stat"><small>Return</small><strong id="ret"></strong></div>
<div class="stat"><small>Max daily drawdown</small><strong id="dd"></strong></div>
<div class="stat"><small>Closed trades</small><strong id="trades"></strong></div>
</div>
<div class="panel"><h2>Daily Equity Curve</h2><canvas id="equityChart" role="img" aria-label="Daily equity curve"></canvas></div>
<div class="panel"><h2>Drawdown from running peak (%)</h2><canvas id="ddChart" role="img" aria-label="Daily drawdown curve"></canvas></div>
<footer>End-of-day mark-to-market; adjusted OHLC; excludes spread and intraday drawdown. This is not a live portfolio.</footer>
<script>
const data=__POINTS__;
const initial=__CAPITAL__, trades=__TRADES__;
const usd=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(n);
const last=data[data.length-1], pnl=last.equity-initial;
document.getElementById("equity").textContent=usd(last.equity);
document.getElementById("pnl").textContent=usd(pnl);
document.getElementById("ret").textContent=(pnl/initial*100).toFixed(2)+"%";
document.getElementById("dd").textContent=Math.abs(Math.min(...data.map(p=>p.drawdown))).toFixed(2)+"%";
document.getElementById("trades").textContent=trades;
if(pnl<0){document.getElementById("pnl").classList.add("negative");document.getElementById("ret").classList.add("negative")}
function plot(id,key,color,baseline){
 const canvas=document.getElementById(id), dpr=window.devicePixelRatio||1;
 const width=Math.max(300,canvas.clientWidth),height=280;
 canvas.width=width*dpr;canvas.height=height*dpr;
 const ctx=canvas.getContext("2d");ctx.scale(dpr,dpr);
 const pad={left:62,right:16,top:20,bottom:32},w=width-pad.left-pad.right,h=height-pad.top-pad.bottom;
 const values=data.map(p=>p[key]);
 let lo=Math.min(...values,baseline),hi=Math.max(...values,baseline);
 if(hi===lo){lo-=1;hi+=1}
 const margin=(hi-lo)*.08;lo-=margin;hi+=margin;
 const x=i=>pad.left+i*w/(data.length-1), y=v=>pad.top+(hi-v)*h/(hi-lo);
 ctx.font="12px system-ui";ctx.textAlign="right";ctx.textBaseline="middle";
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i,yy=y(v);
  ctx.strokeStyle="#263850";ctx.beginPath();ctx.moveTo(pad.left,yy);ctx.lineTo(width-pad.right,yy);ctx.stroke();
  ctx.fillStyle="#aab8ce";ctx.fillText(key==="equity"?"$"+v.toFixed(0):v.toFixed(1)+"%",pad.left-8,yy);
 }
 ctx.setLineDash([5,4]);ctx.strokeStyle="#8390a8";ctx.beginPath();
 ctx.moveTo(pad.left,y(baseline));ctx.lineTo(width-pad.right,y(baseline));ctx.stroke();ctx.setLineDash([]);
 ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();
 values.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.stroke();
 ctx.fillStyle="#aab8ce";ctx.textAlign="left";ctx.fillText(data[0].date,pad.left,height-8);
 ctx.textAlign="right";ctx.fillText(data[data.length-1].date,width-pad.right,height-8);
}
function render(){plot("equityChart","equity","#60a5fa",initial);plot("ddChart","drawdown","#fb7185",0)}
window.addEventListener("resize",render);render();
</script></body></html>"""
    html = (html.replace("__POINTS__", points)
                .replace("__CAPITAL__", str(CAPITAL))
                .replace("__TRADES__", str(result["closed_trades"])))
    html_path = OUTPUT / "backtest_equity.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"PASS: equity reconciles | End equity: ${end['equity']:.2f}")
    print(f"Net P/L: ${pnl:+.2f} | Max daily drawdown: {max_dd:.2f}%")
    print(f"HTML: {html_path.resolve()}")
    print(f"CSV:  {csv_path.resolve()}")


if __name__ == "__main__":
    main()
