from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TranscriptionBackend(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path) -> list[dict]:
        """
        Transcribe audio to text segments with timestamps.

        Returns:
            list of {start: float, end: float, text: str}
        """
