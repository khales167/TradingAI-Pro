"""V9.4 stock-split data consistency checks (offline, isolated).

A 4:1 split changes raw share price and volume, but adjusted historical
OHLCV should preserve economic continuity. No portfolio/broker writes.
"""
import numpy as np
import pandas as pd

from core.daily_backtester import DailyTechnicalBacktester


def make_history(adjusted: bool) -> pd.DataFrame:
    n = 260
    split_index = 230
    dates = pd.bdate_range("2024-01-01", periods=n)
    underlying = np.linspace(95.0, 115.0, n)
    # Pre-split quotes 4x post-split quotes; volume scales inversely.
    raw_factor = np.where(np.arange(n) < split_index, 4.0, 1.0)
    price_factor = np.ones(n) if adjusted else raw_factor
    volume_factor = np.ones(n) if adjusted else 1.0 / raw_factor
    df = pd.DataFrame({
        "Open": underlying * price_factor * 0.999,
        "High": underlying * price_factor * 1.01,
        "Low": underlying * price_factor * 0.99,
        "Close": underlying * price_factor,
        "Volume": 1000000.0 * volume_factor,
    }, index=dates)
    return df


def main():
    raw = make_history(adjusted=False)
    adjusted = make_history(adjusted=True)
    split_day = 230
    raw_jump = raw["Close"].iloc[split_day] / raw["Close"].iloc[split_day - 1] - 1
    adjusted_jump = adjusted["Close"].iloc[split_day] / adjusted["Close"].iloc[split_day - 1] - 1
    assert raw_jump < -0.70, raw_jump
    assert abs(adjusted_jump) < 0.01, adjusted_jump
    print(f"PASS: raw 4:1 split creates apparent {raw_jump:.1%} price drop")
    print(f"PASS: split-adjusted price continuity {adjusted_jump:+.2%}")

    # Total economic value is unchanged by a pure split: 1 pre-split share
    # becomes 4 post-split shares at one-quarter the raw price.
    pre_value = 1 * raw["Close"].iloc[split_day - 1]
    post_value = 4 * raw["Close"].iloc[split_day]
    expected_market_move = adjusted["Close"].iloc[split_day] / adjusted["Close"].iloc[split_day - 1]
    assert abs(post_value / pre_value - expected_market_move) < 1e-12
    print("PASS: 4 post-split shares preserve economic value after market move")

    # Technical engine accepts continuous adjusted OHLCV and returns
    # deterministic output. This does NOT certify vendor split adjustments.
    engine = DailyTechnicalBacktester()
    first = engine.run(adjusted, initial_cash=2000.0)
    second = engine.run(adjusted.copy(), initial_cash=2000.0)
    assert first["trades"] == second["trades"]
    assert first["realized_cash"] == second["realized_cash"]
    print("PASS: adjusted OHLCV produces deterministic backtest replay")
    print("NOTE: yfinance auto_adjust=True also adjusts for dividends; verify real corporate actions separately.")


if __name__ == "__main__":
    main()
