"""V10.7 per-trade execution audit from immutable snapshots.

Read-only: no downloads, strategy changes, broker orders or live DB writes.
Audits realized closed trades; open positions are reported separately.
"""
import csv
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "AVGO")
START, END = "2024-10-01", "2026-10-16"
CAPITAL = 2000.0
COMMISSION = 0.005
SLIP = 5 / 10000
OUT = Path("reports/backtest_trade_audit.csv")


def main():
    rows = []
    gap_count = 0
    open_count = 0
    for symbol in SYMBOLS:
        df = load_snapshot(Path(f"data/backtest_snapshots/{symbol}_{START}_{END}.csv"))
        result = DailyTechnicalBacktester().run(
            df, initial_cash=CAPITAL, risk_per_trade_pct=1.0,
            commission_per_share=COMMISSION, slippage_bps=5,
        )
        symbol_pl = 0.0
        for number, trade in enumerate(result["trades"], 1):
            shares = int(trade["shares"])
            entry = float(trade["entry"])
            exit_price = float(trade["exit"])
            raw_exit = float(trade["raw_exit"])
            gross_pl = (exit_price - entry) * shares
            commission_total = 2 * COMMISSION * shares
            calculated_pl = gross_pl - commission_total
            assert abs(calculated_pl - float(trade["pl"])) < 1e-7
            assert abs(commission_total - float(trade["commission_total"])) < 1e-7
            assert abs(exit_price - raw_exit * (1 - SLIP)) < 1e-7
            assert abs(entry - float(trade["reference_open"]) * (1 + SLIP)) < 1e-7
            reason = trade["reason"]
            assert reason in {"STOP", "STOP_GAP", "TARGET", "TARGET_GAP"}
            if reason == "STOP_GAP":
                assert raw_exit <= float(trade["stop"]) + 1e-7
            elif reason == "TARGET_GAP":
                assert raw_exit >= float(trade["target"]) - 1e-7
            elif reason == "STOP":
                assert abs(raw_exit - float(trade["stop"])) < 1e-7
            elif reason == "TARGET":
                assert abs(raw_exit - float(trade["target"])) < 1e-7
            is_gap = reason.endswith("_GAP")
            gap_count += int(is_gap)
            symbol_pl += calculated_pl
            rows.append({
                "symbol": symbol, "trade_number": number,
                "entry_date": trade["entry_date"], "exit_date": trade["exit_date"],
                "reference_open": trade["reference_open"],
                "entry_fill": entry, "shares": shares,
                "stop": trade["stop"], "target": trade["target"],
                "raw_exit": raw_exit, "exit_fill": exit_price,
                "exit_reason": reason, "is_gap": is_gap,
                "gross_pl_after_slippage_before_commission": gross_pl,
                "commission_total": commission_total,
                "net_pl": calculated_pl,
            })
        assert len(result["trades"]) == result["closed_trades"]
        if result["open_position"] is None:
            assert abs(symbol_pl - (result["realized_cash"] - CAPITAL)) < 1e-7
        else:
            open_count += 1
        print(
            f"{symbol:5} closed={result['closed_trades']:2} "
            f"gap_exits={sum(t['reason'].endswith('_GAP') for t in result['trades']):2} "
            f"net_P/L=${symbol_pl:+.2f} "
            f"open_at_end={result['open_position'] is not None}"
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "symbol", "trade_number", "entry_date", "exit_date",
        "reference_open", "entry_fill", "shares", "stop", "target",
        "raw_exit", "exit_fill", "exit_reason", "is_gap",
        "gross_pl_after_slippage_before_commission", "commission_total", "net_pl",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Audited: {len(rows)} closed trades | gap exits: {gap_count} | open positions: {open_count}")
    print(f"CSV: {OUT.resolve()}")
    print("NOTE: gross P/L includes modeled entry/exit slippage; commissions deducted separately.")
    print("NOTE: gap exits use the opening price, not the planned stop/target.")
    print("NOTE: no mark-to-market or spread modeling; this is an accounting audit, not proof of live fills.")


if __name__ == "__main__":
    main()
