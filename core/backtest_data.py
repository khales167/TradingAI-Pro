"""Backtest-only daily price loader; does not change live scanner data."""
from datetime import date

import pandas as pd
import yfinance as yf


def load_backtest_data(symbol: str, period: str = "2y", *, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Download consistently adjusted OHLC; preserve raw volume.

    Use start/end together for a fixed date window (end is exclusive).\n    auto_adjust=True adjusts historical OHLC for splits and cash dividends.
    This is suitable for a first-pass consistency check, but dividend-adjusted
    OHLC is not identical to historically executable market prices.
    """
    if (start is None) != (end is None):
        raise ValueError("Provide both start and end, or neither")
    if start is not None:
        try:
            start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
        except (ValueError, TypeError) as exc:
            raise ValueError("start and end must be YYYY-MM-DD") from exc
        if start_date >= end_date:
            raise ValueError("start must precede end (exclusive)")
    date_options = {"start": start, "end": end} if start is not None else {"period": period}
    df = yf.download(
        tickers=symbol,
        **date_options,
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
