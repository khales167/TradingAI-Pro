"""Execution cost attribution for identical fills vs risk-adjusted sizing.

Fixed-size scenario preserves baseline trade dates, reference prices and quantities.
Costs are applied adversely to each entry and exit. This is a controlled
attribution, not a replay with potentially different stop/target outcomes.
"""
from core.backtest_data import load_backtest_data
from core.daily_backtester import DailyTechnicalBacktester

CAPITAL = 2000.0
COMMISSION_PER_SHARE = 0.005
SLIPPAGE_BPS = 5.0


def main():
    df = load_backtest_data("NVDA")
    engine = DailyTechnicalBacktester()
    baseline = engine.run(df, initial_cash=CAPITAL)
    adjusted = engine.run(
        df, initial_cash=CAPITAL,
        commission_per_share=COMMISSION_PER_SHARE,
        slippage_bps=SLIPPAGE_BPS,
    )
    slip = SLIPPAGE_BPS / 10000.0
    gross_total = 0.0
    slippage_total = 0.0
    commission_total = 0.0
    print("NVDA EXECUTION COST REPORT | fixed trade list and share quantities")
    print("Entry date | Exit date | Qty | Gross P/L | Slippage | Commission | Net P/L")
    for trade in baseline["trades"]:
        shares = trade["shares"]
        entry = float(trade["entry"])
        exit_price = float(trade["raw_exit"]) if "raw_exit" in trade else float(trade["exit"])
        gross = (exit_price - entry) * shares
        slippage = (entry + exit_price) * slip * shares
        commission = 2 * COMMISSION_PER_SHARE * shares
        net = gross - slippage - commission
        gross_total += gross
        slippage_total += slippage
        commission_total += commission
        print(
            f"{trade['entry_date']} | {trade['exit_date']} | {shares:>3} | "
            f"{gross:+9.2f} | {slippage:>8.2f} | {commission:>10.2f} | {net:+8.2f}"
        )
    net_total = gross_total - slippage_total - commission_total
    print("\nFIXED-SIZE ATTRIBUTION (same dates, prices and shares)")
    print(f"Gross P/L:          ${gross_total:+.2f}")
    print(f"Estimated slippage: ${slippage_total:.2f}")
    print(f"Commissions:        ${commission_total:.2f}")
    print(f"Total costs:        ${slippage_total + commission_total:.2f}")
    print(f"Net P/L:            ${net_total:+.2f}")
    print(f"Net return:         {100 * net_total / CAPITAL:+.2f}%")
    print("\nRISK-ADJUSTED REPLAY (shares may change)")
    print(f"Closed trades: {adjusted['closed_trades']}")
    print(f"Net realized P/L: ${adjusted['realized_cash'] - CAPITAL:+.2f}")
    print(f"Shares baseline: {[t['shares'] for t in baseline['trades']]}")
    print(f"Shares adjusted: {[t['shares'] for t in adjusted['trades']]}")
    print("\nCaveats: adjusted-price OHLC, no spread or financing; fixed-size")
    print("attribution does not recompute exits after changing execution fills.")


if __name__ == "__main__":
    main()
