from collections import defaultdict
from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"


# ==================================================
# COLLECT ALL OOS TRADES
# ==================================================

all_trades = []

for symbol in WATCHLIST:

    print(f"Testing {symbol}...")

    trades = backtester.run(
        symbol,
        start_date=OOS_START,
        end_date=OOS_END
    )

    all_trades.extend(trades)


# ==================================================
# SORT CHRONOLOGICALLY
# ==================================================

all_trades.sort(
    key=lambda trade: trade["exit_date"]
)


# ==================================================
# MAX DRAWDOWN
# ==================================================

equity_r = 0.0
peak_r = 0.0
peak_date = None

max_drawdown_r = 0.0
dd_start_date = None
dd_bottom_date = None

current_dd_start_date = None

equity_curve = []

for trade in all_trades:

    equity_r += trade["r_multiple"]

    exit_date = trade["exit_date"]

    if equity_r > peak_r:

        peak_r = equity_r
        peak_date = exit_date
        current_dd_start_date = exit_date

    drawdown = peak_r - equity_r

    equity_curve.append({
        "date": exit_date,
        "equity_r": equity_r,
        "drawdown_r": drawdown,
        "symbol": trade["symbol"],
        "r_multiple": trade["r_multiple"]
    })

    if drawdown > max_drawdown_r:

        max_drawdown_r = drawdown
        dd_start_date = current_dd_start_date
        dd_bottom_date = exit_date


# ==================================================
# RECOVERY DATE
# ==================================================

recovery_date = None

if dd_bottom_date is not None:

    bottom_found = False

    for point in equity_curve:

        if point["date"] == dd_bottom_date:
            bottom_found = True

        if (
            bottom_found
            and point["drawdown_r"] <= 0
        ):
            recovery_date = point["date"]
            break


# ==================================================
# TRADES INSIDE MAX DRAWDOWN
# ==================================================

dd_trades = []

if dd_start_date is not None and dd_bottom_date is not None:

    for trade in all_trades:

        if (
            trade["exit_date"] >= dd_start_date
            and trade["exit_date"] <= dd_bottom_date
        ):
            dd_trades.append(trade)


# ==================================================
# SYMBOL CONTRIBUTION DURING DRAWDOWN
# ==================================================

symbol_contribution = defaultdict(float)
symbol_trade_count = defaultdict(int)

for trade in dd_trades:

    symbol = trade["symbol"]

    symbol_contribution[symbol] += trade["r_multiple"]
    symbol_trade_count[symbol] += 1


# ==================================================
# LONGEST LOSING STREAK
# ==================================================

current_losing_streak = 0
longest_losing_streak = 0

streak_start = None
longest_streak_start = None
longest_streak_end = None

for trade in all_trades:

    if trade["r_multiple"] < 0:

        if current_losing_streak == 0:
            streak_start = trade["exit_date"]

        current_losing_streak += 1

        if current_losing_streak > longest_losing_streak:

            longest_losing_streak = current_losing_streak
            longest_streak_start = streak_start
            longest_streak_end = trade["exit_date"]

    else:

        current_losing_streak = 0
        streak_start = None


# ==================================================
# DISPLAY
# ==================================================

print("\n")
print("=" * 80)
print("MAX DRAWDOWN ANALYSIS")
print("=" * 80)

print(f"Total Trades          : {len(all_trades)}")
print(f"Max Drawdown          : {max_drawdown_r:.2f}R")
print(f"Drawdown Start        : {dd_start_date}")
print(f"Drawdown Bottom       : {dd_bottom_date}")
print(f"Recovery Date         : {recovery_date}")
print(f"Trades In Drawdown    : {len(dd_trades)}")

print(f"Longest Losing Streak : {longest_losing_streak}")
print(f"Streak Start          : {longest_streak_start}")
print(f"Streak End            : {longest_streak_end}")

print("=" * 80)


print("\n")
print("=" * 80)
print("SYMBOL CONTRIBUTION DURING MAX DRAWDOWN")
print("=" * 80)

sorted_symbols = sorted(
    symbol_contribution.items(),
    key=lambda x: x[1]
)

for symbol, contribution in sorted_symbols:

    count = symbol_trade_count[symbol]

    print(
        f"{symbol:<8}"
        f" Trades: {count:<4}"
        f" Contribution: {contribution:>8.2f}R"
    )

print("=" * 80)


print("\n")
print("=" * 100)
print("TRADES DURING MAX DRAWDOWN")
print("=" * 100)

print(
    f"{'DATE':<25}"
    f"{'SYMBOL':<10}"
    f"{'R':>10}"
    f"{'P/L':>12}"
    f"{'EXIT REASON':>18}"
)

print("-" * 100)

for trade in dd_trades:

    print(
        f"{str(trade['exit_date']):<25}"
        f"{trade['symbol']:<10}"
        f"{trade['r_multiple']:>10.2f}"
        f"{trade['pl']:>12.2f}"
        f"{trade['exit_reason']:>18}"
    )

print("=" * 100)