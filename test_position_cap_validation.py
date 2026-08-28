from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

MAX_POSITIONS = 5

PERIODS = {
    "TRAIN": {
        "start": "2021-01-01",
        "end": "2024-01-01"
    },

    "OOS": {
        "start": "2024-01-01",
        "end": "2026-08-22"
    }
}


# ==================================================
# APPLY POSITION CAP
# ==================================================

def apply_position_cap(trades, max_positions):

    # Ranking:
    # 1. Entry date
    # 2. Higher entry score
    # 3. Higher ADX

    trades = sorted(
        trades,
        key=lambda trade: (
            trade["entry_date"],
            -trade.get("entry_score", 0),
            -trade.get("entry_adx", 0)
        )
    )

    accepted = []
    rejected = []
    open_trades = []

    for trade in trades:

        entry_date = trade["entry_date"]

        # Free positions that already exited
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
# CALCULATE RESULT
# ==================================================

def calculate_result(trades):

    # Drawdown must follow actual exit chronology
    trades = sorted(
        trades,
        key=lambda trade: trade["exit_date"]
    )

    performance = backtester.performance(trades)

    total_r = round(
        sum(
            trade["r_multiple"]
            for trade in trades
        ),
        2
    )

    return {
        "trades": len(trades),
        "win_rate": performance["win_rate"],
        "pf": performance["profit_factor"],
        "avg_r": performance["average_r"],
        "expectancy": performance["expectancy"],
        "total_r": total_r,
        "max_dd": performance["max_drawdown_r"]
    }


# ==================================================
# RUN PERIOD
# ==================================================

def run_period(name, start_date, end_date):

    print("\n")
    print("=" * 80)
    print(f"DOWNLOADING {name}")
    print(f"{start_date} -> {end_date}")
    print("=" * 80)

    all_trades = []

    for symbol in WATCHLIST:

        print(f"Testing {symbol}...")

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

    # ------------------------------
    # UNLIMITED
    # ------------------------------

    unlimited = calculate_result(
        all_trades
    )

    # ------------------------------
    # MAX 5
    # ------------------------------

    accepted, rejected = apply_position_cap(
        all_trades,
        MAX_POSITIONS
    )

    capped = calculate_result(
        accepted
    )

    capped["rejected"] = len(rejected)

    return {
        "name": name,
        "unlimited": unlimited,
        "max5": capped
    }


# ==================================================
# RUN TRAIN + OOS
# ==================================================

results = []

for name, dates in PERIODS.items():

    result = run_period(
        name,
        dates["start"],
        dates["end"]
    )

    results.append(result)


# ==================================================
# DISPLAY
# ==================================================

print("\n\n")
print("=" * 118)
print("POSITION CAP = 5 VALIDATION")
print("=" * 118)

print(
    f"{'PERIOD':<10}"
    f"{'MODE':<12}"
    f"{'TRADES':>9}"
    f"{'REJECT':>9}"
    f"{'WIN%':>10}"
    f"{'PF':>9}"
    f"{'AVG-R':>10}"
    f"{'EXP':>11}"
    f"{'TOTAL-R':>11}"
    f"{'MAX-DD':>11}"
)

print("-" * 118)


for result in results:

    name = result["name"]

    # Unlimited
    u = result["unlimited"]

    print(
        f"{name:<10}"
        f"{'Unlimited':<12}"
        f"{u['trades']:>9}"
        f"{0:>9}"
        f"{u['win_rate']:>9.2f}%"
        f"{u['pf']:>9.2f}"
        f"{u['avg_r']:>10.2f}"
        f"{u['expectancy']:>11.2f}"
        f"{u['total_r']:>11.2f}"
        f"{u['max_dd']:>11.2f}"
    )

    # Max 5
    c = result["max5"]

    print(
        f"{name:<10}"
        f"{'Max 5':<12}"
        f"{c['trades']:>9}"
        f"{c['rejected']:>9}"
        f"{c['win_rate']:>9.2f}%"
        f"{c['pf']:>9.2f}"
        f"{c['avg_r']:>10.2f}"
        f"{c['expectancy']:>11.2f}"
        f"{c['total_r']:>11.2f}"
        f"{c['max_dd']:>11.2f}"
    )

    print("-" * 118)

print("=" * 118)