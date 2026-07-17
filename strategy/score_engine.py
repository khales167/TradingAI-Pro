class ScoreEngine:

    def __init__(self):
        self.score = 0
        self.reasons = []

    def add_news(self, positive):
        if positive:
            self.score += 30
            self.reasons.append("✅ Positive News")

    def add_ma(self, ma19, ma38, ma209):
        if ma19 > ma38 > ma209:
            self.score += 25
            self.reasons.append("✅ MA Trend")

    def add_dmi(self, di_plus, di_minus, adx):
        if di_plus > di_minus and adx > 25:
            self.score += 20
            self.reasons.append("✅ DMI Confirmed")

    def add_volume(self, relative_volume):
        if relative_volume >= 2:
            self.score += 15
            self.reasons.append("✅ High Relative Volume")

    def add_pvp(self, above_pivot):
        if above_pivot:
            self.score += 10
            self.reasons.append("✅ Above Pivot")

    def result(self):
        return self.score, self.reasons