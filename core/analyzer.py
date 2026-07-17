from core.news_score import NewsScore
from news.news_scanner import NewsScanner

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

    def analyze(self, data):

        score = 0
        reasons = []

        # Trend
        if data["MA19"] > data["MA38"] > data["MA209"]:
            score += TREND_SCORE
            reasons.append("Trend")

        # DMI
        if data["DI+"] > data["DI-"]:
            score += DMI_SCORE
            reasons.append("DI+")

        # ADX
        if data["ADX"] > ADX_LIMIT:
            score += ADX_SCORE
            reasons.append("ADX")

        # RVOL
        if data["RVOL"] >= RVOL_LIMIT:
            score += RVOL_SCORE
            reasons.append("RVOL")

        # News
        headlines = self.news.get_news(data["symbol"])
        news = self.news_score.calculate(headlines)

        score += news["score"]
        reasons.extend(news["keywords"])

        # لا نتجاوز الحد الأقصى
        score = min(score, MAX_SCORE)

        confidence = round(score / MAX_SCORE * 100)

        return {
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "news_score": news["score"]
        }