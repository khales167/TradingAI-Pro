import threading
import pandas as pd
import yfinance as yf


class DataManager:

    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get_data(self, symbol):

        print(f"Downloading {symbol}")

        try:
            df = yf.download(
                tickers=symbol,
                period="1y",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False
            )

            print(df.tail())

            if df.empty:
                print(f"❌ Failed to download {symbol}")
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            return df

        except Exception as e:
            print(f"ERROR: {e}")
            return None