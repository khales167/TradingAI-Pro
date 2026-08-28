from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

all_trades = []
results = []

print("\n" + "=" * 80)
print("MULTI-SYMBOL HISTORICAL BACKTEST")
print("=" * 80)

for symbol in WATCHLIST:

    print(f"\nTesting {symbol}...")

    try:

        trades = backtester.run(
            symbol,
            period="2y"
        )

        performance = backtester.performance(trades)

        results.append({
            "symbol": symbol,
            "trades": performance["total_trades"],
            "winners": performance["winners"],
            "losers": performance["losers"],
            "win_rate": performance["win_rate"],
            "profit_factor": performance["profit_factor"],
            "expectancy": performance["expectancy"],
            "average_r": performance["average_r"],
            "total_pl": performance["total_pl"]
        })

        all_trades.extend(trades)

    except Exception as e:

        print(f"ERROR {symbol}: {e}")


# ==================================================
# DISPLAY EACH SYMBOL
# ==================================================

print("\n")
print("=" * 100)
print("RESULTS BY SYMBOL")
print("=" * 100)

print(
    f"{'SYMBOL':<8}"
    f"{'TRADES':>8}"
    f"{'WINNERS':>10}"
    f"{'LOSERS':>10}"
    f"{'WIN%':>10}"
    f"{'PF':>10}"
    f"{'AVG-R':>10}"
    f"{'EXP':>12}"
    f"{'P/L':>12}"
)

print("-" * 100)

for result in results:

    pf = result["profit_factor"]

    if pf == float("inf"):
        pf_display = "INF"
    else:
        pf_display = f"{pf:.2f}"

    print(
        f"{result['symbol']:<8}"
        f"{result['trades']:>8}"
        f"{result['winners']:>10}"
        f"{result['losers']:>10}"
        f"{result['win_rate']:>9.2f}%"
        f"{pf_display:>10}"
        f"{result['average_r']:>10.2f}"
        f"{result['expectancy']:>12.2f}"
        f"{result['total_pl']:>12.2f}"
    )


# ==================================================
# GLOBAL PERFORMANCE
# ==================================================

global_performance = backtester.performance(
    all_trades
)

print("\n")
print("=" * 70)
print("GLOBAL STRATEGY PERFORMANCE")
print("=" * 70)

print(
    f"Total Trades       : "
    f"{global_performance['total_trades']}"
)

print(
    f"Winners            : "
    f"{global_performance['winners']}"
)

print(
    f"Losers             : "
    f"{global_performance['losers']}"
)

print(
    f"Win Rate           : "
    f"{global_performance['win_rate']:.2f}%"
)

print(
    f"Total P/L          : "
    f"{global_performance['total_pl']:.2f}"
)

print(
    f"Average P/L        : "
    f"{global_performance['average_pl']:.2f}"
)

print(
    f"Average Win        : "
    f"{global_performance['average_win']:.2f}"
)

print(
    f"Average Loss       : "
    f"{global_performance['average_loss']:.2f}"
)

pf = global_performance["profit_factor"]

if pf == float("inf"):
    print("Profit Factor      : INF")
else:
    print(
        f"Profit Factor      : "
        f"{pf:.2f}"
    )

print(
    f"Expectancy         : "
    f"{global_performance['expectancy']:.2f}"
)

print(
    f"Average R          : "
    f"{global_performance['average_r']:.2f}"
)
print(
    f"Break-even Trades  : "
    f"{global_performance['break_even_trades']}"
)

print(
    f"Best Trade         : "
    f"{global_performance['best_r']:.2f}R"
)

print(
    f"Worst Trade        : "
    f"{global_performance['worst_r']:.2f}R"
)

print(
    f"Max Drawdown       : "
    f"{global_performance['max_drawdown_r']:.2f}R"
)

print("=" * 70)