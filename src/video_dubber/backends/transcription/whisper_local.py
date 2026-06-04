from __future__ import annotations

from pathlib import Path

from rich.console import Console

from video_dubber.backends.transcription.base import TranscriptionBackend

console = Console()


class WhisperLocalBackend(TranscriptionBackend):
    def __init__(self, model_name: str = "large-v3") -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            import whisper
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            console.print(f"[cyan]  transcribe: loading whisper {self.model_name} on {device}...[/cyan]")
            self._model = whisper.load_model(self.model_name, device=device)
        return self._model

    def transcribe(self, audio_path: Path) -> list[dict]:
        model = self._load()
        console.print("[cyan]  transcribe: running Whisper...[/cyan]")
        result = model.transcribe(
            str(audio_path),
            language="en",
            word_timestamps=True,
            verbose=False,
        )
        return [
            {
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "text": seg["text"].strip(),
            }
            for seg in result["segments"]
        ]
