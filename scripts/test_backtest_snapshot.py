"""V9.2: create and verify an immutable NVDA historical snapshot."""
from core.backtest_snapshot import create_snapshot, load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SYMBOL = "NVDA"
START = "2024-10-01"
END = "2026-10-16"


def main():
    from pathlib import Path
    filename = Path("data/backtest_snapshots") / f"{SYMBOL}_{START}_{END}.csv"
    if filename.exists():
        print(f"Using existing snapshot (no overwrite): {filename}")
    else:
        filename = create_snapshot(SYMBOL, START, END)
        print(f"Created snapshot: {filename}")
    df = load_snapshot(filename)
    engine = DailyTechnicalBacktester()
    params = dict(initial_cash=2000.0, commission_per_share=0.005, slippage_bps=5)
    first = engine.run(df, **params)
    second = engine.run(load_snapshot(filename), **params)
    assert first["trades"] == second["trades"]
    assert first["realized_cash"] == second["realized_cash"]
    print(f"PASS: verified snapshot, {len(df)} bars")
    print("PASS: deterministic backtest replay from saved CSV")
    print(f"Closed trades: {first['closed_trades']}; realized P/L: ${first['realized_cash'] - 2000:+.2f}")
    print(f"Metadata and SHA256: {filename.with_suffix('.json')}")


if __name__ == "__main__":
    main()
