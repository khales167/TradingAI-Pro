from scanner.watchlist_manager import WatchlistManager

wm = WatchlistManager()

print("Available Lists:")
print(wm.get_available())

print()

symbols = wm.load("nasdaq100")

print(symbols)