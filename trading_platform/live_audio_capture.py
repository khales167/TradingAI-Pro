from __future__ import annotations

import tempfile
import wave
from pathlib import Path

import sounddevice as sd


class LiveAudioCapture:
    """Capture Windows system audio from Stereo Mix in fixed-size chunks."""

    def __init__(
        self,
        device: int | None = None,
        samplerate: int = 48000,
        channels: int = 2,
        dtype: str = "int16",
        chunk_seconds: int = 10,
    ):
        self.device = (
            device
            if device is not None
            else self.find_stereo_mix_directsound()
        )
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.chunk_seconds = chunk_seconds

    @staticmethod
    def find_stereo_mix_directsound() -> int:
        """Return the DirectSound Stereo Mix input device index."""

        devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        for index, device in enumerate(devices):
            name = str(device["name"]).lower()
            hostapi_index = int(device["hostapi"])
            hostapi_name = str(
                hostapis[hostapi_index]["name"]
            ).lower()

            is_stereo_mix = (
                "mixage stéréo" in name
                or "mixage stereo" in name
                or "stereo mix" in name
            )

            if (
                is_stereo_mix
                and "directsound" in hostapi_name
                and int(device["max_input_channels"]) >= 2
            ):
                return index

        raise RuntimeError(
            "Stereo Mix DirectSound input was not found. "
            "Enable Stereo Mix in Windows Sound settings."
        )

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
