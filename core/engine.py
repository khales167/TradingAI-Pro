from datetime import datetime
from core.database import DatabaseManager
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
import time

from scanner.watchlist_manager import WatchlistManager

from strategy.trade_planner import TradePlanner

from core.data_manager import DataManager
from core.analyzer import Analyzer
from core.decision import DecisionEngine
from core.trade_levels import TradeLevels
from core.ranking import RankingEngine
from core.report import ReportGenerator
from core.scanner_engine import ScannerEngine

from market.sentiment import MarketSentiment
from strategy.risk_manager import RiskManager

from strategy.portfolio_manager import PortfolioManager

from core.portfolio_monitor import PortfolioMonitor



class TradingEngine:

    def __init__(self):

        self.results = []

        self.watchlists = WatchlistManager()

        self.data_manager = DataManager()
        self.analyzer = Analyzer()
        self.decision = DecisionEngine()
        self.trade_levels = TradeLevels()
        self.risk_manager = RiskManager()
        

        self.ranking = RankingEngine()
        self.report = ReportGenerator()

        self.database = DatabaseManager()

        self.portfolio = PortfolioManager()
        self.monitor = PortfolioMonitor()

        self.trade_planner = TradePlanner(self.portfolio)

        self.market = MarketSentiment()

        self.scanner = ScannerEngine(
            self.data_manager,
            self.analyzer,
            self.decision,
            self.trade_levels
        )

    def run(self):

        print("=" * 80)
        print("                 TRADING AI PRO V2.5 STABLE")
        print("=" * 80)

        # -----------------------------
        # Market Sentiment
        # -----------------------------

        market = self.market.analyze()

        print("\nMARKET SENTIMENT")
        print("-" * 40)

        for key, value in market.items():
            print(f"{key:<10}: {value}")

        # -----------------------------
        # Watchlists
        # -----------------------------

        print("\nAVAILABLE WATCHLISTS")
        print("-" * 40)

        watchlists = self.watchlists.get_available()

        if not watchlists:
            print("No watchlists available.")
            return

        for index, name in enumerate(watchlists, start=1):
            print(f"{index}. {name}")

        while True:

            try:

                choice = int(input("\nSelect Watchlist : "))

                if 1 <= choice <= len(watchlists):
                    break

                print("Invalid selection.")

            except ValueError:

                print("Enter a valid number.")

        selected = watchlists[choice - 1]

        symbols = self.watchlists.load(selected)

        print(f"\nLoaded : {selected}")
        print(f"Scanning {len(symbols)} symbols...\n")

        self.results.clear()

        start = time.perf_counter()

        workers = min(8, len(symbols))

        with ThreadPoolExecutor(max_workers=workers) as executor:

            results = executor.map(
                self.scanner.scan_symbol,
                symbols,
                repeat(market)
            )

            for stock in results:

                if stock is not None:
                    self.results.append(stock)

        elapsed = time.perf_counter() - start

        
        # ----------------------------------------
        # Remove None results
        # ----------------------------------------

        self.results = [
            stock for stock in self.results
            if stock is not None
        ]

        # ----------------------------------------
        # Ranking
        # ----------------------------------------

        self.results = self.ranking.rank(self.results)

        # ----------------------------------------
        # Display Results
        # ----------------------------------------
        print("BEFORE DISPLAY:", len(self.results))
        self.display_results()
        print("AFTER DISPLAY:", len(self.results))
        print("\n========== DEBUG ENGINE ==========")
        print(type(self.results))
        print(len(self.results))

        if len(self.results) > 0:
           print(self.results[0])
        self.trade_planner.process_trade_plans(self.results)

        # ----------------------------------------
        # Performance
        # ----------------------------------------

        print("\n" + "=" * 80)
        print(f"Scan completed in : {elapsed:.2f} seconds")
        print(f"Symbols scanned   : {len(self.results)}")
        print(f"Threads used      : {workers}")
        print("=" * 80)
        # ----------------------------------------
# Performance Summary
# ----------------------------------------

        performance = self.database.get_performance_summary()

        print("\n" + "=" * 60)
        print("              PERFORMANCE SUMMARY")
        print("=" * 60)

        print(f"Closed Trades       : {performance['total_trades']}")
        print(f"Winners             : {performance['winners']}")
        print(f"Losers              : {performance['losers']}")
        print(f"Win Rate            : {performance['win_rate']:.2f}%")
        print(f"Total Realized P/L  : ${performance['total_realized_pl']:.2f}")
        print(f"Average Trade P/L   : ${performance['average_pl']:.2f}")
        print(f"Average Win         : ${performance['average_win']:.2f}")
        print(f"Average Loss        : ${performance['average_loss']:.2f}")

        profit_factor = performance["profit_factor"]

        if profit_factor == float("inf"):
           print("Profit Factor       : INF")
        else:
           print(f"Profit Factor       : {profit_factor:.2f}")

        print(f"Best Trade          : ${performance['best_trade']:.2f}")
        print(f"Worst Trade         : ${performance['worst_trade']:.2f}")
        print(f"Expectancy / Trade  : ${performance['expectancy']:.2f}")

        print("=" * 60)

        # ----------------------------------------
        # Save Report
        # ----------------------------------------

        self.report.save_csv(self.results)
        now = datetime.now()

        scan_date = now.strftime("%Y-%m-%d")
        scan_time = now.strftime("%H:%M:%S")

        for stock in self.results:

            self.database.save_scan(
                 stock,
                 scan_date,
                 scan_time
    )

        print("✓ Results saved to SQLite.")

        self.portfolio.show_portfolio()
        
        positions = self.portfolio.get_open_positions()

        for position in positions:

            self.monitor.analyze_position(
            position,
            market
    )

        print("\nReport saved successfully.")

    # ==================================================
    # DISPLAY RESULTS
    # ==================================================

    def display_results(self):

        if not self.results:
            print("\nNo opportunities found.\n")
            return

        print()

        print(
            f"{'SYM':<8}"
            f"{'PRICE':>10}"
            f"{'ATR':>8}"
            f"{'ENTRY':>10}"
            f"{'STOP':>10}"
            f"{'TARGET':>10}"
            f"{'RR':>8}"
            f"{'SCORE':>8}"
            f"{'CONF':>8}"
            f"{'ACTION':>12}"
        )

        print("-" * 110)
        for stock in self.results:

            print(
                f"{stock['Symbol']:<8}"
                f"{stock['Price']:>10.2f}"
                f"{stock['ATR']:>8.2f}"
                f"{stock['Entry']:>10.2f}"
                f"{stock['Stop']:>10.2f}"
                f"{stock['Target']:>10.2f}"
                f"{stock['RR']:>8.2f}"
                f"{stock['Score']:>8}"
                f"{stock['Confidence']:>7}%"
                f"{stock['Decision']:>12}"
            )

        print("-" * 110)

        buys = sum(
            1 for stock in self.results
            if stock["Decision"].upper() == "BUY"
        )

        sells = sum(
            1 for stock in self.results
            if stock["Decision"].upper() == "SELL"
        )

        holds = sum(
            1 for stock in self.results
            if stock["Decision"].upper() == "HOLD"
        )

        print(f"\nTotal Symbols : {len(self.results)}")
        print(f"BUY Signals   : {buys}")
        print(f"SELL Signals  : {sells}")
        print(f"HOLD Signals  : {holds}")

        if self.results:

            best = max(
                self.results,
                key=lambda x: x["Score"]
            )

            print("\nBest Opportunity")
            print("-" * 40)
            print(f"Symbol     : {best['Symbol']}")
            print(f"Price      : {best['Price']:.2f}")
            print(f"Score      : {best['Score']}")
            print(f"Confidence : {best['Confidence']}%")
            print(f"Decision   : {best['Decision']}")
            print(f"Entry      : {best['Entry']:.2f}")
            print(f"Target     : {best['Target']:.2f}")
            print(f"Stop       : {best['Stop']:.2f}")
            print(f"RR         : {best['RR']:.2f}")
            print("-" * 40)
            print("Scan finished successfully.")


    