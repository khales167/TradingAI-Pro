from scanner.rvol_scanner import RVOLScanner

scanner = RVOLScanner()

symbols = [
    "NVDA",
    "AMD",
    "AAPL",
    "TSLA"
]

for symbol in symbols:

    print(
        symbol,
        scanner.get_rvol(symbol)
    )