from backtest.historical_backtester import HistoricalBacktester


backtester = HistoricalBacktester()

trades = backtester.run(
    "NVDA",
    period="2y"
)

print("\n" + "=" * 70)
print("HISTORICAL BACKTEST TRADES")
print("=" * 70)

for trade in trades:

    print(
        f"{trade['entry_date']} -> {trade['exit_date']} "
        f"| Entry: {trade['entry']:.2f} "
        f"| Exit: {trade['exit_price']:.2f} "
        f"| P/L: {trade['pl']:.2f} "
        f"| R: {trade['r_multiple']:.2f} "
        f"| {trade['exit_reason']}"
    )

performance = backtester.performance(trades)

print("\n" + "=" * 70)
print("HISTORICAL BACKTEST PERFORMANCE")
print("=" * 70)

for key, value in performance.items():
    print(f"{key:<20}: {value}")