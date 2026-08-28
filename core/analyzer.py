from news.news_score import NewsScore
from news.news_scanner import NewsScanner

from earnings.earnings_calendar import EarningsCalendar
from earnings.earnings_engine import EarningsEngine

from config import (
    TREND_SCORE,
    DMI_SCORE,
    ADX_SCORE,
    RVOL_SCORE,
    ADX_LIMIT,
    RVOL_LIMIT,
    MAX_SCORE
)


class Analyzer:

    def __init__(self):

        self.news = NewsScanner()
        self.news_score = NewsScore()

        self.earnings = EarningsCalendar()
        self.earnings_engine = EarningsEngine()

    def analyze(self, data, symbol):

        score = 0
        reasons = []

        symbol = symbol.upper()

        

        # ==================================================
        # EARNINGS CALENDAR
        # ==================================================

        earnings = self.earnings.get_today()

        today_earnings = None

        for item in earnings:

            if item["symbol"] == symbol:

                today_earnings = item
                break

        # ==================================================
        # TREND
        # ==================================================

        if data["MA19"] > data["MA38"] > data["MA209"]:

            score += TREND_SCORE
            reasons.append("Trend")

        # ==================================================
        # DMI
        # ==================================================

        if data["DI+"] > data["DI-"]:

            score += DMI_SCORE
            reasons.append("DI+")

        # ==================================================
        # ADX
        # ==================================================

        if data["ADX"] > ADX_LIMIT:

            score += ADX_SCORE
            reasons.append("ADX")

        # ==================================================
        # RVOL
        # ==================================================

        if data["RVOL"] >= RVOL_LIMIT:

            score += RVOL_SCORE
            reasons.append("RVOL")

        # ==================================================
        # NEWS
        # ==================================================

        headlines = self.news.get_news(symbol)

        print("\n==============================")
        print(symbol)
        print("==============================")

        for item in headlines:

            print(item["title"])

        news_result = self.news_score.calculate(headlines)

        print("=" * 50)
        print(symbol)
        print("News Score :", news_result["score"])
        print("Positive   :", news_result["positive"])
        print("Negative   :", news_result["negative"])
        print("=" * 50)

        score += news_result["score"]

        reasons.extend(news_result["keywords"])

        # ==================================================
        # EARNINGS ENGINE
        # ==================================================

        earnings_result = self.earnings_engine.analyze(
            symbol,
            earnings
        )

        # HIGH = +15
        if earnings_result["risk"] == "HIGH":

            score += 15

            reasons.append(
                earnings_result["message"]
            )

        # MEDIUM = +8
        elif earnings_result["risk"] == "MEDIUM":

            score += 8

            reasons.append(
                earnings_result["message"]
            )

        # ==================================================
        # MAX SCORE
        # ==================================================

        score = min(score, MAX_SCORE)

        # ==================================================
        # CONFIDENCE
        # ==================================================

        confidence = round(
            score / MAX_SCORE * 100
        )

        # ==================================================
        # RETURN RESULT
        # ==================================================

        return {

            "score": score,

            "confidence": confidence,

            "reasons": reasons,

            # -------------------------
            # NEWS
            # -------------------------

            "news_score": news_result["score"],

            "positive_news": news_result["positive"],

            "negative_news": news_result["negative"],

            # -------------------------
            # EARNINGS
            # -------------------------

            "earnings": today_earnings,

            "earnings_result": earnings_result,

            # -------------------------
            # TECHNICAL
            # -------------------------

            "trend":
                data["MA19"]
                > data["MA38"]
                > data["MA209"],

            "adx": data["ADX"],

            "di_plus": data["DI+"],

            "di_minus": data["DI-"],

            "rvol": data["RVOL"],

            "atr": data["ATR"]
        }