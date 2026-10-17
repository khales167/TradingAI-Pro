"""V11.1 AVGO entry-decision audit at 5 vs 10 bps.

Reconstructs the daily backtest's exact prior-day signal, risk-based whole-share
sizing, and whether a position is already open at each candidate entry.
Read-only fixed snapshot; no live portfolio or strategy changes.
"""
from pathlib import Path
import csv

import pandas as pd
from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SNAPSHOT = Path("data/backtest_snapshots/AVGO_2024-10-01_2026-10-16.csv")
OUT = Path("reports/backtest_avgo_entry_decisions.csv")
CAPITAL = 2000.0
RISK_PCT = 1.0
COMMISSION = 0.005
LEVELS = (5, 10)
FOCUS = ("2026-04-16", "2026-04-23")


def indicators(df):
    d = df.copy().sort_index()
    for n in (19, 38, 209):
        d[f"MA{n}"] = SMAIndicator(d["Close"], window=n).sma_indicator()
    a = ADXIndicator(d["High"], d["Low"], d["Close"], window=14)
    d["ADX"] = a.adx()
    d["DI+"] = a.adx_pos()
    d["DI-"] = a.adx_neg()
    d["ATR"] = AverageTrueRange(d["High"], d["Low"], d["Close"], window=14).average_true_range()
    d["RVOL"] = d["Volume"] / d["Volume"].shift(1).rolling(20).mean()
    return d


def signal(y):
    return bool(
        y["Close"] > y["MA19"] > y["MA38"] > y["MA209"]
        and y["ADX"] >= 20 and y["DI+"] > y["DI-"]
        and y["RVOL"] >= 1.0 and y["ATR"] > 0
    )


def main():
    df = load_snapshot(SNAPSHOT)
    d = indicators(df)
    results = {
        bps: DailyTechnicalBacktester().run(
            df, initial_cash=CAPITAL, risk_per_trade_pct=RISK_PCT,
            commission_per_share=COMMISSION, slippage_bps=bps,
        ) for bps in LEVELS
    }
    rows = []
    for date in FOCUS:
        matching = d.index[d.index.strftime("%Y-%m-%d") == date]
        assert len(matching) == 1, f"Missing date: {date}"
        idx = d.index.get_loc(matching[0])
        assert idx >= 209
        y = d.iloc[idx - 1]
        today = d.iloc[idx]
        technical = signal(y)
        for bps in LEVELS:
            slip = bps / 10000.0
            open_price = float(today["Open"])
            entry = open_price * (1 + slip)
            atr = float(y["ATR"])
            stop = open_price - 1.5 * atr
            target = open_price + 3 * atr
            unit_risk = entry - stop * (1 - slip) + 2 * COMMISSION
            risk_budget = CAPITAL * RISK_PCT / 100
            risk_shares = int(risk_budget // unit_risk) if unit_risk > 0 else 0
            exposure_shares = int(CAPITAL * 0.40 // entry) if entry > 0 else 0
            cash_shares = int(CAPITAL // (entry + COMMISSION)) if entry > 0 else 0
            permitted = min(risk_shares, exposure_shares, cash_shares)
            trades = results[bps]["trades"]
            accepted = [t for t in trades if t["entry_date"] == date]
            occupied = [t for t in trades if t["entry_date"] < date <= t["exit_date"]]
            open_position = results[bps]["open_position"]
            if open_position and open_position["entry_date"] < date:
                occupied.append(open_position)
            # On a day occupied by a prior position, the engine skips signal
            # evaluation even if that position exits later that same day.
            state = ("IN_POSITION" if occupied else
                     "NO_SIGNAL" if not technical else
                     "ACCEPTED" if accepted else "REJECTED")
            if state == "ACCEPTED":
                assert len(accepted) == 1
                assert int(accepted[0]["shares"]) == permitted
            if state == "REJECTED":
                assert permitted == 0, "Unexpected rejection: check engine state"
            row = {
                "date": date, "slippage_bps": bps,
                "prior_day_signal": technical,
                "position_occupied": bool(occupied),
                "decision": state,
                "open": open_price, "atr_previous_day": atr,
                "entry_fill": entry, "stop": stop, "target": target,
                "risk_per_share": unit_risk, "risk_budget": risk_budget,
                "risk_limited_shares": risk_shares,
                "exposure_limited_shares": exposure_shares,
                "cash_limited_shares_assuming_full_cash": cash_shares,
                "permitted_shares_if_flat": permitted,
            }
            rows.append(row)
            print(
                f"{date} slip={bps:2}bps decision={state:11} "
                f"signal={technical} open=${open_price:.2f} ATR=${atr:.2f} "
                f"risk/share=${unit_risk:.2f} budget=${risk_budget:.2f} "
                f"risk_shares={risk_shares} exposure_shares={exposure_shares} "
                f"shares_if_flat={permitted}"
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Completed: {len(rows)}/{len(FOCUS) * len(LEVELS)} focused decisions")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: cash sizing assumes full initial cash; the focus dates are verified against executed trades.")
    print("NOTE: in-position days are not eligible for fresh signals, even when an exit occurs that day.")
    print("NOTE: historical immutable snapshot only; no broker or live portfolio writes.")


if __name__ == "__main__":
    main()
