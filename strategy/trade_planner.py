from config import ACCOUNT_CAPITAL
from strategy.risk_manager import RiskManager


class TradePlanner:

    def __init__(self, portfolio):
        self.risk_manager = RiskManager()
        self.portfolio = portfolio

    def process_trade_plans(self, results):

        # ==========================================
        # Only BUY signals
        # ==========================================

        buys = [
            stock
            for stock in results
            if stock["Decision"].upper() == "BUY"
        ]

        # Rank candidates exactly as used by the
        # position-cap validation: Score DESC, ADX DESC.
        buys.sort(
            key=lambda stock: (
                stock.get("Score", 0),
                stock.get("ADX", 0)
            ),
            reverse=True
        )

        # ==========================================
        # Debug
        # ==========================================

        print("\n========== DEBUG RESULTS ==========")

        for stock in results:
            print(stock)

        print("\n========== BUY SIGNALS (RANKED) ==========")
        print(buys)

        # ==========================================
        # No BUY
        # ==========================================

        if not buys:
            print("\n❌ No BUY opportunities today.")
            return

        # ==========================================
        # Portfolio capacity
        # ==========================================

        risk_check = self.portfolio.portfolio_risk.can_open_new_position()
        available_slots = risk_check["available_slots"]

        if not risk_check["allowed"] or available_slots <= 0:
            print(
                "\n⛔ No portfolio slots available: "
                f"{risk_check['reason']}"
            )
            return

        # Do not waste candidate slots on symbols that
        # are already open in the portfolio.
        eligible_buys = [
            stock
            for stock in buys
            if not self.portfolio.db.position_exists(stock["Symbol"])
        ]

        print(
            f"\nPortfolio capacity: "
            f"{risk_check['open_positions']}/"
            f"{risk_check['max_positions']} open, "
            f"{available_slots} slot(s) available."
        )

        if not eligible_buys:
            print("\n⚠ All BUY signals already exist in the portfolio.")
            return

        # ==========================================
        # Trade Plans
        # ==========================================

        for stock in eligible_buys:

            if available_slots <= 0:
                print("\n⛔ Portfolio is now full. Remaining BUY signals skipped.")
                break

            invested_capital = self.portfolio.db.get_open_invested_capital()
            available_cash = max(
                0,
                ACCOUNT_CAPITAL - invested_capital
            )

            if available_cash <= 0:
                print(
                    "\n⛔ No available cash. Remaining BUY signals skipped."
                )
                break

            report = self.risk_manager.calculate(
                stock["Entry"],
                stock["Stop"],
                stock["Target"],
                available_cash=available_cash
            )

            if report is None or report["Shares"] <= 0:
                print(
                    f"\n⚠ Invalid position size for {stock['Symbol']} "
                    f"with ${available_cash:.2f} available cash."
                )
                continue

            print("\n" + "=" * 60)
            print("TRADE PLAN")
            print("=" * 60)

            print(f"Symbol          : {stock['Symbol']}")
            print(f"Quality         : {stock['Quality']}")
            print(f"Score           : {stock['Score']}")
            print(f"ADX             : {stock.get('ADX', 0)}")
            print(f"Confidence      : {stock['Confidence']}%")
            print(f"Account Capital : ${report['Capital']:.2f}")
            print(f"Invested Capital: ${invested_capital:.2f}")
            print(f"Available Cash  : ${report['AvailableCash']:.2f}")
            print(f"Max Risk        : ${report['MaxLoss']:.2f}")
            print(f"Entry           : {report['Entry']}")
            print(f"Stop            : {report['Stop']}")
            print(f"Target          : {report['Target']}")
            print(f"Risk / Share    : ${report['RiskPerShare']:.2f}")
            print(f"Shares          : {report['Shares']}")
            print(f"Position Size   : ${report['PositionSize']:.2f}")
            print(f"Risk / Reward   : {report['RiskReward']}")
            print(f"Expected Profit : ${report['ExpectedProfit']:.2f}")

            answer = input("\nAdd to Portfolio ? (Y/N): ").strip().upper()

            if answer == "Y":

                added = self.portfolio.add_position(
                    stock["Symbol"],
                    report["Shares"],
                    report["Entry"],
                    report["Stop"],
                    report["Target"]
                )

                if added:
                    available_slots -= 1
                    print(
                        "✅ Trade added to Portfolio. "
                        f"Remaining slots: {available_slots}"
                    )
                else:
                    print("⚠ Trade was not added to Portfolio.")

            else:
                print("❌ Trade skipped. Checking next ranked candidate.")
