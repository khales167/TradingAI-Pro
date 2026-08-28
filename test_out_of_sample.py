from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()


# ==================================================
# PERIODS
# ==================================================

TRAIN_START = "2021-01-01"
TRAIN_END = "2024-01-01"

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"


# ==================================================
# HELPER
# ==================================================

def run_period(name, start_date, end_date):

    print("\n" + "=" * 90)
    print(name)
    print("=" * 90)

    all_trades = []

    for symbol in WATCHLIST:

        print(
            f"\nTesting {symbol} "
            f"from {start_date} to {end_date}"
        )

        try:

            trades = backtester.run(
                symbol,
                start_date=start_date,
                end_date=end_date
            )

            all_trades.extend(trades)

        except Exception as e:

            print(
                f"ERROR {symbol}: {e}"
            )

    performance = backtester.performance(
        all_trades
    )

    return performance


# ==================================================
# TRAIN
# ==================================================

train = run_period(
    "TRAIN PERIOD",
    TRAIN_START,
    TRAIN_END
)


# ==================================================
# OUT OF SAMPLE
# ==================================================

oos = run_period(
    "OUT-OF-SAMPLE PERIOD",
    OOS_START,
    OOS_END
)


# ==================================================
# COMPARISON
# ==================================================

print("\n")
print("=" * 100)
print("TRAIN VS OUT-OF-SAMPLE")
print("=" * 100)

print(
    f"{'METRIC':<25}"
    f"{'TRAIN':>20}"
    f"{'OUT-OF-SAMPLE':>20}"
)

print("-" * 100)


def show_metric(label, train_value, oos_value):

    print(
        f"{label:<25}"
        f"{str(train_value):>20}"
        f"{str(oos_value):>20}"
    )


show_metric(
    "Total Trades",
    train["total_trades"],
    oos["total_trades"]
)

show_metric(
    "Winners",
    train["winners"],
    oos["winners"]
)

show_metric(
    "Losers",
    train["losers"],
    oos["losers"]
)

show_metric(
    "Break-even",
    train["break_even_trades"],
    oos["break_even_trades"]
)

show_metric(
    "Win Rate %",
    train["win_rate"],
    oos["win_rate"]
)

show_metric(
    "Profit Factor",
    train["profit_factor"],
    oos["profit_factor"]
)

show_metric(
    "Average R",
    train["average_r"],
    oos["average_r"]
)

show_metric(
    "Expectancy",
    train["expectancy"],
    oos["expectancy"]
)

show_metric(
    "Total P/L",
    train["total_pl"],
    oos["total_pl"]
)

show_metric(
    "Best Trade R",
    train["best_r"],
    oos["best_r"]
)

show_metric(
    "Worst Trade R",
    train["worst_r"],
    oos["worst_r"]
)

show_metric(
    "Max Drawdown R",
    train["max_drawdown_r"],
    oos["max_drawdown_r"]
)

print("=" * 100)