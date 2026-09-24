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
    print("\n========== RISK ALERTS V6 TEST ==========")

    engine = RiskAlertEngine()

    safe = engine.evaluate(make_summary())

    print("\nSafe state")
    print(f"Risk Usage : {safe['risk_usage_percent']:.2f}%")
    print(f"Alerts     : {safe['alert_count']}")

    assert safe["risk_usage_percent"] == 0.0
    assert safe["alert_count"] == 0
    assert safe["alerts"] == []

    high_risk = engine.evaluate(
        make_summary(
            current_portfolio_risk=12.0,
            max_portfolio_risk=15.0,
        )
    )

    print("\nPortfolio risk threshold")
    print(f"Risk Usage : {high_risk['risk_usage_percent']:.2f}%")
    print(f"Alerts     : {high_risk['alert_count']}")

    assert high_risk["risk_usage_percent"] == 80.0
    assert any(
        alert["code"] == "PORTFOLIO_RISK_HIGH"
        for alert in high_risk["alerts"]
    )

    low_slots = engine.evaluate(
        make_summary(open_slots=1)
    )

    assert any(
        alert["code"] == "LOW_OPEN_SLOTS"
        for alert in low_slots["alerts"]
    )

    low_cash = engine.evaluate(
        make_summary(available_cash=99.99)
    )

    assert any(
        alert["code"] == "LOW_AVAILABLE_CASH"
        for alert in low_cash["alerts"]
    )

    high_exposure = engine.evaluate(
        make_summary(
            positions=[
                {
                    "symbol": "TEST1",
                    "exposure_percent": 35.0,
                }
            ]
        )
    )

    assert any(
        alert["code"] == "POSITION_EXPOSURE_HIGH"
        and alert.get("symbol") == "TEST1"
        for alert in high_exposure["alerts"]
    )

    combined = engine.evaluate(
        make_summary(
            available_cash=50.0,
            current_portfolio_risk=13.5,
            max_portfolio_risk=15.0,
            open_slots=0,
            positions=[
                {
                    "symbol": "TEST1",
                    "exposure_percent": 40.0,
                },
                {
                    "symbol": "TEST2",
                    "exposure_percent": 20.0,
                },
            ],
        )
    )

    print("\nCombined warning state")
    print(f"Risk Usage : {combined['risk_usage_percent']:.2f}%")
    print(f"Alerts     : {combined['alert_count']}")

    codes = {
        alert["code"]
        for alert in combined["alerts"]
    }

    assert combined["risk_usage_percent"] == 90.0
    assert combined["alert_count"] == 4
    assert codes == {
        "PORTFOLIO_RISK_HIGH",
        "LOW_OPEN_SLOTS",
        "LOW_AVAILABLE_CASH",
        "POSITION_EXPOSURE_HIGH",
    }

    print("\n========== RESULT ==========")
    print("PASS: Safe state produces no alerts.")
    print("PASS: 80% portfolio-risk warning threshold is enforced.")
    print("PASS: Low-slot and low-cash warnings are enforced.")
    print("PASS: 35% position-exposure warning threshold is enforced.")
    print("PASS: Multiple warnings can be reported together.")


if __name__ == "__main__":
    main()
