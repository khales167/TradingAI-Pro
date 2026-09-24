from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TranscriberBackend(Protocol):
    def transcribe(self, audio_path: str) -> str:
        """Return transcript text for an audio file."""


@dataclass
class TranscriptResult:
    text: str
    source: str = "audio"


class LiveTranscriptionEngine:
    """Backend-neutral transcription layer for TraderTV audio."""

    def __init__(self, backend: TranscriberBackend):
        self.backend = backend

    def transcribe_file(self, audio_path: str) -> TranscriptResult:
        if not audio_path or not audio_path.strip():
            raise ValueError("audio_path is required")

        text = self.backend.transcribe(audio_path).strip()
        return TranscriptResult(text=text)


class MockTranscriber:
    """Deterministic backend used for local tests before live audio capture."""

    def __init__(self, transcript: str):
        self.transcript = transcript

    def transcribe(self, audio_path: str) -> str:
        return self.transcript
