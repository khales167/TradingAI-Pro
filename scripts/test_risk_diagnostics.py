"""V8 risk sizing and rejection diagnostics regression checks.

No network access, portfolio writes, or broker activity.
"""
from core.daily_backtester import DailyTechnicalBacktester


def main():
    import pandas as pd
    import numpy as np
    from unittest.mock import patch

    # Synthetic trending daily OHLCV: technical signals on sufficiently
    # mature bars; deterministic and independent of Yahoo Finance.
    dates = pd.bdate_range("2024-01-01", periods=270)
    closes = np.linspace(100.0, 220.0, len(dates))
    data = pd.DataFrame({
        "Open": closes - 0.1,
        "High": closes + 1.0,
        "Low": closes - 1.0,
        "Close": closes,
        "Volume": np.full(len(dates), 1000000.0),
    }, index=dates)
    engine = DailyTechnicalBacktester()
    for pct in (0.5, 1.0, 1.5, 2.0):
        result = engine.run(data, initial_cash=2000, risk_per_trade_pct=pct)
        d = result["diagnostics"]
        assert d["technical_signals"] == d["accepted_entries"] + d["rejected_by_risk"], (pct, d)
        reason_counts = d["rejection_reasons"]
        assert sum(reason_counts.values()) >= d["rejected_by_risk"], (pct, reason_counts)
        for rejected in d["sample_rejections"]:
            assert rejected["reasons"], (pct, rejected)
            if "trade_risk" in rejected["reasons"]:
                assert rejected["risk_per_share"] > 2000 * pct / 100 - 0.011
        for trade in result["trades"]:
            assert trade["shares"] >= 1
            assert trade["shares"] * (trade["entry"] - trade["stop"] * 1.0) <= 2000 * pct / 100 + 1e-8
        print(f"PASS: risk={pct}% signals={d['technical_signals']} accepted={d['accepted_entries']} rejected={d['rejected_by_risk']} reasons={reason_counts}")
    # Rejected-signal regression cases using the same deterministic trend.
    # Very small risk budget rejects otherwise-valid technical signals.
    risk_rejected = engine.run(data, initial_cash=2000, risk_per_trade_pct=0.01)
    rd = risk_rejected["diagnostics"]
    assert rd["technical_signals"] > 0
    assert rd["accepted_entries"] == 0
    assert rd["rejected_by_risk"] == rd["technical_signals"]
    assert rd["rejection_reasons"]["trade_risk"] == rd["rejected_by_risk"]
    print(f"PASS: trade-risk rejections={rd['rejected_by_risk']}")

    # With $100 initial capital and a 40% exposure cap, even one share
    # of this trending $100+ stock is unaffordable under exposure rules.
    exposure_rejected = engine.run(data, initial_cash=100, risk_per_trade_pct=100)
    ed = exposure_rejected["diagnostics"]
    assert ed["technical_signals"] > 0
    assert ed["accepted_entries"] == 0
    assert ed["rejection_reasons"]["exposure"] == ed["rejected_by_risk"]
    print(f"PASS: exposure rejections={ed['rejected_by_risk']}")

    # Check scenario-specific risk threshold: at 2% the same per-share
    # risk must not be diagnosed against the old hardcoded 1% budget.
    scenario = engine.run(data, initial_cash=2000, risk_per_trade_pct=2)
    sd = scenario["diagnostics"]
    assert sd["rejection_reasons"]["trade_risk"] == 0, sd
    print("PASS: 2% scenario does not use old 1% diagnostic threshold")
    for invalid in (-1, 0, 101):
        try:
            engine.run(data, initial_cash=2000, risk_per_trade_pct=invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid risk {invalid} was accepted")
    print("PASS: invalid risk settings rejected")
    print("PASS: V8 synthetic risk diagnostics checks")


if __name__ == "__main__":
    main()
