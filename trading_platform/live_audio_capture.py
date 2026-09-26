from __future__ import annotations

import tempfile
import wave
from pathlib import Path

import sounddevice as sd


class LiveAudioCapture:
    """Capture Windows system audio from Stereo Mix in fixed-size chunks."""

    def __init__(
        self,
        device: int = 12,
        samplerate: int = 48000,
        channels: int = 2,
        dtype: str = "int16",
        chunk_seconds: int = 10,
    ):
        self.device = device
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.chunk_seconds = chunk_seconds

    def record_chunk(self) -> Path:
        """Record one audio chunk and return its temporary WAV path."""

        frames = int(self.chunk_seconds * self.samplerate)

        print(
            f"Recording {self.chunk_seconds}s "
            f"from audio device {self.device}..."
        )

        audio = sd.rec(
            frames,
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
        )

        sd.wait()

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
        )
        temp_file.close()

        audio_path = Path(temp_file.name)

        with wave.open(str(audio_path), "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # int16 = 2 bytes
            wav_file.setframerate(self.samplerate)
            wav_file.writeframes(audio.tobytes())

        print(f"Audio chunk saved: {audio_path}")

        return audio_path

    @staticmethod
    def cleanup(audio_path: Path) -> None:
        """Delete a temporary audio chunk."""

        try:
            audio_path.unlink(missing_ok=True)
        except OSError:
            pass