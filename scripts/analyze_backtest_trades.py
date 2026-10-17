"""Inspect each closed trade from the isolated technical-only backtest."""
from core.data_manager import DataManager
from core.daily_backtester import DailyTechnicalBacktester


def main():
    capital = 2000.0
    df = DataManager().get_data("NVDA")
    if df is None:
        raise RuntimeError("NVDA data unavailable")
    result = DailyTechnicalBacktester().run(df, initial_cash=capital)
    trades = result["trades"]
    print("\nNVDA | Technical-only | Capital $2,000 | Risk 1% | Exposure 40%")
    print("Entry date | Exit date | Qty | Entry | Stop | Target | Exit | Reason | P/L")
    for t in trades:
        print(
            f"{t['entry_date']} | {t['exit_date']} | {t['shares']} | "
            f"${t['entry']:.2f} | ${t['stop']:.2f} | ${t['target']:.2f} | "
            f"${t['exit']:.2f} | {t['reason']} | ${t['pl']:+.2f}"
        )
    wins = [t["pl"] for t in trades if t["pl"] > 0]
    losses = [t["pl"] for t in trades if t["pl"] < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
    equity = capital
    peak = capital
    max_drawdown = 0.0
    for t in trades:
        equity += t["pl"]
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak * 100)
    print(f"\nClosed trades: {len(trades)}")
    print(f"Win rate: {win_rate:.2f}%")
    print(f"Profit factor: {profit_factor:.2f}")
    print(f"Max closed-trade drawdown: {max_drawdown:.2f}%")
    print(f"Realized P/L: ${sum(t['pl'] for t in trades):+.2f}")
    print(f"Open position: {result['open_position']}")
    print("Caveat: no fees/slippage; drawdown measured only at closed-trade points.")


if __name__ == "__main__":
    main()
