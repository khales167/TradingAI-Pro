class RiskManager:

    def __init__(self, capital=10000, risk_percent=1):

        self.capital = capital
        self.risk_percent = risk_percent

    def calculate(self, entry, stop, target):

        max_loss = self.capital * self.risk_percent / 100

        risk_per_share = abs(entry - stop)

        if risk_per_share == 0:
            return None

        shares = int(max_loss / risk_per_share)

        position_size = shares * entry

        # Don't exceed available capital
        if position_size > self.capital:
            shares = int(self.capital / entry)
            position_size = shares * entry

        reward_per_share = target - entry

        rr = reward_per_share / risk_per_share

        expected_profit = reward_per_share * shares

        return {
            "Capital": self.capital,
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