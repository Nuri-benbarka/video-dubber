from __future__ import annotations

from video_dubber.backends.translation.base import TranslationBackend

_SYSTEM_PROMPT = """You are a professional Arabic translator specializing in Modern Standard Arabic (MSA / الفصحى).
Translate the given English text to MSA Arabic. Output only the translated text, nothing else.
Preserve the original tone, meaning, and any technical terms. Do not add explanations or notes."""


class ClaudeBackend(TranslationBackend):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self.api_key = api_key
        self.model = model

    def translate(self, segments: list[dict]) -> list[dict]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)

        result = []
        for seg in segments:
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": seg["text"]}],
            )
            result.append({**seg, "text_en": seg["text"], "text_ar": response.content[0].text.strip()})

        return result
