import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
import finnhub

load_dotenv()

client = finnhub.Client(
    api_key=os.getenv("FINNHUB_API_KEY")
)


class NewsScanner:

    def get_news(self, symbol):

        try:

            today = datetime.today()
            week_ago = today - timedelta(days=7)

            news = client.company_news(
                symbol,
                _from=week_ago.strftime("%Y-%m-%d"),
                to=today.strftime("%Y-%m-%d")
            )

            headlines = []

            for item in news[:10]:

                headlines.append({

                    "title": item.get("headline", ""),

                    "summary": item.get("summary", ""),

                    "source": item.get("source", ""),

                    "date": item.get("datetime", 0)

                })

            return headlines

        except Exception as e:

            print(f"News Error ({symbol}): {e}")

            return []