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
            # Use 2 years of daily history so long moving averages
            # (especially MA209) have a reliable data buffer.
            df = yf.download(
                tickers=symbol,
                period="2y",
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

            # MA209 needs at least 209 daily observations.
            if len(df) < 209:
                print(
                    f"❌ Not enough history for {symbol}: "
                    f"{len(df)} rows (209 required)"
                )
                return None

            return df

        except Exception as e:
            print(f"ERROR: {e}")
            return None
