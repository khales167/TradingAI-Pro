import yfinance as yf
import pandas as pd


class RVOLScanner:

    def get_rvol(self, symbol):

        try:

            df = yf.download(
                symbol,
                period="30d",
                interval="1d",
                progress=False,
                auto_adjust=False
            )

            if df.empty:
                return 0

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            volume = df["Volume"].squeeze()

            avg_volume = volume.iloc[:-1].mean()
            today_volume = volume.iloc[-1]

            if avg_volume == 0:
                return 0

            rvol = today_volume / avg_volume

            return round(float(rvol), 2)

        except Exception:
            return 0