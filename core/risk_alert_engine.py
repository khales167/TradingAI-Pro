class RiskAlertEngine:

    def evaluate(self, summary):
        alerts = []

        max_risk = summary["max_portfolio_risk"]
        current_risk = summary["current_portfolio_risk"]

        risk_usage_percent = (
            (current_risk / max_risk) * 100
            if max_risk > 0
            else 0.0
        )

        if risk_usage_percent >= 80:
            alerts.append({
                "level": "WARNING",
                "code": "PORTFOLIO_RISK_HIGH",
                "message": (
                    f"Portfolio risk usage is "
                    f"{risk_usage_percent:.1f}% of limit."
                ),
            })

        if summary["open_slots"] <= 1:
            alerts.append({
                "level": "WARNING",
                "code": "LOW_OPEN_SLOTS",
                "message": (
                    f"Only {summary['open_slots']} "
                    f"portfolio slot(s) remaining."
                ),
            })

        if summary["available_cash"] < 100:
            alerts.append({
                "level": "WARNING",
                "code": "LOW_AVAILABLE_CASH",
                "message": (
                    f"Available cash is low: "
                    f"${summary['available_cash']:.2f}."
                ),
            })

        for position in summary["positions"]:
            if position["exposure_percent"] >= 35:
                alerts.append({
                    "level": "WARNING",
                    "code": "POSITION_EXPOSURE_HIGH",
                    "symbol": position["symbol"],
                    "message": (
                        f"{position['symbol']} exposure is "
                        f"{position['exposure_percent']:.2f}%."
                    ),
                })

        return {
            "risk_usage_percent": round(
                float(risk_usage_percent),
                2
            ),
            "alerts": alerts,
            "alert_count": len(alerts),
        }
