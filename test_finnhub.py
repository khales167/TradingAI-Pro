import os
from dotenv import load_dotenv
import finnhub

load_dotenv()

api_key = os.getenv("FINNHUB_API_KEY")

client = finnhub.Client(api_key=api_key)

print(client.quote("AAPL"))