import tempfile
from datetime import datetime
from pathlib import Path

from core.database import DatabaseManager
from core.portfolio_risk_dashboard import PortfolioRiskDashboard


def main():
    print("\n========== PORTFOLIO RISK DASHBOARD V5 TEST ==========")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = DatabaseManager()
        db.db_path = str(Path(tmpdir) / "dashboard_v5.db")
        db.create_tables()

        dashboard = PortfolioRiskDashboard(db)

        empty = dashboard.get_summary()

        print("\nEmpty portfolio")
        print(f"Capital              : ${empty['account_capital']:.2f}")
        print(f"Invested             : ${empty['invested_capital']:.2f}")
        print(f"Available Cash       : ${empty['available_cash']:.2f}")
        print(f"Current Risk         : ${empty['current_portfolio_risk']:.2f}")
        print(f"Risk Budget Left     : ${empty['risk_budget_left']:.2f}")
        print(
            f"Open Positions       : "
            f"{empty['open_positions']}/{empty['max_open_positions']}"
        )
        print(f"Open Slots           : {empty['open_slots']}")
        print(
            f"Max Position Exposure: "
            f"${empty['max_position_exposure']:.2f}"
        )

        assert empty["account_capital"] == 500.0
        assert empty["invested_capital"] == 0.0
        assert empty["available_cash"] == 500.0
        assert empty["current_portfolio_risk"] == 0.0
        assert empty["max_portfolio_risk"] == 15.0
        assert empty["risk_budget_left"] == 15.0
        assert empty["open_positions"] == 0
        assert empty["max_open_positions"] == 5
        assert empty["open_slots"] == 5
        assert empty["max_position_exposure"] == 200.0
        assert empty["positions"] == []

        db.add_position(
            symbol="TEST1",
            quantity=2,
            entry_price=100,
            stop_price=98,
            target_price=110,
            entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        db.add_position(
            symbol="TEST2",
            quantity=2,
            entry_price=50,
            stop_price=48,
            target_price=60,
            entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        summary = dashboard.get_summary()

        print("\nAfter TEST1 + TEST2")
        print(f"Invested             : ${summary['invested_capital']:.2f}")
        print(f"Available Cash       : ${summary['available_cash']:.2f}")
        print(f"Current Risk         : ${summary['current_portfolio_risk']:.2f}")
        print(f"Risk Budget Left     : ${summary['risk_budget_left']:.2f}")
        print(
            f"Open Positions       : "
            f"{summary['open_positions']}/{summary['max_open_positions']}"
        )
        print(f"Open Slots           : {summary['open_slots']}")

        assert summary["invested_capital"] == 300.0
        assert summary["available_cash"] == 200.0
        assert summary["current_portfolio_risk"] == 8.0
        assert summary["risk_budget_left"] == 7.0
        assert summary["open_positions"] == 2
        assert summary["open_slots"] == 3

        by_symbol = {
            p["symbol"]: p
            for p in summary["positions"]
        }

        assert by_symbol["TEST1"]["position_value"] == 200.0
        assert by_symbol["TEST1"]["exposure_percent"] == 40.0
        assert by_symbol["TEST2"]["position_value"] == 100.0
        assert by_symbol["TEST2"]["exposure_percent"] == 20.0

        db.activate_break_even("TEST1", 100)

        after_be = dashboard.get_summary()

        print("\nAfter TEST1 break-even")
        print(
            f"Current Risk         : "
            f"${after_be['current_portfolio_risk']:.2f}"
        )
        print(
            f"Risk Budget Left     : "
            f"${after_be['risk_budget_left']:.2f}"
        )

        assert after_be["current_portfolio_risk"] == 4.0
        assert after_be["risk_budget_left"] == 11.0

        print("\n========== RESULT ==========")
        print("PASS: Dashboard summary matches V2/V3/V4 risk state.")
        print("PASS: Cash, portfolio risk, slots and exposure are correct.")
        print("PASS: Break-even releases dashboard risk budget.")
        print(
            "The test used a temporary SQLite database; "
            "the live portfolio was untouched."
        )


if __name__ == "__main__":
    main()
