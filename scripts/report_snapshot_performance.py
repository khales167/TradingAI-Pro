"""V10.1: closed-trade performance diagnostics from immutable OHLCV snapshot.

No download, no portfolio/database writes, no strategy rule changes.
"""
from pathlib import Path

from core.backtest_snapshot import load_snapshot
from core.daily_backtester import DailyTechnicalBacktester

SNAPSHOT = Path("data/backtest_snapshots/NVDA_2024-10-01_2026-10-16.csv")
CAPITAL = 2000.0


def metrics(trades, capital):
    pls = [float(t["pl"]) for t in trades]
    wins = [p for p in pls if p > 0]
    losses = [p for p in pls if p < 0]
    n = len(pls)
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    equity = peak = capital
    max_closed_drawdown = 0.0
    for p in pls:
        equity += p
        peak = max(peak, equity)
        max_closed_drawdown = max(max_closed_drawdown, (peak - equity) / peak * 100)
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": n - len(wins) - len(losses),
        "win_rate_pct": len(wins) / n * 100 if n else None,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else None),
        "average_win": gross_profit / len(wins) if wins else None,
        "average_loss": -gross_loss / len(losses) if losses else None,
        "expectancy": sum(pls) / n if n else None,
        "realized_pl": sum(pls),
        "closed_trade_max_drawdown_pct": max_closed_drawdown,
    }


def fmt(value, suffix=""):
    if value is None:
        return "N/A"
    if value == float("inf"):
        return "Infinity (no losing trades)"
    return f"{value:+.2f}{suffix}" if suffix == "$" else f"{value:.2f}{suffix}"


def main():
    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Run py -3.14 -m scripts.test_backtest_snapshot first: {SNAPSHOT}")
    df = load_snapshot(SNAPSHOT)
    result = DailyTechnicalBacktester().run(
        df, initial_cash=CAPITAL, commission_per_share=0.005,
        slippage_bps=5, risk_per_trade_pct=1.0,
    )
    m = metrics(result["trades"], CAPITAL)
    assert m["trades"] == result["closed_trades"]
    assert abs(m["realized_pl"] - (result["realized_cash"] - CAPITAL)) < 1e-7
    print(f"V10.1 NVDA snapshot | {df.index.min().date()} to {df.index.max().date()} | {len(df)} bars")
    print(f"Closed trades: {m['trades']} | wins: {m['wins']} | losses: {m['losses']} | breakeven: {m['breakeven']}")
    print(f"Win rate: {fmt(m['win_rate_pct'], '%')} | Profit factor: {fmt(m['profit_factor'])}")
    print(f"Average win: {fmt(m['average_win'], '$')} | Average loss: {fmt(m['average_loss'], '$')}")
    print(f"Expectancy per closed trade: {fmt(m['expectancy'], '$')}")
    print(f"Realized P/L: {fmt(m['realized_pl'], '$')}")
    print(f"Closed-trade drawdown: {fmt(m['closed_trade_max_drawdown_pct'], '%')}")
    print(f"Open position at end: {'YES (excluded from realized metrics)' if result['open_position'] else 'NO'}")
    print("NOTE: closed-trade drawdown is NOT daily mark-to-market maximum drawdown.")
    print("NOTE: sample size may be too small to establish statistical edge; out-of-sample testing pending.")


if __name__ == "__main__":
    main()
