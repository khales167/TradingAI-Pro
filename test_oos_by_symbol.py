from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"


print("\n" + "=" * 100)
print("OUT-OF-SAMPLE PERFORMANCE BY SYMBOL")
print("=" * 100)

results = []


for symbol in WATCHLIST:

    print(
        f"\nTesting {symbol} "
        f"from {OOS_START} to {OOS_END}"
    )

    try:

        trades = backtester.run(
            symbol,
            start_date=OOS_START,
            end_date=OOS_END
        )

        performance = backtester.performance(
            trades
        )

        results.append({
            "symbol": symbol,
            "trades": performance["total_trades"],
            "winners": performance["winners"],
            "losers": performance["losers"],
            "break_even": performance["break_even_trades"],
            "win_rate": performance["win_rate"],
            "profit_factor": performance["profit_factor"],
            "average_r": performance["average_r"],
            "expectancy": performance["expectancy"],
            "max_drawdown_r": performance["max_drawdown_r"],
            "best_r": performance["best_r"],
            "worst_r": performance["worst_r"]
        })

    except Exception as e:

        print(f"ERROR {symbol}: {e}")


# ==================================================
# DISPLAY
# ==================================================

print("\n")
print("=" * 120)
print("OOS RESULTS BY SYMBOL")
print("=" * 120)

print(
    f"{'SYMBOL':<8}"
    f"{'TRADES':>8}"
    f"{'WIN%':>10}"
    f"{'PF':>10}"
    f"{'AVG-R':>10}"
    f"{'EXP':>12}"
    f"{'MAX-DD':>12}"
    f"{'BEST-R':>10}"
    f"{'WORST-R':>10}"
)

print("-" * 120)


for result in results:

    pf = result["profit_factor"]

    if pf == float("inf"):
        pf_display = "INF"
    else:
        pf_display = f"{pf:.2f}"

    print(
        f"{result['symbol']:<8}"
        f"{result['trades']:>8}"
        f"{result['win_rate']:>9.2f}%"
        f"{pf_display:>10}"
        f"{result['average_r']:>10.2f}"
        f"{result['expectancy']:>12.2f}"
        f"{result['max_drawdown_r']:>12.2f}"
        f"{result['best_r']:>10.2f}"
        f"{result['worst_r']:>10.2f}"
    )


# ==================================================
# SIMPLE CLASSIFICATION
# ==================================================

print("\n")
print("=" * 100)
print("OOS CLASSIFICATION")
print("=" * 100)

for result in results:

    trades = result["trades"]
    pf = result["profit_factor"]
    avg_r = result["average_r"]

    if trades < 10:

        status = "LOW SAMPLE"

    elif (
        pf >= 1.50
        and avg_r >= 0.20
    ):

        status = "STRONG"

    elif (
        pf > 1.00
        and avg_r > 0
    ):

        status = "POSITIVE"

    else:

        status = "WEAK"

    print(
        f"{result['symbol']:<8}: {status}"
    )

print("=" * 100)