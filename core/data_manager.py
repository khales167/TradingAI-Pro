import threading
import pandas as pd
import yfinance as yf


class DataManager:

    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get_data(
        self,
        symbol,
        period="300d",
        interval="1d"
    ):

        # Check cache
        with self.lock:
            if symbol in self.cache:
                print(f"✓ Cache : {symbol}")
                return self.cache[symbol].copy()

        # Download
        print(f"↓ Download : {symbol}")

        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False
        )

        # Debug
        print(f"\n=== {symbol} ===")
        print("Columns:", df.columns.tolist())
        print(df.tail(1))

        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Save to cache
        with self.lock:
            self.cache[symbol] = df.copy()

        return df