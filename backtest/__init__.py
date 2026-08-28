import pandas as pd
import yfinance as yf

from ta.trend import SMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange

from config import (
    MA_FAST,
    MA_MID,
    MA_SLOW,
    ADX_PERIOD,
    ADX_LIMIT,
    RVOL_LIMIT,
    TREND_SCORE,
    DMI_SCORE,
    ADX_SCORE,
    RVOL_SCORE
)


class HistoricalBacktester:

    def __init__(
        self,
        stop_multiplier=1.5,
        target_multiplier=3.0,
        trailing_atr_multiplier=1.0
    ):

        self.stop_multiplier = stop_multiplier
        self.target_multiplier = target_multiplier
        self.trailing_atr_multiplier = trailing_atr_multiplier

    # ==================================================
    # DOWNLOAD DATA
    # ==================================================

    def get_data(self, symbol, period="2y"):

        print(f"Downloading historical data for {symbol}...")

        df = yf.download(
            symbol,
            period=period,
            auto_adjust=False,
            progress=False
        )

        if df is None or df.empty:
            return None

        # Fix yfinance MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df.copy()

    # ==================================================
    # HISTORICAL INDICATORS
    # ==================================================

    def calculate_indicators(self, df):

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # Moving averages
        df["MA19"] = SMAIndicator(
            close,
            window=MA_FAST
        ).sma_indicator()

        df["MA38"] = SMAIndicator(
            close,
            window=MA_MID
        ).sma_indicator()

        df["MA209"] = SMAIndicator(
            close,
            window=MA_SLOW
        ).sma_indicator()

        # ADX / DMI
        adx = ADXIndicator(
            high=high,
            low=low,
            close=close,
            window=ADX_PERIOD
        )

        df["ADX"] = adx.adx()
        df["DI+"] = adx.adx_pos()
        df["DI-"] = adx.adx_neg()

        # ATR
        atr = AverageTrueRange(
            high=high,
            low=low,
            close=close,
            window=14
        )

        df["ATR"] = atr.average_true_range()

        # Historical RVOL
        # shift(1) مهم باش ما نستعملوش volume ديال نفس اليوم
        df["AVG_VOLUME_20"] = (
            volume
            .rolling(20)
            .mean()
            .shift(1)
        )

        df["RVOL"] = (
            volume / df["AVG_VOLUME_20"]
        )

        return df

    # ==================================================
    # TECHNICAL SCORE
    # ==================================================

    def calculate_score(self, row):

        score = 0
        reasons = []

        if (
            row["MA19"]
            > row["MA38"]
            > row["MA209"]
        ):
            score += TREND_SCORE
            reasons.append("Trend")

        if row["DI+"] > row["DI-"]:
            score += DMI_SCORE
            reasons.append("DI+")

        if row["ADX"] > ADX_LIMIT:
            score += ADX_SCORE
            reasons.append("ADX")

        if row["RVOL"] >= RVOL_LIMIT:
            score += RVOL_SCORE
            reasons.append("RVOL")

        return score, reasons

    # ==================================================
    # CLOSE TRADE
    # ==================================================

    def close_trade(
        self,
        trade,
        exit_price,
        exit_date,
        exit_reason
    ):

        trade["exit_price"] = round(
            float(exit_price),
            2
        )

        trade["exit_date"] = exit_date
        trade["exit_reason"] = exit_reason

        trade["pl"] = round(
            trade["exit_price"]
            - trade["entry"],
            2
        )

        trade["pl_percent"] = round(
            (
                trade["exit_price"]
                - trade["entry"]
            )
            / trade["entry"]
            * 100,
            2
        )

        if trade["initial_risk"] > 0:
            trade["r_multiple"] = round(
                trade["pl"]
                / trade["initial_risk"],
                2
            )
        else:
            trade["r_multiple"] = 0

    # ==================================================
    # RUN BACKTEST
    # ==================================================

    def run(self, symbol, period="2y"):

        df = self.get_data(symbol, period)

        if df is None:
            print("No historical data.")
            return []

        df = self.calculate_indicators(df)

        # MA209 needs enough history
        df = df.dropna().copy()

        trades = []
        position = None

        for i in range(len(df) - 1):

            row = df.iloc[i]
            next_row = df.iloc[i + 1]

            # ==========================================
            # MANAGE OPEN POSITION
            # ==========================================

            if position is not None:

                high = float(row["High"])
                low = float(row["Low"])
                close = float(row["Close"])
                atr = float(row["ATR"])

                # STOP HIT
                if low <= position["stop"]:

                    self.close_trade(
                        position,
                        position["stop"],
                        df.index[i],
                        "STOP"
                    )

                    trades.append(position)
                    position = None
                    continue

                # TARGET HIT
                if high >= position["target"]:

                    self.close_trade(
                        position,
                        position["target"],
                        df.index[i],
                        "TARGET"
                    )

                    trades.append(position)
                    position = None
                    continue

                # BREAK-EVEN at +1R
                if not position["break_even"]:

                    if high >= position["break_even_trigger"]:

                        position["stop"] = position["entry"]
                        position["break_even"] = True

                # TRAILING STOP after break-even
                if position["break_even"]:

                    trailing_stop = (
                        close
                        - atr * self.trailing_atr_multiplier
                    )

                    if trailing_stop > position["stop"]:
                        position["stop"] = trailing_stop

                continue

            # ==========================================
            # NEW SIGNAL
            # ==========================================

            score, reasons = self.calculate_score(row)

            adx_value = float(row["ADX"])

            # Same BUY filter as current DecisionEngine
            if (
                score >= 80
                and adx_value >= 20
            ):

                # Entry at next candle open
                entry = float(next_row["Open"])

                atr = float(row["ATR"])

                stop = (
                    entry
                    - atr * self.stop_multiplier
                )

                target = (
                    entry
                    + atr * self.target_multiplier
                )

                initial_risk = entry - stop

                break_even_trigger = (
                    entry + initial_risk
                )

                position = {
                    "symbol": symbol,

                    "entry_date": df.index[i + 1],

                    "entry": round(entry, 2),

                    "initial_stop": round(stop, 2),
                    "stop": round(stop, 2),

                    "target": round(target, 2),

                    "initial_risk": round(
                        initial_risk,
                        2
                    ),

                    "break_even_trigger": round(
                        break_even_trigger,
                        2
                    ),

                    "break_even": False,

                    "entry_score": score,

                    "entry_adx": round(
                        adx_value,
                        2
                    ),

                    "reasons": reasons
                }

        # Close any position still open
        if position is not None:

            last = df.iloc[-1]

            self.close_trade(
                position,
                float(last["Close"]),
                df.index[-1],
                "END"
            )

            trades.append(position)

        return trades

    # ==================================================
    # PERFORMANCE
    # ==================================================

    def performance(self, trades):

        if not trades:

            return {
                "total_trades": 0,
                "winners": 0,
                "losers": 0,
                "win_rate": 0,
                "total_pl": 0,
                "average_pl": 0,
                "average_win": 0,
                "average_loss": 0,
                "profit_factor": 0,
                "expectancy": 0,
                "average_r": 0
            }

        wins = [
            trade["pl"]
            for trade in trades
            if trade["pl"] > 0
        ]

        losses = [
            trade["pl"]
            for trade in trades
            if trade["pl"] < 0
        ]

        total_trades = len(trades)

        winners = len(wins)
        losers = len(losses)

        total_pl = sum(
            trade["pl"]
            for trade in trades
        )

        average_pl = total_pl / total_trades

        win_rate = (
            winners / total_trades
        ) * 100

        average_win = (
            sum(wins) / len(wins)
            if wins
            else 0
        )

        average_loss = (
            sum(losses) / len(losses)
            if losses
            else 0
        )

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))

        if gross_loss > 0:
            profit_factor = (
                gross_profit / gross_loss
            )

        elif gross_profit > 0:
            profit_factor = float("inf")

        else:
            profit_factor = 0

        average_r = (
            sum(
                trade["r_multiple"]
                for trade in trades
            )
            / total_trades
        )

        return {
            "total_trades": total_trades,
            "winners": winners,
            "losers": losers,

            "win_rate": round(
                win_rate,
                2
            ),

            "total_pl": round(
                total_pl,
                2
            ),

            "average_pl": round(
                average_pl,
                2
            ),

            "average_win": round(
                average_win,
                2
            ),

            "average_loss": round(
                average_loss,
                2
            ),

            "profit_factor": (
                round(profit_factor, 2)
                if profit_factor != float("inf")
                else float("inf")
            ),

            "expectancy": round(
                average_pl,
                2
            ),

            "average_r": round(
                average_r,
                2
            )
        }