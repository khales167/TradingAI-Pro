from datetime import datetime

from core.data_manager import DataManager
from core.analyzer import Analyzer
from core.decision import DecisionEngine
from core.database import DatabaseManager

from indicators.indicators import calculate_indicators


class PortfolioMonitor:

    def __init__(self):

        self.data = DataManager()
        self.analyzer = Analyzer()
        self.decision = DecisionEngine()
        self.db = DatabaseManager()

    def analyze_position(self, position, market):

        symbol = position["symbol"]
        entry = position["entry_price"]
        stop = position["stop_price"]
        target = position["target_price"]
        quantity = position["quantity"]

        break_even_activated = position["break_even_activated"]

        print(f"\nAnalyzing {symbol} ...")

        try:

            # ==========================================
            # DOWNLOAD MARKET DATA
            # ==========================================

            df = self.data.get_data(symbol)

            if df is None or df.empty:
                print("No market data.")
                return None

            # ==========================================
            # CALCULATE INDICATORS
            # ==========================================

            data = calculate_indicators(
                symbol,
                df
            )

            if data is None:
                print("No indicator data.")
                return None

            current = data["price"]

            # ==========================================
            # CURRENT P/L
            # ==========================================

            pl = (
                current - entry
            ) * quantity

            pl_percent = (
                (current - entry)
                / entry
            ) * 100

            # ==========================================
            # ANALYZER
            # ==========================================

            analysis = self.analyzer.analyze(
                data,
                symbol
            )

            # ==========================================
            # DECISION
            # ==========================================

            decision = self.decision.decide(
                analysis,
                market
            )

            # ==========================================
            # BREAK-EVEN LEVEL
            # ==========================================

            initial_risk = entry - stop

            break_even_trigger = None

            print("\n========== DEBUG BREAK-EVEN ==========")
            print(f"Symbol               : {symbol}")
            print(f"Entry                : {entry}")
            print(f"Stop                 : {stop}")
            print(f"Current              : {current}")
            print(f"Break-even Activated : {break_even_activated}")
            print(f"Initial Risk         : {initial_risk}")

            if (
                not break_even_activated
                and initial_risk > 0
            ):

                break_even_trigger = (
                    entry + initial_risk
                )

                print(
                    f"Break-even Trigger   : "
                    f"{break_even_trigger}"
                )

            else:

                print(
                    "Break-even Trigger   : "
                    "NOT AVAILABLE"
                )

            print("======================================")

            # ==========================================
            # POSITION STATUS
            # ==========================================

            trade_status = "HOLD"

            exit_date = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ==========================================
            # 1. STOP HIT
            # ==========================================

            if current <= stop:

                trade_status = "EXIT - STOP HIT"

                self.db.close_position(
                    symbol,
                    current,
                    exit_date
                )

            # ==========================================
            # 2. TARGET HIT
            # ==========================================

            elif current >= target:

                trade_status = "EXIT - TARGET HIT"

                self.db.close_position(
                    symbol,
                    current,
                    exit_date
                )

            # ==========================================
            # 3. BREAK-EVEN AT +1R
            # ==========================================

            elif (
                break_even_trigger is not None
                and current >= break_even_trigger
            ):

                print(
                    f"\n✅ BREAK-EVEN CONDITION MET "
                    f"for {symbol}"
                )

                self.db.activate_break_even(
                    symbol,
                    entry
                )

                stop = entry

                break_even_activated = 1

                trade_status = "BREAK-EVEN ACTIVE"
            # ==========================================
            # 4. TRAILING STOP
            # ==========================================

            if (
                break_even_activated
                and trade_status not in [
                    "EXIT - STOP HIT",
                    "EXIT - TARGET HIT"
            ]
    ):

                atr = analysis["atr"]

                trailing_stop = current - atr

             # Trailing stop يتحرك غير للأعلى
                if trailing_stop > stop:

                   self.db.update_stop(
                        symbol,
                        trailing_stop
               )

                   stop = trailing_stop

                   trade_status = "TRAILING STOP UPDATED"  

            # ==========================================
            # 4. TECHNICAL WEAKNESS
            # ==========================================

            elif decision["action"] == "SKIP":

                trade_status = "REVIEW / EXIT"

            elif decision["action"] == "WATCH":

                trade_status = "WATCH"

            else:

                trade_status = "HOLD"

            # ==========================================
            # DISPLAY
            # ==========================================

            print(
                f"\nBreak-even    : "
                f"{'ACTIVE' if break_even_activated else 'OFF'}"
            )

            if break_even_trigger is not None:

                print(
                    f"BE Trigger    : "
                    f"{break_even_trigger:.2f}"
                )

            print(
                "\n========== PORTFOLIO MONITOR =========="
            )

            print(
                f"Symbol        : {symbol}"
            )

            print(
                f"Entry         : {entry:.2f}"
            )

            print(
                f"Current       : {current:.2f}"
            )

            print(
                f"Stop          : {stop:.2f}"
            )

            print(
                f"Target        : {target:.2f}"
            )

            print(
                f"Quantity      : {quantity}"
            )

            print(
                f"P/L           : ${pl:.2f}"
            )

            print(
                f"P/L %         : {pl_percent:.2f}%"
            )

            print(
                f"Score         : {analysis['score']}"
            )

            print(
                f"Confidence    : "
                f"{analysis['confidence']}%"
            )

            print(
                f"Decision      : "
                f"{decision['action']}"
            )

            print(
                f"Quality       : "
                f"{decision['quality']}"
            )

            print(
                f"Market        : "
                f"{decision['market']}"
            )

            print(
                f"ADX           : "
                f"{analysis['adx']:.2f}"
            )

            print(
                f"DI+           : "
                f"{analysis['di_plus']:.2f}"
            )

            print(
                f"DI-           : "
                f"{analysis['di_minus']:.2f}"
            )

            print(
                f"RVOL          : "
                f"{analysis['rvol']:.2f}"
            )

            print(
                f"ATR           : "
                f"{analysis['atr']:.2f}"
            )

            print(
                "Reasons       :",
                ", ".join(
                    analysis["reasons"]
                )
            )

            print(
                f"Trade Status  : "
                f"{trade_status}"
            )

            print(
                "======================================"
            )

            return {
                "symbol": symbol,
                "current": current,
                "pl": round(pl, 2),
                "pl_percent": round(
                    pl_percent,
                    2
                ),
                "decision": decision["action"],
                "trade_status": trade_status,
                "break_even_activated":
                    break_even_activated,
                "break_even_trigger":
                    break_even_trigger
            }

        except Exception as e:

            print(
                f"{symbol} -> {e}"
            )

            return None