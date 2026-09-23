import os
import tempfile
from unittest.mock import patch

from strategy.portfolio_manager import PortfolioManager
from strategy.trade_planner import TradePlanner


def main():
    print("========== TRADE PLANNER V2 INTEGRATION TEST ==========")

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "trade_planner_v2.db")

        portfolio = PortfolioManager()
        portfolio.db.db_path = db_path
        portfolio.db.create_tables()
        portfolio.portfolio_risk.db = portfolio.db

        planner = TradePlanner(portfolio)

        results = [
            {"Symbol": "TEST1", "Decision": "BUY", "Quality": "TEST", "Score": 95, "ADX": 35, "Confidence": 90, "Entry": 100, "Stop": 98, "Target": 110},
            {"Symbol": "TEST2", "Decision": "BUY", "Quality": "TEST", "Score": 90, "ADX": 32, "Confidence": 85, "Entry": 200, "Stop": 199, "Target": 205},
            {"Symbol": "TEST3", "Decision": "BUY", "Quality": "TEST", "Score": 85, "ADX": 30, "Confidence": 80, "Entry": 150, "Stop": 149, "Target": 160},
        ]

        with patch("builtins.input", return_value="Y"):
            planner.process_trade_plans(results)

        rows = portfolio.db.get_portfolio()
        positions = {row["symbol"]: row for row in rows}

        assert len(rows) == 2
        assert "TEST1" in positions
        assert "TEST2" in positions
        assert "TEST3" not in positions
        assert positions["TEST1"]["quantity"] == 2
        assert positions["TEST2"]["quantity"] == 1

        invested = portfolio.db.get_open_invested_capital()
        available = max(0, 500 - invested)
        assert invested == 400
        assert available == 100
        assert invested <= 500

        print("\n========== FINAL PORTFOLIO ==========")
        print("TEST1: 2 x $100 = $200")
        print("TEST2: 1 x $200 = $200")
        print(f"Invested: ${invested:.2f}")
        print(f"Available Cash: ${available:.2f}")

    print("\n========== RESULT ==========")
    print("PASS: TradePlanner -> RiskManager -> Portfolio -> Database integration works.")
    print("PASS: Cash-account sizing prevented TEST3 from exceeding account capital.")
    print("The test used a temporary SQLite database; the live portfolio was untouched.")


if __name__ == "__main__":
    main()
