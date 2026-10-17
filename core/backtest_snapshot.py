"""Immutable local OHLCV snapshot for isolated daily backtests.

CSV + SHA256 metadata; never writes to live portfolio or trading databases.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from core.backtest_data import load_backtest_data

COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def create_snapshot(symbol: str, start: str, end: str, directory: str = "data/backtest_snapshots") -> Path:
    symbol = symbol.upper().strip()
    if not symbol or not symbol.replace("-", "").replace(".", "").isalnum():
        raise ValueError("Invalid ticker symbol")
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    prefix = f"{symbol}_{start}_{end}"
    csv_path = folder / f"{prefix}.csv"
    meta_path = folder / f"{prefix}.json"
    if csv_path.exists() or meta_path.exists():
        raise FileExistsError(f"Snapshot already exists: {prefix}; never overwrite a snapshot")
    df = load_backtest_data(symbol, start=start, end=end)
    csv_bytes = df[COLUMNS].to_csv(index_label="Date", float_format="%.17g").encode("utf-8")
    metadata = {
        "schema_version": 1,
        "symbol": symbol,
        "start": start,
        "end_exclusive": end,
        "rows": len(df),
        "first_date": str(df.index.min().date()),
        "last_date": str(df.index.max().date()),
        "adjustment": "yfinance auto_adjust=True (split/dividend-adjusted OHLC)",
        "sha256": _digest(csv_bytes),
    }
    # Exclusive creation prevents accidental replacement.
    with csv_path.open("xb") as handle:
        handle.write(csv_bytes)
    try:
        with meta_path.open("x", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)
    except Exception:
        csv_path.unlink()
        raise
    return csv_path


def load_snapshot(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)
    meta_path = csv_path.with_suffix(".json")
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    csv_bytes = csv_path.read_bytes()
    if _digest(csv_bytes) != metadata["sha256"]:
        raise ValueError(f"Snapshot SHA256 mismatch: {csv_path}")
    df = pd.read_csv(csv_path, index_col="Date", parse_dates=["Date"])
    if list(df.columns) != COLUMNS or len(df) != metadata["rows"]:
        raise ValueError("Snapshot columns or row count mismatch")
    if not df.index.is_unique or not df.index.is_monotonic_increasing:
        raise ValueError("Snapshot dates are not unique and ascending")
    if str(df.index.min().date()) != metadata["first_date"] or str(df.index.max().date()) != metadata["last_date"]:
        raise ValueError("Snapshot date bounds mismatch")
    return df
