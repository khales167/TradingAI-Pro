"""V11.4 fixed-snapshot full-backtest regression after risk precision fix.

Checks the previously recorded V10.2 closed-trade counts and realized P/L.
Does not download missing snapshots or touch live portfolio/broker state.
"""
from __future__ import annotations

from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

START = "2024-10-01"
END = "2026-10-16"
CAPITAL = 2000.0
BASELINES = {
    "NVDA": (6, -38.59),
    "AMD": (7, 3.68),
    "AAPL": (8, -21.99),
    "TSLA": (0, 0.00),
    "AVGO": (3, 83.42),
}


def main():
    passed = 0
    for symbol, (expected_trades, expected_pl) in BASELINES.items():
        snapshot = Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv")
        if not snapshot.is_file():
            raise FileNotFoundError(f"Missing verified snapshot: {snapshot}")
        df = load_snapshot(snapshot)
        result = DailyTechnicalBacktester().run(
            df, initial_cash=CAPITAL, risk_per_trade_pct=1.0,
            commission_per_share=0.005, slippage_bps=5,
        )
        trades = result["trades"]
        actual_pl = sum(float(t["pl"]) for t in trades)
        ledger_pl = float(result["realized_cash"]) - CAPITAL
        assert result["open_position"] is None, f"{symbol}: unexpected open position"
        assert abs(actual_pl - ledger_pl) < 1e-7, f"{symbol}: ledger mismatch"
        assert len(trades) == expected_trades, (
            f"{symbol}: trades changed {expected_trades} -> {len(trades)}"
        )
        # Original V10.2 P/L was displayed to cents, not stored at full precision.
        assert abs(actual_pl - expected_pl) < 0.011, (
            f"{symbol}: P/L changed from about ${expected_pl:+.2f} "
            f"to ${actual_pl:+.4f}"
        )
        passed += 1
        print(
            f"PASS {symbol:5} closed={len(trades):2} "
            f"realized_P/L=${actual_pl:+.2f} "
            f"baseline=${expected_pl:+.2f}"
        )
    print(f"Completed: {passed}/{len(BASELINES)} full-backtest regressions")
    print("NOTE: baselines are V10.2 rounded-to-cent outputs; this is not a trade-by-trade equivalence test.")
    print("NOTE: independently funded $2,000 stock runs, verified local snapshots only.")
    print("NOTE: no strategy tuning, live account writes, or broker orders.")


if __name__ == "__main__":
    main()
