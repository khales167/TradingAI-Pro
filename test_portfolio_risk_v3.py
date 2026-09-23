import tempfile
from pathlib import Path

from config import ACCOUNT_CAPITAL, MAX_PORTFOLIO_RISK_PERCENT
from core.database import DatabaseManager


def main():
    print("\n========== PORTFOLIO RISK V3 TEST ==========")

    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager()
        db.db_path = str(Path(tmp) / "risk_v3_test.db")
        db.create_tables()

        max_portfolio_risk = (
            ACCOUNT_CAPITAL * MAX_PORTFOLIO_RISK_PERCENT / 100
        )

        print(f"Account Capital       : ${ACCOUNT_CAPITAL:.2f}")
        print(f"Max Portfolio Risk    : ${max_portfolio_risk:.2f}")

        assert max_portfolio_risk == 15.0
        assert db.get_open_portfolio_risk() == 0.0
        assert db.get_open_initial_portfolio_risk() == 0.0

        # TEST1: 2 shares, $2 risk/share => $4 risk.
        assert db.add_position(
            "TEST1", 2, 100, 98, 110, "2026-09-23 12:00:00"
        )

        # TEST2: 3 shares, $2 risk/share => $6 risk.
        assert db.add_position(
            "TEST2", 3, 50, 48, 60, "2026-09-23 12:01:00"
        )

        current_risk = db.get_open_portfolio_risk()
        initial_risk = db.get_open_initial_portfolio_risk()
        remaining = max_portfolio_risk - current_risk

        print("\nAfter TEST1 + TEST2")
        print(f"Current Risk          : ${current_risk:.2f}")
        print(f"Initial Risk          : ${initial_risk:.2f}")
        print(f"Remaining Risk Budget : ${remaining:.2f}")

        assert current_risk == 10.0
        assert initial_risk == 10.0
        assert remaining == 5.0

        # Break-even TEST1: current downside risk falls to zero,
        # while initial risk must remain unchanged.
        db.activate_break_even("TEST1", 100)

        current_risk = db.get_open_portfolio_risk()
        initial_risk = db.get_open_initial_portfolio_risk()
        remaining = max_portfolio_risk - current_risk

        print("\nAfter TEST1 Break-Even")
        print(f"Current Risk          : ${current_risk:.2f}")
        print(f"Initial Risk          : ${initial_risk:.2f}")
        print(f"Remaining Risk Budget : ${remaining:.2f}")

        assert current_risk == 6.0
        assert initial_risk == 10.0
        assert remaining == 9.0

        # A trailing stop above entry must never create negative risk.
        db.update_stop("TEST1", 103)

        current_risk = db.get_open_portfolio_risk()
        initial_risk = db.get_open_initial_portfolio_risk()

        print("\nAfter TEST1 Trailing Stop Above Entry")
        print(f"Current Risk          : ${current_risk:.2f}")
        print(f"Initial Risk          : ${initial_risk:.2f}")

        assert current_risk == 6.0
        assert initial_risk == 10.0

        print("\n========== RESULT ==========")
        print("PASS: Portfolio risk calculations are correct.")
        print("PASS: Break-even releases current risk budget.")
        print("PASS: Initial risk remains preserved.")
        print("PASS: Stops above entry never create negative risk.")
        print("The test used a temporary SQLite database; the live portfolio was untouched.")


if __name__ == "__main__":
    main()
