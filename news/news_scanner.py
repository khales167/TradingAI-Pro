import os
from dotenv import load_dotenv
import finnhub

load_dotenv()

client = finnhub.Client(
    api_key=os.getenv("FINNHUB_API_KEY")
)


class NewsScanner:

    def get_news(self, symbol):

        try:

            news = client.company_news(
                symbol,
                _from="2026-07-01",
                to="2026-07-09"
            )

            headlines = []

            for item in news[:5]:
                headlines.append(item["headline"])

            return headlines

        except Exception:

            return []