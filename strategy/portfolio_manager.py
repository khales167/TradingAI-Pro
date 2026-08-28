from datetime import datetime
from core.database import DatabaseManager
import yfinance as yf


class PortfolioManager:

    def __init__(self):
        self.db = DatabaseManager()

    def add_position(
        self,
        symbol,
        quantity,
        entry_price,
        stop_price,
        target_price
   ):
        if self.db.position_exists(symbol):
           print(f"⚠ {symbol} is already in portfolio.")
           return False  
        
        self.db.add_position(
             symbol=symbol,
             quantity=quantity,
             entry_price=entry_price,
             stop_price=stop_price,
             target_price=target_price,
             entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         )

        return True

    def get_open_positions(self):
        return self.db.get_portfolio()

    def show_portfolio(self):
    

        positions = self.get_open_positions()
        
 
        if not positions:
                   print("\n================== PORTFOLIO ==================")

        print(
            f"{'SYMBOL':<10}"
            f"{'QTY':>8}"
            f"{'ENTRY':>12}"
            f"{'CURRENT':>12}"
            f"{'P/L($)':>12}"
            f"{'P/L%':>10}"
            f"{'DAYS':>8}"
            f"{'STATUS':>14}"
        )

        print("-" * 90)

        total_pl = 0
        invested = 0
        current_value = 0

        for position in positions:

            symbol = position["symbol"]
            qty = position["quantity"]
            entry = position["entry_price"]
            stop = position["stop_price"]
            target = position["target_price"]

            try:
                entry_date = datetime.strptime(
                    position["entry_date"],
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                entry_date = datetime.strptime(
                    position["entry_date"],
                    "%Y-%m-%d"
                )

            days = (datetime.now() - entry_date).days

            try:
                current = yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1]
            except Exception:
                current = entry

            pl = (current - entry) * qty
            pl_percent = ((current - entry) / entry) * 100

            invested += entry * qty
            current_value += current * qty
            total_pl += pl

            if abs(pl) < 0.01:
                status = "⚪ EVEN"
            elif pl > 0:
                status = "🟢 WINNING"
            else:
                status = "🔴 LOSING"

            print(
                f"{symbol:<10}"
                f"{qty:>8}"
                f"{entry:>12.2f}"
                f"{current:>12.2f}"
                f"{pl:>12.2f}"
                f"{pl_percent:>9.2f}%"
                f"{days:>8}"
                f"{status:>14}"
            )