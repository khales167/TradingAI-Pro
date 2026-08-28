from strategy.risk_manager import RiskManager

rm = RiskManager(
    capital=10000,
    risk_percent=1
)

trade = rm.calculate(
    entry=210.50,
    stop=205.80,
    target=222.80
)

print("\n========== RISK REPORT ==========\n")

for key, value in trade.items():
    print(f"{key:<20}: {value}")