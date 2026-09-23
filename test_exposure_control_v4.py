from strategy.risk_manager import RiskManager


def main():
    print("\n========== EXPOSURE CONTROL V4 TEST ==========")

    risk = RiskManager(capital=500, risk_percent=1.0)

    # Exposure cap = 40% of $500 = $200.
    report = risk.calculate(
        entry=50,
        stop=49,
        target=55,
        available_cash=500,
        remaining_portfolio_risk=15
    )

    print(f"Capital               : ${report['Capital']:.2f}")
    print(f"Max Position Exposure : ${report['MaxPositionExposure']:.2f}")
    print(f"Entry                 : ${report['Entry']:.2f}")
    print(f"Shares                : {report['Shares']}")
    print(f"Position Size         : ${report['PositionSize']:.2f}")

    # Risk allows 5 shares and cash allows 10, but exposure allows only 4.
    assert report["MaxPositionExposurePercent"] == 40.0
    assert report["MaxPositionExposure"] == 200.0
    assert report["Shares"] == 4
    assert report["PositionSize"] == 200.0

    # A stock above the $200 single-position cap cannot be bought
    # with whole-share sizing.
    expensive = risk.calculate(
        entry=250,
        stop=249,
        target=260,
        available_cash=500,
        remaining_portfolio_risk=15
    )

    print("\nWhole-share exposure rejection")
    print(f"Entry                 : ${expensive['Entry']:.2f}")
    print(f"Shares                : {expensive['Shares']}")
    print(f"Position Size         : ${expensive['PositionSize']:.2f}")

    assert expensive["Shares"] == 0
    assert expensive["PositionSize"] == 0.0

    # Verify the existing cash constraint can still be the tightest limit.
    cash_limited = risk.calculate(
        entry=50,
        stop=49,
        target=55,
        available_cash=120,
        remaining_portfolio_risk=15
    )

    print("\nCash remains an independent limit")
    print(f"Available Cash        : ${cash_limited['AvailableCash']:.2f}")
    print(f"Shares                : {cash_limited['Shares']}")
    print(f"Position Size         : ${cash_limited['PositionSize']:.2f}")

    assert cash_limited["Shares"] == 2
    assert cash_limited["PositionSize"] == 100.0

    # Verify portfolio risk can still be the tightest limit.
    portfolio_risk_limited = risk.calculate(
        entry=50,
        stop=49,
        target=55,
        available_cash=500,
        remaining_portfolio_risk=2
    )

    print("\nPortfolio risk remains an independent limit")
    print(
        f"Remaining Risk Budget : "
        f"${portfolio_risk_limited['RemainingPortfolioRisk']:.2f}"
    )
    print(f"Shares                : {portfolio_risk_limited['Shares']}")
    print(
        f"Position Size         : "
        f"${portfolio_risk_limited['PositionSize']:.2f}"
    )

    assert portfolio_risk_limited["Shares"] == 2
    assert portfolio_risk_limited["PositionSize"] == 100.0

    print("\n========== RESULT ==========")
    print("PASS: 40% single-position exposure cap is enforced.")
    print("PASS: Whole-share positions above the exposure cap are rejected.")
    print("PASS: Cash and portfolio-risk limits remain independently enforced.")


if __name__ == "__main__":
    main()
