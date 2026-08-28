class TradeLevels:

    def __init__(self):

        # ATR Multipliers
        self.stop_multiplier = 1.5
        self.target_multiplier = 3.0

    def calculate(self, data):

        entry = data["price"]
        atr = data["ATR"]

        stop = round(
            entry - atr * self.stop_multiplier,
            2
        )

        target = round(
            entry + atr * self.target_multiplier,
            2
        )

        risk = round(entry - stop, 2)
        reward = round(target - entry, 2)

        if risk == 0:
            rr = 0
        else:
            rr = round(reward / risk, 2)

        return {

            "Entry": entry,
            "ATR": atr,
            "Stop": stop,
            "Target": target,
            "Risk": risk,
            "Reward": reward,
            "RR": rr

        }