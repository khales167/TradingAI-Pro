class EarningsEngine:

    def analyze(self, symbol, earnings):

        for item in earnings:

            if item["symbol"] == symbol:

                hour = str(item.get("hour", "")).lower()

                if hour == "bmo":

                    return {
                        "risk": "HIGH",
                        "message": "Before Market Open"
                    }

                elif hour == "amc":

                    return {
                        "risk": "HIGH",
                        "message": "After Market Close"
                    }

                else:

                    return {
                        "risk": "MEDIUM",
                        "message": "Unknown Time"
                    }

        return {
            "risk": "LOW",
            "message": "No earnings today"
        }