from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
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


class WhisperCppBackend:
    """Transcription backend using the local whisper.cpp CLI."""

    def __init__(self, executable_path: str, model_path: str):
        self.executable_path = Path(executable_path)
        self.model_path = Path(model_path)

        if not self.executable_path.is_file():
            raise FileNotFoundError(
                f"whisper-cli executable not found: {self.executable_path}"
            )

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Whisper model not found: {self.model_path}"
            )

    def transcribe(self, audio_path: str) -> str:
        audio = Path(audio_path)

        if not audio.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio}")

        command = [
            str(self.executable_path),
            "-m",
            str(self.model_path),
            "-f",
            str(audio),
            "-l",
            "en",
            "-nt",
            "-np",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(
                f"whisper.cpp failed with exit code "
                f"{result.returncode}: {error}"
            )

        return result.stdout.strip()


class MockTranscriber:
    """Deterministic backend used for local tests."""

    def __init__(self, transcript: str):
        self.transcript = transcript

    def transcribe(self, audio_path: str) -> str:
        return self.transcript