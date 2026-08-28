from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"

CAPS = [2, 3, 4, 5, 999]


# ==================================================
# COLLECT ALL OOS TRADES
# ==================================================

all_trades = []

for symbol in WATCHLIST:

    print(f"Testing {symbol}...")

    try:

        trades = backtester.run(
            symbol,
            start_date=OOS_START,
            end_date=OOS_END
        )

        all_trades.extend(trades)

    except Exception as e:

        print(f"ERROR {symbol}: {e}")


# ==================================================
# SORT BY ENTRY DATE
# ==================================================

all_trades.sort(
    key=lambda trade: (
        trade["entry_date"],
        -trade["entry_score"],
        -trade["entry_adx"]
    )
)


# ==================================================
# APPLY POSITION CAP
# ==================================================

def apply_position_cap(trades, max_positions):

    accepted = []
    rejected = []

    open_trades = []

    for trade in trades:

        entry_date = trade["entry_date"]

        # Remove positions already closed before this entry
        open_trades = [
            open_trade
            for open_trade in open_trades
            if open_trade["exit_date"] > entry_date
        ]

        if len(open_trades) < max_positions:

            accepted.append(trade)
            open_trades.append(trade)

        else:

            rejected.append(trade)

    return accepted, rejected


# ==================================================
# PERFORMANCE FOR EACH CAP
# ==================================================

results = []

for cap in CAPS:

    accepted, rejected = apply_position_cap(
        all_trades,
        cap
    )

    # Important for correct drawdown calculation
    accepted.sort(
        key=lambda trade: trade["exit_date"]
    )

    performance = backtester.performance(
        accepted
    )

    results.append({
        "cap": cap,
        "accepted": len(accepted),
        "rejected": len(rejected),

        "win_rate": performance["win_rate"],
        "profit_factor": performance["profit_factor"],
        "average_r": performance["average_r"],
        "expectancy": performance["expectancy"],
        "max_drawdown_r": performance["max_drawdown_r"],

        "total_r": round(
            sum(
                trade["r_multiple"]
                for trade in accepted
            ),
            2
        )
    })


# ==================================================
# DISPLAY
# ==================================================

print("\n")
print("=" * 120)
print("POSITION CAP BACKTEST")
print("=" * 120)

print(
    f"{'MAX POS':<12}"
    f"{'TRADES':>10}"
    f"{'REJECTED':>12}"
    f"{'WIN%':>10}"
    f"{'PF':>10}"
    f"{'AVG-R':>10}"
    f"{'EXP':>12}"
    f"{'TOTAL-R':>12}"
    f"{'MAX-DD':>12}"
)

print("-" * 120)


for result in results:

    if result["cap"] == 999:
        cap_display = "UNLIMITED"
    else:
        cap_display = str(result["cap"])

    pf = result["profit_factor"]

    if pf == float("inf"):
        pf_display = "INF"
    else:
        pf_display = f"{pf:.2f}"

    print(
        f"{cap_display:<12}"
        f"{result['accepted']:>10}"
        f"{result['rejected']:>12}"
        f"{result['win_rate']:>9.2f}%"
        f"{pf_display:>10}"
        f"{result['average_r']:>10.2f}"
        f"{result['expectancy']:>12.2f}"
        f"{result['total_r']:>12.2f}"
        f"{result['max_drawdown_r']:>12.2f}"
    )

print("=" * 120)