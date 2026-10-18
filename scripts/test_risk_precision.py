"""V11.3 direct risk-sizing precision regression tests."""
from core.daily_backtester import risk_limited_shares


def main():
    cases = [
        ("below_budget", 20.0, 19.99, 1),
        ("exact_budget_float_noise", 20.0, 20.0000000000000107, 1),
        ("exact_budget", 20.0, 20.0, 1),
        ("above_budget", 20.0, 20.000001, 0),
        ("avgo_5bps", 20.0, 19.83394, 1),
        ("avgo_10bps", 20.0, 20.21788, 0),
        ("three_shares", 20.0, 6.01, 3),
        ("multiple_boundary_noise", 20.0, 10.000000000000005, 2),
        ("material_overage", 20.0, 10.0000001, 1),
        ("zero_risk", 20.0, 0.0, 0),
    ]
    for name, budget, unit_risk, expected in cases:
        actual = risk_limited_shares(budget, unit_risk)
        assert actual == expected, f"{name}: expected {expected}, got {actual}"
        assert actual * unit_risk <= budget + 1e-10
        print(f"PASS {name:29} shares={actual}")
    print(f"Completed: {len(cases)}/{len(cases)} direct risk-sizing tests")
    print("NOTE: only historical backtest sizing helper changed; no live portfolio or broker writes.")


if __name__ == "__main__":
    main()
