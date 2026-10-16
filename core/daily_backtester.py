"""Daily technical-only backtest. No live orders or portfolio writes."""
from __future__ import annotations

import pandas as pd
from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange


class DailyTechnicalBacktester:
    def run(self, df: pd.DataFrame, initial_cash: float = 500.0) -> dict:
        if df is None or len(df) < 230:
            raise ValueError("At least 230 daily OHLCV rows are required")
        data = df.copy().sort_index()
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if col not in data:
                raise ValueError(f"Missing {col}")
            data[col] = pd.to_numeric(data[col], errors="coerce")
        data = data.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        close, high, low = data["Close"], data["High"], data["Low"]
        for window in (19, 38, 209):
            data[f"MA{window}"] = SMAIndicator(close, window=window).sma_indicator()
        dmi = ADXIndicator(high, low, close, window=14)
        data["ADX"] = dmi.adx()
        data["DI+"] = dmi.adx_pos()
        data["DI-"] = dmi.adx_neg()
        data["ATR"] = AverageTrueRange(high, low, close, window=14).average_true_range()
        data["RVOL"] = data["Volume"] / data["Volume"].shift(1).rolling(20).mean()
        cash = float(initial_cash)
        trades = []
        position = None
        diagnostics = {"evaluated_bars": 0, "technical_signals": 0, "accepted_entries": 0, "rejected_by_risk": 0, "rejection_reasons": {"trade_risk": 0, "exposure": 0, "cash": 0}, "sample_rejections": []}
        for i in range(209, len(data)):
            today = data.iloc[i]
            yesterday = data.iloc[i - 1]
            if position is None:
                diagnostics["evaluated_bars"] += 1
                signal = (
                    yesterday["Close"] > yesterday["MA19"] > yesterday["MA38"] > yesterday["MA209"]
                    and yesterday["ADX"] >= 20
                    and yesterday["DI+"] > yesterday["DI-"]
                    and yesterday["RVOL"] >= 1.0
                    and yesterday["ATR"] > 0
                )
                if signal:
                    diagnostics["technical_signals"] += 1
                    entry = float(today["Open"])
                    risk = 1.5 * float(yesterday["ATR"])
                    shares = min(
                        int((initial_cash * 0.01) // risk),
                        int((initial_cash * 0.40) // entry),
                        int(cash // entry),
                    ) if entry > 0 and risk > 0 else 0
                    if shares:
                        diagnostics["accepted_entries"] += 1
                        position = {
                            "entry_date": str(data.index[i].date()),
                            "entry": entry,
                            "shares": shares,
                            "stop": entry - risk,
                            "target": entry + 2 * risk,
                        }
                        cash -= entry * shares
                    else:
                        diagnostics["rejected_by_risk"] += 1
                        reasons = []
                        if risk > initial_cash * 0.01:
                            reasons.append("trade_risk")
                        if entry > initial_cash * 0.40:
                            reasons.append("exposure")
                        if entry > cash:
                            reasons.append("cash")
                        for reason in reasons:
                            diagnostics["rejection_reasons"][reason] += 1
                        if len(diagnostics["sample_rejections"]) < 5:
                            diagnostics["sample_rejections"].append({"date": str(data.index[i].date()), "entry": round(entry, 2), "risk_per_share": round(risk, 2), "reasons": reasons})
            if position is not None:
                stop, target = position["stop"], position["target"]
                if today["Open"] <= stop:
                    exit_price, reason = float(today["Open"]), "STOP_GAP"
                elif today["Open"] >= target:
                    exit_price, reason = float(today["Open"]), "TARGET_GAP"
                elif today["Low"] <= stop:
                    exit_price, reason = stop, "STOP"
                elif today["High"] >= target:
                    exit_price, reason = target, "TARGET"
                else:
                    continue
                cash += position["shares"] * exit_price
                trades.append({
                    **position,
                    "exit_date": str(data.index[i].date()),
                    "exit": round(exit_price, 2),
                    "reason": reason,
                    "pl": round((exit_price - position["entry"]) * position["shares"], 2),
                })
                position = None
        return {
            "diagnostics": diagnostics,
            "initial_cash": initial_cash,
            "realized_cash": round(cash + (position["entry"] * position["shares"] if position else 0), 2),
            "closed_trades": len(trades),
            "trades": trades,
            "open_position": position,
            "note": "Technical-only; excludes news, commissions, spreads, and unrealized P/L",
        }
