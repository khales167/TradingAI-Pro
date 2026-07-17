from core.data_manager import DataManager


class MarketSentiment:

    def __init__(self):

        self.data = DataManager()

    def get_trend(self, symbol):

        df = self.data.get_data(symbol)

        if df is None:
            return None

        close = df["Close"]

        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()

        last = close.iloc[-1]

        if last > ma20.iloc[-1] > ma50.iloc[-1]:
            return "Bullish"

        if last < ma20.iloc[-1] < ma50.iloc[-1]:
            return "Bearish"

        return "Neutral"

    def analyze(self):

        symbols = [
            "SPY",
            "QQQ",
            "DIA"
        ]

        result = {}

        bullish = 0

        for s in symbols:

            trend = self.get_trend(s)

            result[s] = trend

            if trend == "Bullish":
                bullish += 1

        if bullish >= 2:
            overall = "Bullish"

        elif bullish == 1:
            overall = "Neutral"

        else:
            overall = "Bearish"

        result["Overall"] = overall

        return result