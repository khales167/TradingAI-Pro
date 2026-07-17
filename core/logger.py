from pathlib import Path
from datetime import datetime


class Logger:

    def __init__(self):

        Path("logs").mkdir(exist_ok=True)

        self.filename = "logs/trading.log"

    def log(self, message):

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f"[{now}] {message}\n")