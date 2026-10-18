"""V15.1 read-only IBKR historical 1-minute data acquisition.

Uses ib_insync, TWS/IB Gateway socket API. No placeOrder calls, no live
portfolio/database updates, and no overwrite of existing CSV snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
OUT = Path("data/intraday_snapshots")


def parser():
    p = argparse.ArgumentParser(description="Read-only IBKR intraday data snapshot")
    p.add_argument("--symbol", default="AAPL", help="US stock symbol")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497, help="TWS paper default: 7497")
    p.add_argument("--client-id", type=int, default=81)
    p.add_argument("--days", type=int, default=5, help="IBKR duration in calendar days, max 30")
    p.add_argument("--rth-only", action="store_true", help="Exclude extended hours")
    p.add_argument("--connect", action="store_true", help="Explicitly authorize read-only connection")
    return p


def main():
    args = parser().parse_args()
    symbol = args.symbol.strip().upper()
    if not symbol.isascii() or not symbol.replace(".", "").isalnum() or len(symbol) > 12:
        raise SystemExit("Invalid symbol")
    if not (1 <= args.days <= 30):
        raise SystemExit("--days must be 1..30; use separate snapshots for longer history")
    if not (1 <= args.port <= 65535) or not (0 <= args.client_id <= 999):
        raise SystemExit("Invalid port or client-id")
    if not args.connect:
        print("V15.1 IBKR READ-ONLY INTRADAY DATA")
        print("Dry-run only. No connection attempted.")
        print(f"symbol={symbol} host={args.host} port={args.port} client_id={args.client_id}")
        print(f"duration={args.days} D | bar=1 min | RTH_only={args.rth_only}")
        print("To connect: rerun with --connect after enabling TWS/IB Gateway socket API.")
        print("Paper TWS typically uses port 7497; confirm your actual configured port.")
        return
    try:
        from ib_insync import IB, Stock
    except ImportError as exc:
        raise SystemExit("Missing dependency: py -3.14 -m pip install ib-insync") from exc
    ib = IB()
    try:
        ib.connect(args.host, args.port, clientId=args.client_id, timeout=12, readonly=True)
        contract = Stock(symbol, "SMART", "USD")
        matches = ib.qualifyContracts(contract)
        if len(matches) != 1:
            raise RuntimeError(f"Could not uniquely qualify {symbol}: {len(matches)} matches")
        contract = matches[0]
        bars = ib.reqHistoricalData(
            contract, endDateTime="", durationStr=f"{args.days} D",
            barSizeSetting="1 min", whatToShow="TRADES",
            useRTH=args.rth_only, formatDate=2, keepUpToDate=False,
            timeout=60,
        )
        if not bars:
            raise RuntimeError("No historical bars returned; check data permissions, pacing and TWS logs")
        rows = []
        seen = set()
        for bar in bars:
            dt = bar.date
            if not isinstance(dt, datetime) or dt.tzinfo is None:
                raise RuntimeError("IBKR returned a naive timestamp; refusing ambiguous timezone")
            utc = dt.astimezone(UTC)
            stamp = utc.isoformat()
            if stamp in seen:
                raise RuntimeError(f"Duplicate bar timestamp {stamp}")
            seen.add(stamp)
            op, high, low, close = (float(bar.open), float(bar.high), float(bar.low), float(bar.close))
            volume = float(bar.volume)
            if not all(math.isfinite(x) for x in (op, high, low, close, volume)):
                raise RuntimeError("Non-finite OHLCV")
            if min(op, high, low, close) <= 0 or high < max(op, close, low) or low > min(op, close, high) or volume < 0:
                raise RuntimeError("Invalid OHLCV bar")
            rows.append({
                "timestamp_utc": stamp,
                "timestamp_ny": utc.astimezone(NY).isoformat(),
                "open": op, "high": high, "low": low, "close": close,
                "volume": volume,
            })
        rows.sort(key=lambda row: row["timestamp_utc"])
        # Immutable filename is derived from exact returned timestamps and content.
        data = ",".join(rows[0].keys()) + "\n" + "\n".join(",".join(str(row[key]) for key in rows[0]) for row in rows) + "\n"
        digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        name = f"{symbol}_1m_{rows[0]['timestamp_utc'][:10]}_{rows[-1]['timestamp_utc'][:10]}_{digest[:12]}"
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{name}.csv"
        meta_path = OUT / f"{name}.json"
        if path.exists() or meta_path.exists():
            if not path.exists() or not meta_path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError("Existing snapshot mismatch or incomplete pair; refusing overwrite")
            print("Snapshot already verified; no overwrite.")
        else:
            with path.open("x", encoding="utf-8", newline="") as handle:
                handle.write(data)
            metadata = {
                "symbol": symbol, "contract_conId": contract.conId,
                "source": "IBKR_TWS_API", "bar_size": "1 min", "what_to_show": "TRADES",
                "rth_only": args.rth_only, "duration": f"{args.days} D",
                "rows": len(rows), "first_utc": rows[0]["timestamp_utc"],
                "last_utc": rows[-1]["timestamp_utc"], "sha256_csv": digest,
                "captured_utc": datetime.now(UTC).isoformat(),
                "adjustments": "IBKR historical bars; verify corporate-action handling before backtesting",
            }
            with meta_path.open("x", encoding="utf-8") as handle:
                json.dump(metadata, handle, indent=2)
        print(f"PASS V15.1 | {symbol} | {len(rows)} bars | 1-minute")
        print(f"first_utc={rows[0]['timestamp_utc']} last_utc={rows[-1]['timestamp_utc']}")
        print(f"CSV: {path.resolve()}")
        print(f"SHA256: {digest}")
        print("NOTE: historical data availability, trade volume and timestamps depend on IBKR permissions.")
        print("NOTE: no orders, live portfolio, or database writes.")
    finally:
        if ib.isConnected():
            ib.disconnect()


if __name__ == "__main__":
    main()
