from trading_platform.ticker_detector import TickerDetector


def main():
    detector = TickerDetector(["NVDA", "AMD", "AAPL", "TSLA", "SMCI"])

    cases = {
        "Nvidia is moving higher on heavy volume": ["NVDA"],
        "Tesla and Apple are active this morning": ["AAPL", "TSLA"],
        "Watching $AMD after the opening bell": ["AMD"],
        "Super Micro Computer is under pressure": ["SMCI"],
        "No stock mentioned here": [],
    }

    for text, expected in cases.items():
        actual = detector.detect(text)
        assert actual == expected, f"{text}: expected {expected}, got {actual}"
        print(f"PASS | {text} -> {actual}")

    print("\nPASS: TraderTV ticker detection engine.")


if __name__ == "__main__":
    main()
