"""Read-only TradingView exported trade list audit, V15.2."""
import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("file", type=Path)
args = p.parse_args()
with args.file.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
required = {"Trade number", "Type", "Date and time", "Signal", "Net PnL USD", "Duration (bars)", "Size (qty)"}
if not rows or not required.issubset(rows[0]):
    raise SystemExit("Not a supported TradingView List of trades CSV")
groups = {}
for row in rows:
    groups.setdefault(row["Trade number"], []).append(row)
errors = []
pairs = []
for number, group in groups.items():
    entries = [r for r in group if r["Type"] == "Entry long"]
    exits = [r for r in group if r["Type"] == "Exit long"]
    if len(entries) != 1 or len(exits) != 1:
        errors.append("Trade " + number + ": missing or duplicate entry/exit")
        continue
    entry, exit_ = entries[0], exits[0]
    t1 = datetime.fromisoformat(entry["Date and time"])
    t2 = datetime.fromisoformat(exit_["Date and time"])
    if t2 < t1:
        errors.append("Trade " + number + ": exit precedes entry")
    if t1.date() != t2.date():
        errors.append("Trade " + number + ": exported timestamps span calendar dates (verify timezone)")
    if float(entry["Size (qty)"]) != float(exit_["Size (qty)"]):
        errors.append("Trade " + number + ": entry/exit quantity mismatch")
    pairs.append((entry, exit_))
pnls = [float(ex["Net PnL USD"]) for en, ex in pairs]
wins = sum(v > 0 for v in pnls)
losses = sum(v < 0 for v in pnls)
gross_wins = sum(max(0, v) for v in pnls)
gross_losses = -sum(min(0, v) for v in pnls)
print("V15.2 TRADINGVIEW CSV AUDIT")
print("CSV rows:", len(rows), "paired trades:", len(pairs))
print("Net PnL:", round(sum(pnls), 2))
print("Wins:", wins, "Losses:", losses, "Win rate:", round(100 * wins / len(pairs), 1) if pairs else 0)
print("Profit factor:", round(gross_wins / gross_losses, 3) if gross_losses else "undefined")
print("Exit reasons:", dict(Counter(ex["Signal"] for en, ex in pairs)))
print("Duration bars:", min((int(float(ex["Duration (bars)"])) for en, ex in pairs), default=0), "to", max((int(float(ex["Duration (bars)"])) for en, ex in pairs), default=0))
print("Errors:", errors if errors else "none")
print("NOTE: Export timestamps may use chart timezone; this CSV alone cannot validate New York session time.")
print("NOTE: CSV alone cannot validate ORB/VWAP logic, stop/target placement, or intrabar fills.")
if errors:
    raise SystemExit(1)
