"""Compare independent technical-only backtests across watchlist symbols.

Each symbol starts with its own $2,000 cash balance; results are NOT
the performance of a combined $2,000 portfolio.
"""
from core.data_manager import DataManager
from core.daily_backtester import DailyTechnicalBacktester

SYMBOLS = ("NVDA", "AMD", "AAPL", "TSLA", "PLTR", "META", "MSFT", "AMZN", "NFLX", "AVGO")
CAPITAL = 2000.0


def summarize(symbol, result):
    trades = result["trades"]
    wins = [float(t["pl"]) for t in trades if t["pl"] > 0]
    losses = [float(t["pl"]) for t in trades if t["pl"] < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    win_rate = 100 * len(wins) / len(trades) if trades else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else (
        float("inf") if gross_profit else 0.0
    )
    realized_pl = float(result["realized_cash"]) - CAPITAL
    return {
        "symbol": symbol,
        "signals": result["diagnostics"]["technical_signals"],
        "entries": result["diagnostics"]["accepted_entries"],
        "rejected": result["diagnostics"]["rejected_by_risk"],
        "closed": len(trades),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "realized_pl": realized_pl,
        "return_pct": realized_pl / CAPITAL * 100,
        "open": bool(result["open_position"]),
    }


def main():
    manager = DataManager()
    backtester = DailyTechnicalBacktester()
    rows = []
    failures = []
    for symbol in SYMBOLS:
        try:
            df = manager.get_data(symbol)
            if df is None:
                raise ValueError("No usable history returned")
            rows.append(summarize(symbol, backtester.run(df, initial_cash=CAPITAL)))
        except Exception as exc:
            failures.append((symbol, str(exc)))
            print(f"SKIPPED {symbol}: {exc}")

    print("\nMULTI-STOCK TECHNICAL BACKTEST | $2,000 PER SYMBOL | 1% RISK | 40% EXPOSURE")
    print("Symbol | Signals | Entries | Rejected | Closed | Win% | PF | P/L $ | Return% | Open")
    for r in rows:
        pf = "inf" if r["profit_factor"] == float("inf") else f"{r['profit_factor']:.2f}"
        print(
            f"{r['symbol']:>6} | {r['signals']:>7} | {r['entries']:>7} | "
            f"{r['rejected']:>8} | {r['closed']:>6} | {r['win_rate']:>5.1f} | "
            f"{pf:>4} | {r['realized_pl']:>+8.2f} | "
            f"{r['return_pct']:>+7.2f}% | {'Yes' if r['open'] else 'No'}"
        )
    if failures:
        print("\nSkipped:", ", ".join(f"{s} ({reason})" for s, reason in failures))
    print("\nEach symbol is tested independently, NOT as one portfolio.")
    print("Returns are realized-only and exclude open P/L, fees and slippage.")
    print("Historical prices are unadjusted; splits and data consistency need review.")
    print("Signal counts can differ because signals during open positions are not counted.")


if __name__ == "__main__":
    main()
