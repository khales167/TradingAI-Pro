"""V13.2 prepare an expanded, fixed historical stock universe.

Creates new immutable SHA256 snapshots only when explicitly run locally.
No optimization, trades, broker access, or changes to live state.
"""
from __future__ import annotations

import csv
from pathlib import Path

from core.backtest_snapshot import create_snapshot, load_snapshot
from scripts.report_shared_portfolio import START, END

# Predeclared liquid large-cap candidates, NOT selected for backtest P/L.
# Universe is intentionally fixed before inspecting new historical outcomes.
NEW_SYMBOLS = ("AMZN", "BAC", "CSCO", "F", "GOOGL", "INTC", "KO", "PFE", "PLTR", "SOFI")
FOLDER = Path("data/backtest_snapshots")
REPORT = Path("reports/v13_expanded_universe_manifest.csv")


def main():
    print("V13.2 EXPANDED HISTORICAL UNIVERSE | immutable snapshots")
    print(f"window={START} to {END} (end exclusive)")
    print(f"predeclared_symbols={','.join(NEW_SYMBOLS)}")
    rows = []
    failures = []
    for symbol in NEW_SYMBOLS:
        path = FOLDER / f"{symbol}_{START}_{END}.csv"
        meta = path.with_suffix(".json")
        try:
            if path.exists() != meta.exists():
                raise RuntimeError("incomplete snapshot pair; manual review required")
            status = "VERIFIED_EXISTING" if path.exists() else "CREATED"
            if not path.exists():
                create_snapshot(symbol, START, END, directory=str(FOLDER))
            df = load_snapshot(path)
            rows.append({
                "symbol": symbol, "status": status, "rows": len(df),
                "first_date": str(df.index.min().date()),
                "last_date": str(df.index.max().date()),
                "snapshot": str(path),
            })
            print(f"{symbol:5} {status:17} rows={len(df):3} "
                  f"first={rows[-1]['first_date']} last={rows[-1]['last_date']}")
        except Exception as exc:
            failures.append((symbol, str(exc)))
            print(f"{symbol:5} ERROR {type(exc).__name__}: {exc}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "symbol", "status", "rows", "first_date", "last_date", "snapshot"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Snapshots verified: {len(rows)}/{len(NEW_SYMBOLS)}")
    print(f"Manifest: {REPORT.resolve()}")
    print("NOTE: this stage only prepares historical data; feasibility screening comes next.")
    print("NOTE: candidates are not guaranteed liquid on every day; spreads are not measured.")
    print("NOTE: adjusted daily OHLC data; downloaded snapshots can reflect later vendor revisions.")
    print("NOTE: no margin, broker orders, live account updates, or database writes.")
    if failures:
        raise SystemExit(f"{len(failures)} snapshot(s) failed; inspect errors before proceeding.")


if __name__ == "__main__":
    main()
