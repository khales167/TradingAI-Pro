import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")


class EarningsCalendar:

    def get_today(self):

        today = datetime.today().strftime("%Y-%m-%d")

        url = "https://finnhub.io/api/v1/calendar/earnings"

        params = {
            "from": today,
            "to": today,
            "token": API_KEY
        }

        try:

            response = requests.get(url, params=params, timeout=10)

            data = response.json()

            return data.get("earningsCalendar", [])

        except Exception as e:

            print("Earnings Error:", e)

            return []