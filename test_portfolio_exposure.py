from collections import defaultdict

from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


backtester = HistoricalBacktester()

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"


# ==================================================
# COLLECT OOS TRADES
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
# SORT
# ==================================================

all_trades.sort(
    key=lambda trade: trade["entry_date"]
)


# ==================================================
# MAX SIMULTANEOUS POSITIONS
# ==================================================

events = []

for trade in all_trades:

    events.append({
        "date": trade["entry_date"],
        "type": "ENTRY",
        "symbol": trade["symbol"]
    })

    events.append({
        "date": trade["exit_date"],
        "type": "EXIT",
        "symbol": trade["symbol"]
    })


# EXIT before ENTRY when same timestamp
events.sort(
    key=lambda event: (
        event["date"],
        0 if event["type"] == "EXIT" else 1
    )
)


open_positions = set()

max_simultaneous = 0
max_simultaneous_date = None
max_symbols = []


for event in events:

    symbol = event["symbol"]

    if event["type"] == "EXIT":

        open_positions.discard(symbol)

    else:

        open_positions.add(symbol)

        if len(open_positions) > max_simultaneous:

            max_simultaneous = len(
                open_positions
            )

            max_simultaneous_date = (
                event["date"]
            )

            max_symbols = sorted(
                open_positions.copy()
            )


# ==================================================
# NEW TRADES PER DAY
# ==================================================

entries_by_day = defaultdict(list)

for trade in all_trades:

    day = trade["entry_date"].date()

    entries_by_day[day].append(
        trade["symbol"]
    )


max_entries_day = 0
max_entries_date = None
max_entries_symbols = []


for day, symbols in entries_by_day.items():

    if len(symbols) > max_entries_day:

        max_entries_day = len(symbols)
        max_entries_date = day
        max_entries_symbols = symbols


# ==================================================
# OPEN RISK OVER TIME
#
# Every new trade starts with approximately 1R risk.
# This measures simultaneous initial-risk exposure.
# ==================================================

risk_events = []

for trade in all_trades:

    risk_events.append({
        "date": trade["entry_date"],
        "type": "ENTRY"
    })

    risk_events.append({
        "date": trade["exit_date"],
        "type": "EXIT"
    })


risk_events.sort(
    key=lambda event: (
        event["date"],
        0 if event["type"] == "EXIT" else 1
    )
)


open_risk_r = 0
max_open_risk_r = 0
max_open_risk_date = None


for event in risk_events:

    if event["type"] == "EXIT":

        open_risk_r = max(
            0,
            open_risk_r - 1
        )

    else:

        open_risk_r += 1

        if open_risk_r > max_open_risk_r:

            max_open_risk_r = open_risk_r
            max_open_risk_date = event["date"]


# ==================================================
# MOST FREQUENT OVERLAPPING PAIRS
# ==================================================

pair_counts = defaultdict(int)

for i, trade_a in enumerate(all_trades):

    for trade_b in all_trades[i + 1:]:

        if trade_a["symbol"] == trade_b["symbol"]:
            continue

        overlap = (
            trade_a["entry_date"] < trade_b["exit_date"]
            and
            trade_b["entry_date"] < trade_a["exit_date"]
        )

        if overlap:

            pair = tuple(
                sorted([
                    trade_a["symbol"],
                    trade_b["symbol"]
                ])
            )

            pair_counts[pair] += 1


top_pairs = sorted(
    pair_counts.items(),
    key=lambda item: item[1],
    reverse=True
)


# ==================================================
# DISPLAY
# ==================================================

print("\n")
print("=" * 80)
print("PORTFOLIO EXPOSURE ANALYSIS")
print("=" * 80)

print(
    f"Total OOS Trades           : "
    f"{len(all_trades)}"
)

print(
    f"Max Simultaneous Positions : "
    f"{max_simultaneous}"
)

print(
    f"Max Exposure Date          : "
    f"{max_simultaneous_date}"
)

print(
    f"Symbols At Max Exposure    : "
    f"{', '.join(max_symbols)}"
)

print(
    f"Estimated Max Open Risk    : "
    f"{max_open_risk_r}R"
)

print(
    f"Max Open Risk Date         : "
    f"{max_open_risk_date}"
)

print(
    f"Max New Trades In One Day  : "
    f"{max_entries_day}"
)

print(
    f"Date                       : "
    f"{max_entries_date}"
)

print(
    f"Symbols                    : "
    f"{', '.join(max_entries_symbols)}"
)

print("=" * 80)


print("\n")
print("=" * 80)
print("TOP OVERLAPPING SYMBOL PAIRS")
print("=" * 80)

for pair, count in top_pairs[:15]:

    print(
        f"{pair[0]:<8} + "
        f"{pair[1]:<8} : "
        f"{count} overlaps"
    )

print("=" * 80)