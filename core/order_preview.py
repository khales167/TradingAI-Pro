from __future__ import annotations


class OrderPreviewBuilder:
    """Build an order preview only. This class never sends broker orders."""

    def build(self, signal: dict, sizing: dict) -> dict:
        ready = (
            signal.get("Decision") == "BUY"
            and bool(sizing.get("Eligible"))
            and int(sizing.get("Shares", 0)) > 0
        )

        return {
            "Symbol": signal["Symbol"],
            "Side": "BUY" if ready else "NONE",
            "Shares": int(sizing.get("Shares", 0)),
            "Entry": round(float(signal["Entry"]), 2),
            "Stop": round(float(signal["Stop"]), 2),
            "Target": round(float(signal["Target"]), 2),
            "PositionValue": round(float(sizing.get("PositionValue", 0)), 2),
            "TotalRisk": round(float(sizing.get("PositionRisk", 0)), 2),
            "RR": signal["RR"],
            "Ready": ready,
            "Mode": "PREVIEW",
        }
