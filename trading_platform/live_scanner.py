from __future__ import annotations

from core.data_manager import DataManager
from indicators.indicators import calculate_indicators


class LiveScannerService:
    """Technical snapshot service for tickers detected by TraderTV."""

    def __init__(self, data_manager: DataManager | None = None):
        self.data_manager = data_manager or DataManager()

    def scan_symbol(self, symbol: str) -> dict | None:
        symbol = symbol.strip().upper()

        if not symbol:
            return None

        df = self.data_manager.get_data(symbol)

        if df is None:
            return None

        data = calculate_indicators(symbol, df)

        if data is None:
            return None

        return {
            "Symbol": symbol,
            "Price": data["price"],
            "MA19": data["MA19"],
            "MA38": data["MA38"],
            "MA209": data["MA209"],
            "ADX": data["ADX"],
            "DI+": data["DI+"],
            "DI-": data["DI-"],
            "RVOL": data["RVOL"],
            "Volume": data["Volume"],
            "TraderTV": True,
        }

    def scan_symbols(self, symbols: list[str]) -> list[dict]:
        results = []

        for symbol in dict.fromkeys(symbols):
            result = self.scan_symbol(symbol)

            if result is not None:
                results.append(result)

        return results
