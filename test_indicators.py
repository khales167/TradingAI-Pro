from indicators.indicators import calculate_indicators

data = calculate_indicators("NVDA")

print("=" * 50)

for key, value in data.items():
    print(f"{key} : {value}")