import yfinance as yf
import pandas as pd

# List of stocks to scan
stocks = [
    "AAPL",
    "NVDA",
    "AMD",
    "TSLA",
    "META",
    "AMZN",
    "MSFT",
    "PLTR",
    "SMCI",
    "NFLX"
]

results = []

print("Scanning market...\n")

for symbol in stocks:
    try:
        stock = yf.Ticker(symbol)
        info = stock.fast_info

        last_price = info.get("lastPrice", None)

        results.append({
            "Symbol": symbol,
            "Price": round(last_price, 2) if last_price else "N/A"
        })

        print(f"✓ {symbol}")

    except Exception:
        print(f"✗ Error with {symbol}")

df = pd.DataFrame(results)

print("\nScan completed!\n")
print(df)

df.to_csv("watchlist.csv", index=False)

print("\nwatchlist.csv created successfully!")