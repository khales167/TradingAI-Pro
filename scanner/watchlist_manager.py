from pathlib import Path


class WatchlistManager:

    def __init__(self):

        self.folder = Path("watchlists")

    def get_available(self):

        return sorted([
            file.stem
            for file in self.folder.glob("*.txt")
        ])

    def load(self, name):

        filename = self.folder / f"{name}.txt"

        if not filename.exists():
            raise FileNotFoundError(
                f"Watchlist '{name}' not found."
            )

        with open(filename, "r", encoding="utf-8") as f:

            symbols = [

                line.strip().upper()

                for line in f

                if line.strip()

            ]

        return symbols