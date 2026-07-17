class PositionManager:

    def __init__(self, capital=10000, risk_percent=1):

        self.capital = capital
        self.risk_percent = risk_percent

    def calculate(self, risk):

        risk_amount = self.capital * self.risk_percent / 100

        risk_per_share = risk["Risk"]

        if risk_per_share <= 0:
            shares = 0
        else:
            shares = int(risk_amount / risk_per_share)

        position_value = round(
            shares * risk["Entry"],
            2
        )

        return {

            "Capital": self.capital,
            "RiskAmount": round(risk_amount, 2),
            "Shares": shares,
            "PositionValue": position_value

        }