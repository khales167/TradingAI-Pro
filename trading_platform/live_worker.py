from __future__ import annotations

import queue
import threading
from dataclasses import dataclass

from trading_platform.live_audio_capture import LiveAudioCapture
from trading_platform.live_transcription import (
    LiveTranscriptionEngine,
    WhisperCppBackend,
)
from trading_platform.ticker_detector import TickerDetector


@dataclass(frozen=True)
class LiveUpdate:
    transcript: str = ""
    tickers: tuple[str, ...] = ()
    error: str = ""


class TraderTVLiveWorker:
    """Background TraderTV capture/transcription worker for Streamlit."""

    def __init__(
        self,
        whisper_exe: str,
        whisper_model: str,
        symbols: list[str],
        chunk_seconds: int = 10,
    ):
        self.whisper_exe = whisper_exe
        self.whisper_model = whisper_model
        self.symbols = symbols
        self.chunk_seconds = chunk_seconds
        self.updates: queue.Queue[LiveUpdate] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="tradertv-live-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def latest_update(self) -> LiveUpdate | None:
        latest = None

        while True:
            try:
                latest = self.updates.get_nowait()
            except queue.Empty:
                return latest

    def _run(self) -> None:
        try:
            capture = LiveAudioCapture(
                device=None,
                samplerate=48000,
                channels=2,
                chunk_seconds=self.chunk_seconds,
            )
            engine = LiveTranscriptionEngine(
                WhisperCppBackend(
                    self.whisper_exe,
                    self.whisper_model,
                )
            )
            detector = TickerDetector(self.symbols)

            while not self._stop_event.is_set():
                audio_path = None

                try:
                    audio_path = capture.record_chunk()

                    if self._stop_event.is_set():
                        break

                    result = engine.transcribe_file(
                        str(audio_path)
                    )
                    transcript = result.text
                    tickers = tuple(
                        detector.detect(transcript)
                    )

                    self.updates.put(
                        LiveUpdate(
                            transcript=transcript,
                            tickers=tickers,
                        )
                    )

                except Exception as exc:
                    self.updates.put(
                        LiveUpdate(error=str(exc))
                    )
                    break

                finally:
                    if audio_path is not None:
                        capture.cleanup(audio_path)

        finally:
            self._stop_event.set()
