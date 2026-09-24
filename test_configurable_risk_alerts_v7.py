from unittest.mock import patch

from core.risk_alert_engine import RiskAlertEngine


def make_summary(
    *,
    available_cash=500.0,
    current_portfolio_risk=0.0,
    max_portfolio_risk=15.0,
    open_slots=5,
    positions=None,
):
    return {
        "available_cash": available_cash,
        "current_portfolio_risk": current_portfolio_risk,
        "max_portfolio_risk": max_portfolio_risk,
        "open_slots": open_slots,
        "positions": positions or [],
    }


def main():
    print("\n========== CONFIGURABLE RISK ALERTS V7 TEST ==========")

    engine = RiskAlertEngine()

    with patch(
        "core.risk_alert_engine.PORTFOLIO_RISK_WARNING_PERCENT",
        70.0,
    ), patch(
        "core.risk_alert_engine.POSITION_EXPOSURE_WARNING_PERCENT",
        25.0,
    ), patch(
        "core.risk_alert_engine.LOW_CASH_WARNING_AMOUNT",
        150.0,
    ), patch(
        "core.risk_alert_engine.LOW_SLOT_WARNING_COUNT",
        2,
    ):
        result = engine.evaluate(
            make_summary(
                available_cash=140.0,
                current_portfolio_risk=10.5,
                max_portfolio_risk=15.0,
                open_slots=2,
                positions=[
                    {
                        "symbol": "TEST1",
                        "exposure_percent": 25.0,
                    }
                ],
            )
        )

    codes = {
        alert["code"]
        for alert in result["alerts"]
    }

    print(f"Risk Usage : {result['risk_usage_percent']:.2f}%")
    print(f"Alerts     : {result['alert_count']}")
    print(f"Codes      : {sorted(codes)}")

    assert result["risk_usage_percent"] == 70.0
    assert result["alert_count"] == 4
    assert codes == {
        "PORTFOLIO_RISK_HIGH",
        "LOW_OPEN_SLOTS",
        "LOW_AVAILABLE_CASH",
        "POSITION_EXPOSURE_HIGH",
    }

    print("\n========== RESULT ==========")
    print("PASS: RiskAlertEngine follows configurable thresholds.")
    print("PASS: No hard-coded V6 threshold is required for evaluation.")


if __name__ == "__main__":
    main()
