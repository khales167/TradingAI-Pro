class Backtester:

    def run(self, results):

        total = len(results)

        buys = 0
        watches = 0
        skips = 0

        for stock in results:

            action = stock["Decision"]

            if action == "BUY":
                buys += 1

            elif action == "WATCH":
                watches += 1

            else:
                skips += 1

        return {

            "Total": total,
            "BUY": buys,
            "WATCH": watches,
            "SKIP": skips

        }