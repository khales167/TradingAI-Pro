class DecisionEngine:

    def decide(self, analysis, market):

        score = analysis["score"]
        reasons = analysis["reasons"]
        adx = analysis["adx"]

        market_state = market.get("Overall", "Neutral")

        # =========================
        # DECISION ENGINE
        # =========================

        # ---------------------------------
        # BEARISH MARKET
        # ---------------------------------

        if market_state == "Bearish":

            if score >= 80 and adx >= 20:
                action = "WATCH"

            elif score >= 60:
                action = "WAIT"

            else:
                action = "SKIP"

        # ---------------------------------
        # BULLISH / NEUTRAL MARKET
        # ---------------------------------

        else:

            # BUY requires:
            # Score >= 80
            # ADX >= 20

            if score >= 80 and adx >= 20:
                action = "BUY"

            elif score >= 80:
                action = "WATCH"

            elif score >= 60:
                action = "WATCH"

            elif score >= 40:
                action = "WAIT"

            else:
                action = "SKIP"

        # =========================
        # QUALITY RATING
        # =========================

        if score >= 90:
            quality = "A+"

        elif score >= 80:
            quality = "A"

        elif score >= 70:
            quality = "B+"

        elif score >= 60:
            quality = "B"

        elif score >= 50:
            quality = "C"

        else:
            quality = "D"

        # =========================
        # RESULT
        # =========================

        return {
            "action": action,
            "quality": quality,
            "reasons": reasons,
            "market": market_state
        }