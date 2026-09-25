import re
from typing import Iterable


class TickerDetector:
    """Detect stock symbols and common company-name mentions in transcript text."""

    DEFAULT_ALIASES = {
        "NVIDIA": "NVDA",
        "NVIDIA CORPORATION": "NVDA",
        "AMD": "AMD",
        "ADVANCED MICRO DEVICES": "AMD",
        "APPLE": "AAPL",
        "TESLA": "TSLA",
        "PALANTIR": "PLTR",
        "META": "META",
        "FACEBOOK": "META",
        "MICROSOFT": "MSFT",
        "AMAZON": "AMZN",
        "NETFLIX": "NFLX",
        "BROADCOM": "AVGO",
        "GOOGLE": "GOOGL",
        "ALPHABET": "GOOGL",
        "SUPERMICRO": "SMCI",
        "SUPER MICRO": "SMCI",
        "SUPER MICRO COMPUTER": "SMCI",
    }

    def __init__(self, symbols: Iterable[str] | None = None):
        self.symbols = {
            s.strip().upper()
            for s in (symbols or [])
            if s and s.strip()
        }
        self.aliases = dict(self.DEFAULT_ALIASES)

    def detect(self, text: str) -> list[str]:
        if not text:
            return []

        normalized = re.sub(r"[^A-Z0-9$]+", " ", text.upper())
        padded = f" {normalized} "
        detected = set()

        for alias, ticker in self.aliases.items():
            if f" {alias} " in padded:
                detected.add(ticker)

        for s in self.symbols:
            if f" {s} " in padded or f" ${s} " in padded:
                detected.add(s)

        return sorted(detected)
