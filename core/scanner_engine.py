from indicators.indicators import calculate_indicators


class ScannerEngine:

    def __init__(
        self,
        data_manager,
        analyzer,
        decision,
        risk
    ):

        self.data_manager = data_manager
        self.analyzer = analyzer
        self.decision = decision
        self.risk = risk

    def scan_symbol(self, symbol, market):

        try:

            df = self.data_manager.get_data(symbol)

            if df is None:
                return None
            
            df = df.copy()

            data = calculate_indicators(symbol, df)
            print(f"DEBUG {symbol}: {data['price']}")

            if data is None:
                return None

            analysis = self.analyzer.analyze(data)

            decision = self.decision.decide(
                analysis,
                market
            )

            risk = self.risk.calculate(data)

            return {

                "Symbol": symbol,

                "Price": data["price"],

                "ADX": data["ADX"],
                "ATR": risk["ATR"],
                "RVOL": data["RVOL"],

                "Entry": risk["Entry"],
                "Stop": risk["Stop"],
                "Target": risk["Target"],
                "RR": risk["RR"],

                "Score": analysis["score"],
                "Confidence": analysis["confidence"],

                "Decision": decision["action"],
                "Market": decision["market"],
                "Reasons": ", ".join(decision["reasons"])

            }

        except Exception as e:

            print(f"Error scanning {symbol}: {e}")

            return None