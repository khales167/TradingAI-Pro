from config import ACCOUNT_CAPITAL, RISK_PER_TRADE_PERCENT


class RiskManager:

    def __init__(
        self,
        capital=ACCOUNT_CAPITAL,
        risk_percent=RISK_PER_TRADE_PERCENT
    ):
        self.capital = capital
        self.risk_percent = risk_percent

    def calculate(
        self,
        entry,
        stop,
        target,
        available_cash=None
    ):
        if entry <= 0:
            return None

        risk_per_share = abs(entry - stop)

        if risk_per_share <= 0:
            return None

        max_loss = (
            self.capital
            * self.risk_percent
            / 100
        )

        risk_based_shares = int(
            max_loss / risk_per_share
        )

        cash = (
            self.capital
            if available_cash is None
            else max(0, available_cash)
        )

        cash_based_shares = int(
            cash / entry
        )

        shares = min(
            risk_based_shares,
            cash_based_shares
        )

        position_size = shares * entry

        reward_per_share = target - entry
        rr = reward_per_share / risk_per_share
        expected_profit = reward_per_share * shares

        return {
            "Capital": round(self.capital, 2),
            "AvailableCash": round(cash, 2),
            "RiskPercent": self.risk_percent,
            "MaxLoss": round(max_loss, 2),
            "Entry": entry,
            "Stop": stop,
            "Target": target,
            "Shares": shares,
            "PositionSize": round(position_size, 2),
            "RiskPerShare": round(risk_per_share, 2),
            "RewardPerShare": round(reward_per_share, 2),
            "RiskReward": round(rr, 2),
            "ExpectedProfit": round(expected_profit, 2)
        }
