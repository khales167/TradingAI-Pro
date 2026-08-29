import tempfile
from pathlib import Path

from config import MAX_OPEN_POSITIONS
from strategy.portfolio_manager import PortfolioManager


TEST_SYMBOLS = ["TEST1", "TEST2", "TEST3", "TEST4", "TEST5", "TEST6"]


def main():
    """Verify that five positions are accepted and the sixth is rejected."""

    with tempfile.TemporaryDirectory() as temp_dir:
        portfolio = PortfolioManager()

        # Redirect this test to an isolated SQLite database.
        # The real database/trading_ai.db is never touched.
        portfolio.db.db_path = str(Path(temp_dir) / "position_cap_test.db")
        portfolio.db.create_tables()

        print("\n========== LIVE POSITION CAP TEST ==========")
        print(f"Configured MAX_OPEN_POSITIONS: {MAX_OPEN_POSITIONS}\n")

        results = []

        for index, symbol in enumerate(TEST_SYMBOLS, start=1):
            added = portfolio.add_position(
                symbol=symbol,
                quantity=1,
                entry_price=100.0,
                stop_price=95.0,
                target_price=110.0,
            )

            open_count = portfolio.db.get_open_positions_count()
            results.append((symbol, added, open_count))

            status = "ACCEPTED" if added else "REJECTED"
            print(
                f"Attempt {index}: {symbol:<6} -> {status:<8} "
                f"| Open positions: {open_count}/{MAX_OPEN_POSITIONS}"
            )

        first_five_accepted = all(added for _, added, _ in results[:5])
        sixth_rejected = results[5][1] is False
        final_count_correct = portfolio.db.get_open_positions_count() == MAX_OPEN_POSITIONS

        print("\n========== RESULT ==========")

        if first_five_accepted and sixth_rejected and final_count_correct:
            print("PASS: Position cap is enforced correctly.")
            print("The first 5 positions were accepted and position 6 was rejected.")
            return

        print("FAIL: Position cap behavior is not correct.")
        print(f"Results: {results}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
