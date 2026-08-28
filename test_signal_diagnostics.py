from backtest.historical_backtester import HistoricalBacktester
from config import ADX_LIMIT, RVOL_LIMIT


bt = HistoricalBacktester()

df = bt.get_data(
    "NVDA",
    period="2y"
)

if df is None or df.empty:
    print("No data.")
    raise SystemExit

df = bt.calculate_indicators(df)

df = df.dropna().copy()


trend_mask = (
    (df["MA19"] > df["MA38"])
    & (df["MA38"] > df["MA209"])
)

dmi_mask = (
    df["DI+"] > df["DI-"]
)

adx_mask = (
    df["ADX"] > ADX_LIMIT
)

rvol_mask = (
    df["RVOL"] >= RVOL_LIMIT
)

all_mask = (
    trend_mask
    & dmi_mask
    & adx_mask
    & rvol_mask
)


scores = []

for _, row in df.iterrows():

    score, reasons = bt.calculate_score(row)

    scores.append(score)


print("\n" + "=" * 60)
print("SIGNAL DIAGNOSTICS - NVDA")
print("=" * 60)

print(f"Historical candles : {len(df)}")
print(f"Trend OK           : {int(trend_mask.sum())}")
print(f"DMI OK             : {int(dmi_mask.sum())}")
print(f"ADX > {ADX_LIMIT:<10}: {int(adx_mask.sum())}")
print(f"RVOL >= {RVOL_LIMIT:<8}: {int(rvol_mask.sum())}")
print(f"ALL CONDITIONS     : {int(all_mask.sum())}")

print("-" * 60)

print(f"Score >= 80        : {sum(s >= 80 for s in scores)}")
print(f"Score >= 70        : {sum(s >= 70 for s in scores)}")
print(f"Score >= 60        : {sum(s >= 60 for s in scores)}")
print(f"Maximum Score      : {max(scores) if scores else 0}")

print("=" * 60)