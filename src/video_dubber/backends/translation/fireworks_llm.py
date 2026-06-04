from __future__ import annotations

from pathlib import Path

from video_dubber.backends.translation.base import TranslationBackend

_BASE_URL = "https://api.fireworks.ai/inference/v1"

FIREWORKS_MODELS = {
    "kimi-k2.6": "accounts/fireworks/models/kimi-k2p6",
    "qwen3-235b": "accounts/fireworks/models/qwen3-235b-a22b",
    "qwen3.6-plus": "accounts/fireworks/models/qwen3p6-plus",
    "llama-4-maverick": "accounts/fireworks/models/llama-4-maverick-instruct-basic",
}

_DEFAULT_MODEL = "kimi-k2.6"

_SYSTEM_PROMPT = """You are a professional Arabic translator specializing in Modern Standard Arabic (MSA / الفصحى).
Translate the given English text to MSA Arabic. Output only the translated text, nothing else.
Preserve the original tone, meaning, and any technical terms. Do not add explanations or notes."""


class FireworksLLMBackend(TranslationBackend):
    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self.api_key = api_key
        self.model_id = FIREWORKS_MODELS.get(model, FIREWORKS_MODELS[_DEFAULT_MODEL])

    def translate(self, segments: list[dict]) -> list[dict]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=_BASE_URL)

        result = []
        for seg in segments:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": seg["text"]},
                ],
                temperature=0.3,
            )
            result.append({**seg, "text_en": seg["text"], "text_ar": response.choices[0].message.content.strip()})

        return result
