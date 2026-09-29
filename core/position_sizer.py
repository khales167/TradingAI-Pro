from __future__ import annotations

import math

from config import (
    ACCOUNT_CAPITAL,
    MAX_OPEN_POSITIONS,
    MAX_PORTFOLIO_RISK_PERCENT,
    MAX_POSITION_EXPOSURE_PERCENT,
    RISK_PER_TRADE_PERCENT,
)


class PositionSizer:
    def calculate(self, entry: float, stop: float, summary: dict) -> dict:
        risk_per_share = max(float(entry) - float(stop), 0.0)
        risk_per_trade = ACCOUNT_CAPITAL * RISK_PER_TRADE_PERCENT / 100
        max_exposure = ACCOUNT_CAPITAL * MAX_POSITION_EXPOSURE_PERCENT / 100
        available_cash = float(summary["available_cash"])
        risk_budget_left = float(summary["risk_budget_left"])
        open_slots = int(summary["open_slots"])

        if entry <= 0 or risk_per_share <= 0 or open_slots <= 0:
            shares = 0
        else:
            by_trade_risk = math.floor(risk_per_trade / risk_per_share)
            by_portfolio_risk = math.floor(risk_budget_left / risk_per_share)
            by_cash = math.floor(available_cash / entry)
            by_exposure = math.floor(max_exposure / entry)
            shares = max(0, min(by_trade_risk, by_portfolio_risk, by_cash, by_exposure))

        position_value = round(shares * entry, 2)
        position_risk = round(shares * risk_per_share, 2)
        constraints = []

        if open_slots <= 0:
            constraints.append(f"Max open positions reached ({MAX_OPEN_POSITIONS})")
        if entry > max_exposure:
            constraints.append(f"One share costs ${entry:.2f}, above ${max_exposure:.2f} exposure cap")
        if entry > available_cash:
            constraints.append(f"One share costs ${entry:.2f}, above ${available_cash:.2f} available cash")
        if risk_per_share > risk_per_trade:
            constraints.append(f"Risk/share ${risk_per_share:.2f} exceeds ${risk_per_trade:.2f} trade-risk budget")
        if risk_per_share > risk_budget_left:
            constraints.append(f"Risk/share ${risk_per_share:.2f} exceeds ${risk_budget_left:.2f} portfolio-risk budget left")

        return {
            "Shares": shares,
            "PositionValue": position_value,
            "PositionRisk": position_risk,
            "RiskPerShare": round(risk_per_share, 2),
            "RiskPerTradeMax": round(risk_per_trade, 2),
            "ExposureMax": round(max_exposure, 2),
            "Eligible": shares > 0,
            "SizingReasons": "; ".join(constraints),
        }
