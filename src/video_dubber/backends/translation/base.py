from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationBackend(ABC):
    @abstractmethod
    def translate(self, segments: list[dict]) -> list[dict]:
        """
        Translate English segments to Arabic.

        Args:
            segments: list of {speaker, start, end, text}

        Returns:
            list of {speaker, start, end, text_en, text_ar}
        """
