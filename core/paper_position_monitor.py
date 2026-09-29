from __future__ import annotations

from datetime import datetime

from core.database import DatabaseManager


class PaperPositionMonitor:
    """Close paper positions when a supplied market price hits stop or target."""

    def __init__(self, database: DatabaseManager | None = None):
        self.db = database or DatabaseManager()

    def check_symbol(self, symbol: str, market_price: float) -> dict:
        symbol = symbol.upper()
        price = float(market_price)

        position = next(
            (row for row in self.db.get_portfolio() if row["symbol"] == symbol),
            None,
        )

        if position is None:
            return {"Closed": False, "Reason": "No open paper position"}

        stop = float(position["stop_price"])
        target = float(position["target_price"])

        if price <= stop:
            exit_price = stop
            trigger = "STOP"
        elif price >= target:
            exit_price = target
            trigger = "TARGET"
        else:
            return {
                "Closed": False,
                "Symbol": symbol,
                "MarketPrice": round(price, 2),
                "Reason": "Position remains open",
            }

        closed = self.db.close_position(
            symbol,
            exit_price,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return {
            "Closed": bool(closed),
            "Symbol": symbol,
            "Trigger": trigger,
            "ExitPrice": round(exit_price, 2),
            "MarketPrice": round(price, 2),
            "Mode": "PAPER",
        }
