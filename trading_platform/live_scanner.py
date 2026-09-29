from __future__ import annotations

from core.analyzer import Analyzer
from core.data_manager import DataManager
from core.decision import DecisionEngine
from core.trade_levels import TradeLevels
from indicators.indicators import calculate_indicators
from market.sentiment import MarketSentiment


class LiveScannerService:
    """Full scanner pipeline for tickers detected by TraderTV."""

    def __init__(
        self,
        data_manager: DataManager | None = None,
        analyzer: Analyzer | None = None,
        decision: DecisionEngine | None = None,
        trade_levels: TradeLevels | None = None,
        market_sentiment: MarketSentiment | None = None,
    ):
        self.data_manager = data_manager or DataManager()
        self.analyzer = analyzer or Analyzer()
        self.decision = decision or DecisionEngine()
        self.trade_levels = trade_levels or TradeLevels()
        self.market_sentiment = market_sentiment or MarketSentiment()

    def scan_symbol(
        self,
        symbol: str,
        market: dict | None = None,
    ) -> dict | None:
        symbol = symbol.strip().upper()

        if not symbol:
            return None

        df = self.data_manager.get_data(symbol)

        if df is None:
            return None

        data = calculate_indicators(symbol, df)

        if data is None:
            return None

        if market is None:
            market = self.market_sentiment.analyze()

        analysis = self.analyzer.analyze(data, symbol)
        decision = self.decision.decide(analysis, market)
        levels = self.trade_levels.calculate(data)

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
            "Score": analysis["score"],
            "Confidence": analysis["confidence"],
            "Decision": decision["action"],
            "Quality": decision["quality"],
            "Market": decision["market"],
            "Entry": levels["Entry"],
            "Stop": levels["Stop"],
            "Target": levels["Target"],
            "RR": levels["RR"],
            "NewsScore": analysis["news_score"],
            "Reasons": ", ".join(decision["reasons"]),
            "DecisionReasons": "; ".join(
                decision["decision_reasons"]
            ),
            "TraderTV": True,
        }

    def scan_symbols(self, symbols: list[str]) -> list[dict]:
        results = []
        unique_symbols = list(dict.fromkeys(symbols))

        if not unique_symbols:
            return results

        market = self.market_sentiment.analyze()

        for symbol in unique_symbols:
            result = self.scan_symbol(symbol, market=market)

            if result is not None:
                results.append(result)

        return results
