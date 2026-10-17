"""Compare isolated daily technical backtests at fixed 1% risk per trade."""
from core.data_manager import DataManager
from core.daily_backtester import DailyTechnicalBacktester


def main():
    df = DataManager().get_data("NVDA")
    if df is None:
        raise RuntimeError("NVDA data unavailable")
    print("NVDA daily technical-only backtest (1% risk, 40% exposure cap)")
    print("Capital | Signals | Entries | Rejected | Closed | Realized P/L | Open")
    for capital in (500, 1000, 2000, 5000):
        result = DailyTechnicalBacktester().run(df, initial_cash=float(capital))
        d = result["diagnostics"]
        pl = result["realized_cash"] - capital
        print(
            f"${capital:>6,} | {d['technical_signals']:>7} | "
            f"{d['accepted_entries']:>7} | {d['rejected_by_risk']:>8} | "
            f"{result['closed_trades']:>6} | ${pl:>12.2f} | "
            f"{'Yes' if result['open_position'] else 'No'}"
        )
    print("Note: realized P/L excludes open unrealized P/L, fees and slippage.")


if __name__ == "__main__":
    main()
