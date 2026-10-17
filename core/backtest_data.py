"""Backtest-only daily price loader; does not change live scanner data."""
import pandas as pd
import yfinance as yf


def load_backtest_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """Download consistently adjusted OHLC; preserve raw volume.

    auto_adjust=True adjusts historical OHLC for splits and cash dividends.
    This is suitable for a first-pass consistency check, but dividend-adjusted
    OHLC is not identical to historically executable market prices.
    """
    df = yf.download(
        tickers=symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        raise ValueError(f"No backtest data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{symbol}: missing columns {missing}")
    df = df[required].copy().dropna()
    if len(df) < 230:
        raise ValueError(f"{symbol}: insufficient history ({len(df)} rows)")
    if (df[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError(f"{symbol}: non-positive OHLC values")
    return df
