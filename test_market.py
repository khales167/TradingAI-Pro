from market.sentiment import MarketSentiment

market = MarketSentiment()

result = market.analyze()

print("\n")

print("=" * 60)
print("MARKET SENTIMENT")
print("=" * 60)

for key, value in result.items():
    print(f"{key:<10} : {value}")