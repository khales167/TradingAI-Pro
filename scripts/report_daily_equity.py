"""Daily mark-to-market equity report from an isolated backtest trade ledger.

Replays recorded entry/exit fills, including execution commissions. Values
are end-of-day equity, not intraday drawdown. No portfolio DB writes.
"""
from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester

CAPITAL = 2000.0
COMMISSION = 0.005
SLIPPAGE_BPS = 5.0


def daily_equity(df, result, initial_cash=CAPITAL, commission=COMMISSION):
    events = {}
    for trade in result["trades"] + ([result["open_position"]] if result["open_position"] else []):
        events.setdefault(trade["entry_date"], []).append(("buy", trade))
        if "exit_date" in trade:
            events.setdefault(trade["exit_date"], []).append(("sell", trade))
    cash = float(initial_cash)
    shares = 0
    curve = []
    for date, bar in df.sort_index().iterrows():
        day = str(date.date())
        # Entry and exit on same day are both supported.
        for kind, trade in events.get(day, []):
            qty = int(trade["shares"])
            if kind == "buy":
                cash -= qty * (float(trade["entry"]) + commission)
                shares += qty
            else:
                cash += qty * (float(trade["exit"]) - commission)
                shares -= qty
        if shares < 0:
            raise ValueError(f"Negative shares on {day}")
        equity = cash + shares * float(bar["Close"])
        curve.append({"date": day, "cash": cash, "shares": shares,
                      "close": float(bar["Close"]), "equity": equity})
    return curve


def main():
    df = load_backtest_data("NVDA")
    result = DailyTechnicalBacktester().run(
        df, initial_cash=CAPITAL,
        commission_per_share=COMMISSION, slippage_bps=SLIPPAGE_BPS
    )
    curve = daily_equity(df, result)
    peak = float("-inf")
    max_drawdown = 0.0
    max_drawdown_date = None
    for point in curve:
        peak = max(peak, point["equity"])
        dd = (peak - point["equity"]) / peak * 100 if peak > 0 else 0
        if dd > max_drawdown:
            max_drawdown, max_drawdown_date = dd, point["date"]
    last = curve[-1]
    expected = result["realized_cash"]
    if result["open_position"]:
        expected += result["open_position"]["shares"] * (
            last["close"] - result["open_position"]["entry"]
        )
    difference = last["equity"] - expected
    print("NVDA DAILY EQUITY | $2,000 | 1% risk | 5 bps/side | $0.005/share/side")
    print(f"Trading days: {len(curve)}")
    print(f"Closed trades: {result['closed_trades']}")
    print(f"End cash: ${last['cash']:.2f}")
    print(f"End open shares: {last['shares']}")
    print(f"End equity (mark-to-market): ${last['equity']:.2f}")
    print(f"Max daily close-to-close drawdown: {max_drawdown:.2f}% ({max_drawdown_date})")
    print(f"Equity reconciliation difference: ${difference:+.6f}")
    print("Last five daily observations:")
    for p in curve[-5:]:
        print(f"  {p['date']}: cash=${p['cash']:.2f} shares={p['shares']} equity=${p['equity']:.2f}")
    if abs(difference) > 0.011:
        raise AssertionError("Equity does not reconcile with trade ledger")
    print("PASS: equity reconciles with trade ledger")
    print("Caveats: close-only drawdown, adjusted OHLC, no spread, intraday path unknown.")


if __name__ == "__main__":
    main()
