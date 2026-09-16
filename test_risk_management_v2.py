import os
import tempfile

from core.database import DatabaseManager
from strategy.risk_manager import RiskManager


ACCOUNT_CAPITAL = 500
RISK_PERCENT = 1.0


def main():
    print("========== RISK MANAGEMENT V2 TEST ==========")

    with tempfile.TemporaryDirectory() as temp_dir:
        db = DatabaseManager()
        db.db_path = os.path.join(temp_dir, "risk_v2_test.db")
        db.create_tables()

        risk = RiskManager(
            capital=ACCOUNT_CAPITAL,
            risk_percent=RISK_PERCENT
        )

        # 1) Empty portfolio
        invested = db.get_open_invested_capital()
        available = max(0, ACCOUNT_CAPITAL - invested)
        assert invested == 0
        assert available == 500

        report = risk.calculate(100, 98, 110, available_cash=available)
        assert report is not None
        assert report["MaxLoss"] == 5.0
        assert report["Shares"] == 2
        assert report["PositionSize"] == 200

        print(
            f"Empty portfolio -> Invested: ${invested:.2f} | "
            f"Available: ${available:.2f} | Shares: {report['Shares']}"
        )

        # 2) Add a $200 open position
        added = db.add_position(
            symbol="TEST1",
            quantity=2,
            entry_price=100,
            stop_price=98,
            target_price=110,
            entry_date="2026-09-16 00:00:00"
        )
        assert added is True

        invested = db.get_open_invested_capital()
        available = max(0, ACCOUNT_CAPITAL - invested)
        assert invested == 200
        assert available == 300

        print(
            f"After TEST1    -> Invested: ${invested:.2f} | "
            f"Available: ${available:.2f}"
        )

        # 3) Cash must cap risk-based sizing.
        # Risk allows 5 shares because risk/share = $1,
        # but $300 cash at $200/share only allows 1 share.
        report = risk.calculate(200, 199, 205, available_cash=available)
        assert report is not None
        assert report["Shares"] == 1
        assert report["PositionSize"] == 200

        print(
            f"Cash cap test  -> Risk-based max: 5 shares | "
            f"Cash-based result: {report['Shares']} share"
        )

        # 4) Add the cash-capped position and verify remaining cash.
        added = db.add_position(
            symbol="TEST2",
            quantity=report["Shares"],
            entry_price=200,
            stop_price=199,
            target_price=205,
            entry_date="2026-09-16 00:01:00"
        )
        assert added is True

        invested = db.get_open_invested_capital()
        available = max(0, ACCOUNT_CAPITAL - invested)
        assert invested == 400
        assert available == 100

        print(
            f"After TEST2    -> Invested: ${invested:.2f} | "
            f"Available: ${available:.2f}"
        )

        # 5) A share costing more than remaining cash must be rejected by sizing.
        report = risk.calculate(150, 149, 160, available_cash=available)
        assert report is not None
        assert report["Shares"] == 0
        assert report["PositionSize"] == 0

        print(
            f"No-margin test -> Available: ${available:.2f} | "
            f"Entry: $150.00 | Shares: {report['Shares']}"
        )

        # The temporary DB must never show invested capital above the account.
        assert db.get_open_invested_capital() <= ACCOUNT_CAPITAL

    print("\n========== RESULT ==========")
    print("PASS: Risk sizing and cash-account limits are enforced correctly.")
    print("The test used a temporary SQLite database; the live portfolio was untouched.")


if __name__ == "__main__":
    main()
