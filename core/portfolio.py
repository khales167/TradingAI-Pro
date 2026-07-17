from datetime import datetime

import pandas as pd
import yfinance as yf

from core.database import DatabaseManager


class PortfolioManager:

    def __init__(self, capital=10000):

        self.initial_capital = capital
        self.available_cash = capital

        self.positions = []

        self.db = DatabaseManager()

    # ==================================================
    # ADD POSITION
    # ==================================================

    def add_position(self, symbol, shares, entry):

        cost = shares * entry

        if cost > self.available_cash:
            print("Not enough cash.")
            return False

        self.available_cash -= cost

        position = {
            "Symbol": symbol,
            "Shares": shares,
            "Entry": round(entry, 2),
            "Cost": round(cost, 2)
        }

        self.positions.append(position)

        self.db.add_position(
            symbol=symbol,
            quantity=shares,
            entry_price=entry,
            entry_date=datetime.now().strftime("%Y-%m-%d")
        )

        return True

    # ==================================================
    # LOAD POSITIONS FROM DATABASE
    # ==================================================

    def load_database_positions(self):

        return self.db.get_portfolio()

    # ==================================================
    # UPDATE CURRENT PRICES
    # ==================================================

    def update_positions(self):

        updated = []

        for position in self.positions:

            symbol = position["Symbol"]

            try:

                df = yf.download(
                    symbol,
                    period="5d",
                    interval="1d",
                    progress=False,
                    auto_adjust=False
                )

                if df.empty:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                close = df["Close"].squeeze()

                current = float(close.iloc[-1])

                entry = position["Entry"]
                shares = position["Shares"]

                pnl = (current - entry) * shares
                pnl_pct = ((current - entry) / entry) * 100

                position["Current"] = round(current, 2)
                position["PnL"] = round(pnl, 2)
                position["PnL%"] = round(pnl_pct, 2)

                updated.append(position)

            except Exception as e:

                print(f"{symbol}: {e}")

        return updated

    # ==================================================
    # DISPLAY PORTFOLIO
    # ==================================================

    def display(self):

        positions = self.update_positions()

        if not positions:
            print("\nPortfolio is empty.\n")
            return

        print("\n" + "=" * 90)
        print("PORTFOLIO")
        print("=" * 90)

        print(
            f"{'SYM':<8}"
            f"{'QTY':>8}"
            f"{'ENTRY':>12}"
            f"{'CURRENT':>12}"
            f"{'P/L':>12}"
            f"{'P/L %':>10}"
        )

        print("-" * 90)

        total_profit = 0

        for p in positions:

            total_profit += p["PnL"]

            print(
                f"{p['Symbol']:<8}"
                f"{p['Shares']:>8}"
                f"{p['Entry']:>12.2f}"
                f"{p['Current']:>12.2f}"
                f"{p['PnL']:>12.2f}"
                f"{p['PnL%']:>9.2f}%"
            )

        print("-" * 90)

        summary = self.summary()

        print(f"Capital   : {summary['Capital']:.2f}")
        print(f"Cash      : {summary['Cash']:.2f}")
        print(f"Invested  : {summary['Invested']:.2f}")
        print(f"Profit    : {total_profit:.2f}")

    # ==================================================
    # SUMMARY
    # ==================================================

    def summary(self):

        invested = sum(
            position["Cost"]
            for position in self.positions
        )

        return {
            "Capital": self.initial_capital,
            "Cash": round(self.available_cash, 2),
            "Invested": round(invested, 2),
            "Positions": len(self.positions)
        }