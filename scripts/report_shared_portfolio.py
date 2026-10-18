"""V12.1 historical shared-cash portfolio backtest; never touches live state.

Daily-bar simulation. Entries at next session open using prior close indicators.
Stops are checked before targets; simultaneous signals use alphabetical priority.
Cash is reusable on exit but same-day new entries are processed before exits,
so sale proceeds are only available for new entries on the following session.
"""
from __future__ import annotations

from pathlib import Path
import math
import pandas as pd
from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange
from core.backtest_snapshot import load_snapshot
from core.daily_backtester import risk_limited_shares

SYMBOLS = ("AAPL", "AMD", "AVGO", "NVDA", "TSLA")
START, END = "2024-10-01", "2026-10-16"


def prepared(symbol):
    df = load_snapshot(Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv"))
    d = df.copy().sort_index()
    for n in (19, 38, 209):
        d[f"MA{n}"] = SMAIndicator(d["Close"], window=n).sma_indicator()
    adx = ADXIndicator(d["High"], d["Low"], d["Close"], window=14)
    d["ADX"], d["DI+"], d["DI-"] = adx.adx(), adx.adx_pos(), adx.adx_neg()
    d["ATR"] = AverageTrueRange(d["High"], d["Low"], d["Close"], window=14).average_true_range()
    d["RVOL"] = d["Volume"] / d["Volume"].shift(1).rolling(20).mean()
    return d


def technical_signal(y):
    return bool(
        y["Close"] > y["MA19"] > y["MA38"] > y["MA209"]
        and y["ADX"] >= 20 and y["DI+"] > y["DI-"]
        and y["RVOL"] >= 1 and y["ATR"] > 0
    )


def run_portfolio(frames, capital=500.0, risk_pct=1.0, max_exposure_pct=40.0,
                  max_portfolio_risk_pct=3.0, max_positions=5,
                  commission=0.005, slippage_bps=5.0, record_daily=False, entry_priority="alphabetical"):
    if capital <= 0 or not (0 < risk_pct <= 100) or not (0 < max_exposure_pct <= 100):
        raise ValueError("Invalid capital or risk/exposure limits")
    if not (0 < max_portfolio_risk_pct <= 100) or max_positions < 1 or commission < 0 or slippage_bps < 0:
        raise ValueError("Invalid portfolio limits or execution costs")
    if entry_priority not in ("alphabetical", "reverse", "adx"):
        raise ValueError("Unknown entry priority")
    slip = slippage_bps / 10000
    symbols = sorted(frames)
    if not symbols:
        raise ValueError("No symbols")
    dates = frames[symbols[0]].index
    if len(dates) < 230 or any(not frames[s].index.equals(dates) for s in symbols):
        raise ValueError("Require aligned daily dates and at least 230 bars")
    cash = capital
    positions = {}
    trades = []
    daily = []
    diagnostics = {"signals": 0, "accepted": 0, "rejected_risk": 0,
                   "rejected_exposure": 0, "rejected_cash": 0,
                   "rejected_portfolio_risk": 0, "rejected_positions": 0}
    for i in range(209, len(dates)):
        date = str(dates[i].date())
        # Evaluate all entries first, with fixed alphabetical tie-breaking.
        if entry_priority == "reverse":
            ordered_symbols = list(reversed(symbols))
        elif entry_priority == "adx":
            # ADX from previous completed bar only; alphabetical ties.
            ordered_symbols = sorted(symbols, key=lambda s: (
                -float(frames[s].iloc[i - 1]["ADX"])
                if math.isfinite(float(frames[s].iloc[i - 1]["ADX"])) else float("inf"),
                s,
            ))
        else:
            ordered_symbols = symbols
        for symbol in ordered_symbols:
            if symbol in positions:
                continue
            y = frames[symbol].iloc[i - 1]
            if not technical_signal(y):
                continue
            diagnostics["signals"] += 1
            today = frames[symbol].iloc[i]
            reference_open = float(today["Open"])
            atr = float(y["ATR"])
            entry = reference_open * (1 + slip)
            stop = reference_open - 1.5 * atr
            target = reference_open + 3 * atr
            unit_risk = entry - stop * (1 - slip) + 2 * commission
            if not all(math.isfinite(x) for x in (entry, stop, target, unit_risk)) or entry <= 0 or unit_risk <= 0:
                diagnostics["rejected_risk"] += 1
                continue
            if len(positions) >= max_positions:
                diagnostics["rejected_positions"] += 1
                continue
            open_risk = sum(p["shares"] * p["unit_risk"] for p in positions.values())
            available_risk = max(0.0, capital * max_portfolio_risk_pct / 100 - open_risk)
            remaining_exposure = max(0.0, capital * max_exposure_pct / 100 -
                                     sum(p["shares"] * p["entry"] for p in positions.values()))
            shares_risk = risk_limited_shares(capital * risk_pct / 100, unit_risk)
            shares_portfolio = risk_limited_shares(available_risk, unit_risk)
            shares_exposure = int(remaining_exposure // entry)
            shares_cash = int(cash // (entry + commission))
            shares = min(shares_risk, shares_portfolio, shares_exposure, shares_cash)
            if shares <= 0:
                if shares_risk == 0:
                    diagnostics["rejected_risk"] += 1
                elif shares_portfolio == 0:
                    diagnostics["rejected_portfolio_risk"] += 1
                elif shares_exposure == 0:
                    diagnostics["rejected_exposure"] += 1
                else:
                    diagnostics["rejected_cash"] += 1
                continue
            positions[symbol] = {
                "symbol": symbol, "entry_date": date, "entry": entry,
                "shares": shares, "stop": stop, "target": target,
                "unit_risk": unit_risk,
            }
            cash -= shares * (entry + commission)
            diagnostics["accepted"] += 1
        # Intraday exits after entries; conservative stop-first ordering.
        for symbol in list(positions):
            today = frames[symbol].iloc[i]
            p = positions[symbol]
            op = float(today["Open"])
            if op <= p["stop"]:
                raw_exit, reason = op, "STOP_GAP"
            elif op >= p["target"]:
                raw_exit, reason = op, "TARGET_GAP"
            elif float(today["Low"]) <= p["stop"]:
                raw_exit, reason = p["stop"], "STOP"
            elif float(today["High"]) >= p["target"]:
                raw_exit, reason = p["target"], "TARGET"
            else:
                continue
            exit_fill = raw_exit * (1 - slip)
            pl = (exit_fill - p["entry"] - 2 * commission) * p["shares"]
            cash += p["shares"] * (exit_fill - commission)
            trades.append({**p, "exit_date": date, "exit": exit_fill,
                           "reason": reason, "pl": pl})
            del positions[symbol]
        if record_daily:
            marked_value = sum(
                p["shares"] * float(frames[s].iloc[i]["Close"])
                for s, p in positions.items()
            )
            daily.append({
                "date": date,
                "cash": cash,
                "position_value": marked_value,
                "equity": cash + marked_value,
                "open_positions": len(positions),
                "open_risk": sum(p["shares"] * p["unit_risk"] for p in positions.values()),
                "entry_exposure": sum(p["shares"] * p["entry"] for p in positions.values()),
            })
    # Mark open positions at final close, not their entry cost.
    equity = cash + sum(p["shares"] * float(frames[s].iloc[-1]["Close"]) for s, p in positions.items())
    return {"initial_cash": capital, "cash": cash, "equity_marked": equity,
            "trades": trades, "positions": positions, "diagnostics": diagnostics, "daily": daily}


def main():
    frames = {s: prepared(s) for s in SYMBOLS}
    result = run_portfolio(frames)
    d = result["diagnostics"]
    print("V12.1 SHARED-CAPITAL HISTORICAL PORTFOLIO")
    print("Capital=$500 | risk/trade=1% | total exposure=40% | portfolio risk=3% | max positions=5")
    print(f"signals={d['signals']} accepted={d['accepted']} closed={len(result['trades'])} open={len(result['positions'])}")
    print("rejections: " + ", ".join(f"{k}={v}" for k, v in d.items() if k.startswith("rejected_")))
    print(f"cash=${result['cash']:.2f} marked_equity=${result['equity_marked']:.2f}")
    print(f"closed_trade_P/L=${sum(t['pl'] for t in result['trades']):+.2f}")
    assert abs(result["cash"] + sum(p["entry"] * p["shares"] for p in result["positions"].values()) -
               500 - sum(t["pl"] for t in result["trades"])) < 1e-6
    assert d["signals"] == d["accepted"] + sum(v for k, v in d.items() if k.startswith("rejected_"))
    print("PASS shared cash ledger and signal accounting")
    print("NOTE: entry allocation uses alphabetical ticker priority; same-day exit cash is not reused.")
    print("NOTE: marked equity uses last adjusted close without liquidation costs; gap losses can exceed budget.")
    print("NOTE: adjusted historical prices, not a real cash-broker settlement or order simulator.")
    print("NOTE: no broker orders, live portfolio updates, or database writes.")


if __name__ == "__main__":
    main()
