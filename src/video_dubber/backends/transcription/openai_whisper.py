from __future__ import annotations

from pathlib import Path

from video_dubber.backends.transcription.base import TranscriptionBackend


class OpenAIWhisperBackend(TranscriptionBackend):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def transcribe(self, audio_path: Path) -> list[dict]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                language="en",
            )

        return [
            {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
            }
            for seg in response.segments
        ]
