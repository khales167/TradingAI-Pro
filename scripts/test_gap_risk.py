"""V9.3 isolated gap-risk regression tests.

Uses synthetic OHLCV and patched indicators to guarantee a signal;
never touches live portfolio, databases or brokers.
"""
import pandas as pd
from unittest.mock import patch
from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange

from core.daily_backtester import DailyTechnicalBacktester


def run_gap_case(open_after_entry, expected_reason, expected_raw_exit):
    dates = pd.bdate_range("2024-01-01", periods=231)
    data = pd.DataFrame({
        "Open": [100.0] * 231,
        "High": [101.0] * 231,
        "Low": [99.0] * 231,
        "Close": [100.0] * 231,
        "Volume": [1000.0] * 231,
    }, index=dates)
    # The signal on day 209 creates a position at $100, with ATR=$2,
    # stop=$97 and target=$106. Exit gap occurs on day 210.
    data.iloc[210, data.columns.get_loc("Open")] = open_after_entry
    data.iloc[210, data.columns.get_loc("High")] = max(open_after_entry, 101.0)
    data.iloc[210, data.columns.get_loc("Low")] = min(open_after_entry, 99.0)

    def constant(value):
        return pd.Series([value] * len(data), index=data.index)

    with patch.object(SMAIndicator, "sma_indicator", autospec=True,
                      side_effect=lambda self: constant({19: 99.0, 38: 98.0, 209: 97.0}[self._window])), \
         patch.object(ADXIndicator, "adx", autospec=True, return_value=constant(30.0)), \
         patch.object(ADXIndicator, "adx_pos", autospec=True, return_value=constant(25.0)), \
         patch.object(ADXIndicator, "adx_neg", autospec=True, return_value=constant(10.0)), \
         patch.object(AverageTrueRange, "average_true_range", autospec=True, return_value=constant(2.0)):
        result = DailyTechnicalBacktester().run(
            data, initial_cash=2000.0, risk_per_trade_pct=1.0,
            commission_per_share=0.005, slippage_bps=5,
        )
    assert result["trades"], f"No closed trades for {expected_reason}"
    trade = result["trades"][0]
    assert trade["reason"] == expected_reason, trade
    assert abs(trade["raw_exit"] - expected_raw_exit) < 1e-9, trade
    expected_exit = expected_raw_exit * (1 - 0.0005)
    assert abs(trade["exit"] - expected_exit) < 1e-9, trade
    expected_pl = (expected_exit - trade["entry"] - 0.01) * trade["shares"]
    assert abs(trade["pl"] - expected_pl) < 1e-8, trade
    return trade


def main():
    stop = run_gap_case(90.0, "STOP_GAP", 90.0)
    print(f"PASS: stop gap exits at open $90, not planned stop $97; P/L=${stop['pl']:+.2f}")
    target = run_gap_case(110.0, "TARGET_GAP", 110.0)
    print(f"PASS: target gap exits at open $110, not planned target $106; P/L=${target['pl']:+.2f}")
    assert stop["pl"] < -20.0, "Gap loss should exceed $20 planned 1% risk budget"
    print("PASS: stop gap can exceed planned 1% risk ($20 on $2000)")
    print("PASS: slippage and both-side commission applied")


if __name__ == "__main__":
    main()
