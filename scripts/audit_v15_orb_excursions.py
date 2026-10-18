"""V15.3 TradingView ORB excursion audit (read-only; no strategy changes)."""
import argparse
import csv
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("file", type=Path)
args = parser.parse_args()
with args.file.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
required = {"Trade number", "Type", "Signal", "Price USD", "Size (qty)", "Net PnL USD",
            "Favorable excursion USD", "Adverse excursion USD", "Duration (bars)"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit("Expected TradingView List of trades CSV with excursion columns")
grouped = {}
for row in rows:
    grouped.setdefault(row["Trade number"], []).append(row)
pairs = []
for number, group in grouped.items():
    entries = [r for r in group if r["Type"].strip().lower() == "entry long"]
    exits = [r for r in group if r["Type"].strip().lower() == "exit long"]
    if len(entries) != 1 or len(exits) != 1:
        raise SystemExit("Unpaired trade: " + number)
    pairs.append((entries[0], exits[0]))
if not pairs:
    raise SystemExit("No paired trades")
values = []
for entry, exit_ in pairs:
    qty = float(entry["Size (qty)"])
    entry_price = float(entry["Price USD"])
    if qty <= 0 or entry_price <= 0:
        raise SystemExit("Invalid price/quantity")
    mfe = float(exit_["Favorable excursion USD"])
    mae = abs(float(exit_["Adverse excursion USD"]))
    if mfe < 0 or mae < 0:
        raise SystemExit("Unexpected excursion sign")
    values.append({"mfe": mfe, "mae": mae, "mfe_share": mfe / qty,
                   "mae_share": mae / qty, "mfe_pct": 100 * mfe / (qty * entry_price),
                   "mae_pct": 100 * mae / (qty * entry_price),
                   "pnl": float(exit_["Net PnL USD"]), "reason": exit_["Signal"],
                   "bars": int(float(exit_["Duration (bars)"]))})
n = len(values)
avg = lambda field: sum(row[field] for row in values) / n
print("V15.3 ORB STOP / TARGET EXCURSION AUDIT")
print("Trades:", n, "| exits:", dict(Counter(v["reason"] for v in values)))
print("Avg MFE: +$%.2f per trade / +%.3f%% of entry notional" % (avg("mfe"), avg("mfe_pct")))
print("Avg MAE: -$%.2f per trade / -%.3f%% of entry notional" % (avg("mae"), avg("mae_pct")))
print("Avg MFE per share: +$%.3f" % avg("mfe_share"))
print("Avg MAE per share: -$%.3f" % avg("mae_share"))
print("MFE > $0:", sum(v["mfe"] > 0 for v in values), "/", n)
print("MAE > $0:", sum(v["mae"] > 0 for v in values), "/", n)
print("Net PnL: $%+.2f" % sum(v["pnl"] for v in values))
print("Avg duration (bars): %.1f" % avg("bars"))
print("IMPORTANT: Excursions are path extrema, not achievable realized PnL.")
print("IMPORTANT: CSV has no original ORB low, entry-time stop distance, or 2R target.")
print("Do not infer actual stop/target hit probability or 1%% risk compliance from this export.")
