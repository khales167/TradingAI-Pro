from __future__ import annotations

from datetime import datetime

from core.database import DatabaseManager


class PaperTradeSimulator:
    """Record READY previews as local paper positions only."""

    def __init__(self, database: DatabaseManager | None = None):
        self.db = database or DatabaseManager()

    def execute(self, preview: dict) -> dict:
        if not preview.get("Ready"):
            return {
                "Executed": False,
                "Mode": "PAPER",
                "Reason": "Order preview is not READY",
            }

        shares = int(preview.get("Shares", 0))
        if shares <= 0:
            return {
                "Executed": False,
                "Mode": "PAPER",
                "Reason": "Share quantity must be greater than zero",
            }

        symbol = str(preview["Symbol"]).upper()
        if self.db.position_exists(symbol):
            return {
                "Executed": False,
                "Mode": "PAPER",
                "Reason": f"{symbol} already has an open paper position",
            }

        saved = self.db.add_position(
            symbol=symbol,
            quantity=shares,
            entry_price=float(preview["Entry"]),
            stop_price=float(preview["Stop"]),
            target_price=float(preview["Target"]),
            entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return {
            "Executed": bool(saved),
            "Mode": "PAPER",
            "Symbol": symbol,
            "Shares": shares,
            "Entry": float(preview["Entry"]),
            "Reason": "Paper position recorded" if saved else "Database rejected paper position",
        }
