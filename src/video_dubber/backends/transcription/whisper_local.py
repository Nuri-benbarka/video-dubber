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
            from faster_whisper import WhisperModel
            # int8 quantization: large-v3 fits in ~2.5 GB VRAM (vs ~6 GB fp32)
            console.print(f"[cyan]  transcribe: loading faster-whisper {self.model_name} (int8 on cuda)...[/cyan]")
            self._model = WhisperModel(
                self.model_name,
                device="cuda",
                compute_type="int8",
            )
        return self._model

    def transcribe(self, audio_path: Path) -> list[dict]:
        model = self._load()
        console.print("[cyan]  transcribe: running Whisper...[/cyan]")

        segments_iter, _ = model.transcribe(
            str(audio_path),
            language="en",
            word_timestamps=True,
            vad_filter=True,  # skip silence chunks — faster + cleaner
        )

        return [
            {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
            }
            for seg in segments_iter
        ]
