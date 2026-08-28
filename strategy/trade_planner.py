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

        # ==========================================
        # Debug
        # ==========================================

        print("\n========== DEBUG RESULTS ==========")

        for stock in results:
            print(stock)

        print("\n========== BUY SIGNALS ==========")
        print(buys)

        # ==========================================
        # No BUY
        # ==========================================

        if not buys:
            print("\n❌ No BUY opportunities today.")
            return

        # ==========================================
        # Trade Plans
        # ==========================================

        for stock in buys:

            report = self.risk_manager.calculate(
                stock["Entry"],
                stock["Stop"],
                stock["Target"]
            )

            if report["Shares"] <= 0:
                print(f"\n⚠ Invalid position size for {stock['Symbol']}")
                continue

            print("\n" + "=" * 60)
            print("TRADE PLAN")
            print("=" * 60)

            print(f"Symbol          : {stock['Symbol']}")
            print(f"Quality         : {stock['Quality']}")
            print(f"Score           : {stock['Score']}")
            print(f"Confidence      : {stock['Confidence']}%")
            print(f"Entry           : {report['Entry']}")
            print(f"Stop            : {report['Stop']}")
            print(f"Target          : {report['Target']}")
            print(f"Shares          : {report['Shares']}")
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
                    print("✅ Trade added to Portfolio.")
                else:
                    print("⚠ Trade already exists.")

            else:
                print("❌ Trade skipped.")