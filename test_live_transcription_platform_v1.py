from platform.live_transcription import LiveTranscriptionEngine, MockTranscriber
from platform.ticker_detector import TickerDetector


def main():
    backend = MockTranscriber(
        "Nvidia is moving while Tesla and Super Micro are active."
    )
    engine = LiveTranscriptionEngine(backend)
    result = engine.transcribe_file("mock_audio.wav")

    detector = TickerDetector(["NVDA", "TSLA", "SMCI"])
    tickers = detector.detect(result.text)

    assert result.text == (
        "Nvidia is moving while Tesla and Super Micro are active."
    )
    assert tickers == ["NVDA", "SMCI", "TSLA"]

    print("========== LIVE TRANSCRIPTION ENGINE TEST ==========")
    print(f"Transcript : {result.text}")
    print(f"Tickers    : {tickers}")
    print("\nPASS: Transcription output feeds ticker detection correctly.")


if __name__ == "__main__":
    main()
