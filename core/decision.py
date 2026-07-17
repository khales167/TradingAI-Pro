class DecisionEngine:

    def decide(self, analysis, market):

        score = analysis["score"]
        reasons = analysis["reasons"]

        market_state = market["Overall"]

        # إذا السوق هابط لا نسمح بالشراء
        if market_state == "Bearish":

            if score >= 80:
                action = "WATCH"

            elif score >= 60:
                action = "WAIT"

            else:
                action = "SKIP"

        else:

            if score >= 80:
                action = "BUY"

            elif score >= 60:
                action = "WATCH"

            elif score >= 40:
                action = "WAIT"

            else:
                action = "SKIP"

        return {
            "action": action,
            "reasons": reasons,
            "market": market_state
        }