from config import (
    ACCOUNT_CAPITAL,
    MAX_OPEN_POSITIONS,
    MAX_PORTFOLIO_RISK_PERCENT,
    MAX_POSITION_EXPOSURE_PERCENT,
)


class PortfolioRiskDashboard:

    def __init__(self, database):
        self.db = database

    def get_summary(self):
        invested = self.db.get_open_invested_capital()
        available_cash = max(0.0, ACCOUNT_CAPITAL - invested)

        current_risk = self.db.get_open_portfolio_risk()
        max_portfolio_risk = (
            ACCOUNT_CAPITAL
            * MAX_PORTFOLIO_RISK_PERCENT
            / 100
        )
        risk_budget_left = max(
            0.0,
            max_portfolio_risk - current_risk
        )

        open_positions = self.db.get_open_positions_count()
        open_slots = max(
            0,
            MAX_OPEN_POSITIONS - open_positions
        )

        max_position_exposure = (
            ACCOUNT_CAPITAL
            * MAX_POSITION_EXPOSURE_PERCENT
            / 100
        )

        positions = []

        for position in self.db.get_portfolio():
            position_value = (
                position["quantity"]
                * position["entry_price"]
            )

            exposure_percent = (
                (position_value / ACCOUNT_CAPITAL) * 100
                if ACCOUNT_CAPITAL > 0
                else 0.0
            )

            positions.append({
                "symbol": position["symbol"],
                "quantity": position["quantity"],
                "entry_price": round(
                    float(position["entry_price"]),
                    2
                ),
                "position_value": round(
                    float(position_value),
                    2
                ),
                "exposure_percent": round(
                    float(exposure_percent),
                    2
                ),
            })

        return {
            "account_capital": round(
                float(ACCOUNT_CAPITAL),
                2
            ),
            "invested_capital": round(
                float(invested),
                2
            ),
            "available_cash": round(
                float(available_cash),
                2
            ),
            "current_portfolio_risk": round(
                float(current_risk),
                2
            ),
            "max_portfolio_risk": round(
                float(max_portfolio_risk),
                2
            ),
            "risk_budget_left": round(
                float(risk_budget_left),
                2
            ),
            "open_positions": open_positions,
            "max_open_positions": MAX_OPEN_POSITIONS,
            "open_slots": open_slots,
            "max_position_exposure_percent": (
                MAX_POSITION_EXPOSURE_PERCENT
            ),
            "max_position_exposure": round(
                float(max_position_exposure),
                2
            ),
            "positions": positions,
        }


    def display(self):
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("              PORTFOLIO RISK DASHBOARD")
        print("=" * 60)

        print(
            f"Account Capital        : "
            f"${summary['account_capital']:.2f}"
        )
        print(
            f"Invested Capital       : "
            f"${summary['invested_capital']:.2f}"
        )
        print(
            f"Available Cash         : "
            f"${summary['available_cash']:.2f}"
        )

        print("-" * 60)

        print(
            f"Current Portfolio Risk : "
            f"${summary['current_portfolio_risk']:.2f}"
        )
        print(
            f"Max Portfolio Risk     : "
            f"${summary['max_portfolio_risk']:.2f}"
        )
        print(
            f"Risk Budget Left       : "
            f"${summary['risk_budget_left']:.2f}"
        )

        print("-" * 60)

        print(
            f"Open Positions         : "
            f"{summary['open_positions']} / "
            f"{summary['max_open_positions']}"
        )
        print(
            f"Open Slots             : "
            f"{summary['open_slots']}"
        )
        print(
            f"Max Position Exposure  : "
            f"${summary['max_position_exposure']:.2f} "
            f"({summary['max_position_exposure_percent']:.1f}%)"
        )

        print("-" * 60)

        if not summary["positions"]:
            print("No open positions.")
        else:
            print(
                f"{'SYMBOL':<10}"
                f"{'QTY':>8}"
                f"{'ENTRY':>12}"
                f"{'VALUE':>14}"
                f"{'EXPOSURE':>12}"
            )
            print("-" * 60)

            for position in summary["positions"]:
                print(
                    f"{position['symbol']:<10}"
                    f"{position['quantity']:>8}"
                    f"{position['entry_price']:>12.2f}"
                    f"{position['position_value']:>14.2f}"
                    f"{position['exposure_percent']:>11.2f}%"
                )

        print("=" * 60)

        return summary
