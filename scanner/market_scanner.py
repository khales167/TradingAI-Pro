from scanner.universe import UniverseScanner


class MarketScanner:

    def __init__(self):

        self.universe = UniverseScanner()

    def get_symbols(self):

        return self.universe.filter()