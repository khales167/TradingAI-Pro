from __future__ import annotations

from datetime import datetime

from trading_platform.live_audio_capture import LiveAudioCapture
from trading_platform.live_transcription import (
    LiveTranscriptionEngine,
    WhisperCppBackend,
)
from trading_platform.ticker_detector import TickerDetector


WHISPER_EXE = (
    r"C:\Users\DELL\Desktop\whisper.cpp"
    r"\build\bin\Release\whisper-cli.exe"
)

WHISPER_MODEL = (
    r"C:\Users\DELL\Desktop\whisper.cpp"
    r"\ggml-tiny.en.bin"
)

WATCHLIST = [
    "NVDA",
    "AMD",
    "AAPL",
    "TSLA",
    "PLTR",
    "META",
    "MSFT",
    "AMZN",
    "NFLX",
    "AVGO",
    "SMCI",
]


def main() -> None:
    capture = LiveAudioCapture(
        device=12,
        samplerate=48000,
        channels=2,
        chunk_seconds=10,
    )

    backend = WhisperCppBackend(
        WHISPER_EXE,
        WHISPER_MODEL,
    )

    transcription = LiveTranscriptionEngine(backend)
    detector = TickerDetector(WATCHLIST)

    print("=" * 60)
    print("TradingAI-Pro | TraderTV Live Intelligence")
    print("=" * 60)
    print("Audio device : Stereo Mix - Device 12")
    print("Chunk size   : 10 seconds")
    print("Whisper      : tiny.en")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    try:
        while True:
            audio_path = None

            try:
                audio_path = capture.record_chunk()

                result = transcription.transcribe_file(
                    str(audio_path)
                )

                transcript = result.text
                tickers = detector.detect(transcript)

                timestamp = datetime.now().strftime("%H:%M:%S")

                print()
                print(f"[{timestamp}] TRANSCRIPT")
                print(transcript or "(no speech detected)")

                if tickers:
                    print(
                        ">>> TICKERS DETECTED:",
                        ", ".join(tickers),
                    )
                else:
                    print("Tickers: none")

                print("-" * 60)

            except Exception as exc:
                print(f"ERROR: {exc}")

            finally:
                if audio_path is not None:
                    capture.cleanup(audio_path)

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("TraderTV Live Intelligence stopped.")
        print("=" * 60)


if __name__ == "__main__":
    main()