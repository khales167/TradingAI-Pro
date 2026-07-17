import pandas as pd


class UniverseScanner:

    def __init__(self):
        self.file = "data/universe.csv"

    def load(self):

        try:

            df = pd.read_csv(self.file)

            return df

        except:

            return pd.DataFrame()

    def filter(
        self,
        min_price=5,
        max_price=1000,
        min_volume=1000000
    ):

        df = self.load()

        if df.empty:
            return []

        df = df[
            (df["Price"] >= min_price)
            &
            (df["Price"] <= max_price)
            &
            (df["Volume"] >= min_volume)
        ]

        return df["Symbol"].tolist()