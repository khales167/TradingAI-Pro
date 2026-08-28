import pandas as pd
import yfinance as yf

from backtest.historical_backtester import HistoricalBacktester
from config import WATCHLIST


# ==================================================
# SETTINGS
# ==================================================

OOS_START = "2024-01-01"
OOS_END = "2026-08-22"

# Extra history before OOS for MA50 warm-up
MARKET_START = "2023-09-01"

MARKET_SYMBOLS = [
    "SPY",
    "QQQ",
    "DIA"
]


backtester = HistoricalBacktester()


# ==================================================
# MARKET DATA
# ==================================================

def download_market_data(symbol):

    print(f"Downloading market regime data: {symbol}")

    df = yf.download(
        symbol,
        start=MARKET_START,
        end=OOS_END,
        auto_adjust=False,
        progress=False
    )

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.copy()

    close = df["Close"]

    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()

    return df


# ==================================================
# BUILD MARKET REGIME
# ==================================================

def build_market_regime():

    market_data = {}

    for symbol in MARKET_SYMBOLS:

        df = download_market_data(symbol)

        if df is not None:
            market_data[symbol] = df

    if len(market_data) != 3:

        raise RuntimeError(
            "Could not download all market ETFs."
        )

    # Common trading dates
    common_dates = (
        market_data["SPY"].index
        .intersection(market_data["QQQ"].index)
        .intersection(market_data["DIA"].index)
    )

    regimes = {}

    for date in common_dates:

        bullish = 0

        result = {}

        for symbol in MARKET_SYMBOLS:

            row = market_data[symbol].loc[date]

            close = float(row["Close"])
            ma20 = float(row["MA20"])
            ma50 = float(row["MA50"])

            if pd.isna(ma20) or pd.isna(ma50):

                trend = None

            elif close > ma20 > ma50:

                trend = "Bullish"
                bullish += 1

            elif close < ma20 < ma50:

                trend = "Bearish"

            else:

                trend = "Neutral"

            result[symbol] = trend

        # Same logic as market/sentiment.py
        if bullish >= 2:

            overall = "Bullish"

        elif bullish == 1:

            overall = "Neutral"

        else:

            overall = "Bearish"

        regimes[date] = {
            "SPY": result["SPY"],
            "QQQ": result["QQQ"],
            "DIA": result["DIA"],
            "Overall": overall
        }

    return regimes


# ==================================================
# GET REGIME FOR TRADE DATE
# ==================================================

def get_regime_for_date(date, regimes):

    date = pd.Timestamp(date)

    if date in regimes:
        return regimes[date]["Overall"]

    # If entry date not present, use most recent
    # market trading day before entry
    available_dates = [
        d
        for d in regimes.keys()
        if d <= date
    ]

    if not available_dates:
        return "Unknown"

    previous_date = max(available_dates)

    return regimes[previous_date]["Overall"]


# ==================================================
# RUN OOS BACKTEST
# ==================================================

print("\n" + "=" * 100)
print("OOS MARKET REGIME BACKTEST")
print("=" * 100)

regimes = build_market_regime()

regime_trades = {
    "Bullish": [],
    "Neutral": [],
    "Bearish": [],
    "Unknown": []
}

all_trades = []


for symbol in WATCHLIST:

    print(f"\nTesting {symbol}...")

    try:

        trades = backtester.run(
            symbol,
            start_date=OOS_START,
            end_date=OOS_END
        )

        for trade in trades:

            regime = get_regime_for_date(
                trade["entry_date"],
                regimes
            )

            trade["market_regime"] = regime

            regime_trades[regime].append(
                trade
            )

            all_trades.append(
                trade
            )

    except Exception as e:

        print(
            f"ERROR {symbol}: {e}"
        )


# ==================================================
# PERFORMANCE BY MARKET REGIME
# ==================================================

print("\n")
print("=" * 110)
print("OOS PERFORMANCE BY MARKET REGIME")
print("=" * 110)

print(
    f"{'REGIME':<12}"
    f"{'TRADES':>10}"
    f"{'WIN%':>12}"
    f"{'PF':>12}"
    f"{'AVG-R':>12}"
    f"{'EXP':>12}"
    f"{'MAX-DD':>12}"
)

print("-" * 110)


for regime in [
    "Bullish",
    "Neutral",
    "Bearish",
    "Unknown"
]:

    trades = regime_trades[regime]

    performance = backtester.performance(
        trades
    )

    pf = performance["profit_factor"]

    if pf == float("inf"):
        pf_display = "INF"
    else:
        pf_display = f"{pf:.2f}"

    print(
        f"{regime:<12}"
        f"{performance['total_trades']:>10}"
        f"{performance['win_rate']:>11.2f}%"
        f"{pf_display:>12}"
        f"{performance['average_r']:>12.2f}"
        f"{performance['expectancy']:>12.2f}"
        f"{performance['max_drawdown_r']:>12.2f}"
    )


# ==================================================
# GLOBAL OOS
# ==================================================
all_trades.sort(
    key=lambda trade: trade["exit_date"]
)

regime_trades["Bullish"].sort(
    key=lambda trade: trade["exit_date"]
)
global_performance = backtester.performance(
    all_trades
)
bullish_only_performance = backtester.performance(
    regime_trades["Bullish"]
)
print("\n")
print("=" * 70)
print("GLOBAL OOS PERFORMANCE")
print("=" * 70)

print(
    f"Total Trades       : "
    f"{global_performance['total_trades']}"
)

print(
    f"Win Rate           : "
    f"{global_performance['win_rate']:.2f}%"
)

print(
    f"Profit Factor      : "
    f"{global_performance['profit_factor']}"
)

print(
    f"Average R          : "
    f"{global_performance['average_r']:.2f}R"
)

print(
    f"Max Drawdown       : "
    f"{global_performance['max_drawdown_r']:.2f}R"
)

print("=" * 70)
print("\n")
print("=" * 90)
print("GLOBAL vs BULLISH-ONLY")
print("=" * 90)

print(
    f"{'METRIC':<25}"
    f"{'GLOBAL':>20}"
    f"{'BULLISH ONLY':>20}"
)

print("-" * 90)


def compare(label, global_value, bullish_value):

    print(
        f"{label:<25}"
        f"{str(global_value):>20}"
        f"{str(bullish_value):>20}"
    )


compare(
    "Total Trades",
    global_performance["total_trades"],
    bullish_only_performance["total_trades"]
)

compare(
    "Win Rate %",
    global_performance["win_rate"],
    bullish_only_performance["win_rate"]
)

compare(
    "Profit Factor",
    global_performance["profit_factor"],
    bullish_only_performance["profit_factor"]
)

compare(
    "Average R",
    global_performance["average_r"],
    bullish_only_performance["average_r"]
)

compare(
    "Expectancy",
    global_performance["expectancy"],
    bullish_only_performance["expectancy"]
)

compare(
    "Max Drawdown R",
    global_performance["max_drawdown_r"],
    bullish_only_performance["max_drawdown_r"]
)

compare(
    "Total P/L",
    global_performance["total_pl"],
    bullish_only_performance["total_pl"]
)

print("=" * 90)