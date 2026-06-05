from __future__ import annotations

from video_dubber.backends.translation.base import TranslationBackend

GEMINI_MODELS = {
    "gemini-3-flash": "gemini-3.0-flash",
    "gemini-3.1-pro": "gemini-3.1-pro-preview",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-pro": "gemini-2.5-pro",
}

_DEFAULT_MODEL = "gemini-3-flash"

_SYSTEM_PROMPT = """You are a professional Arabic translator specializing in Modern Standard Arabic (MSA / الفصحى).
Translate the given English text to MSA Arabic. Output only the translated text, nothing else.
Preserve the original tone, meaning, and any technical terms. Do not add explanations or notes."""


class GeminiBackend(TranslationBackend):
    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self.api_key = api_key
        self.model_id = GEMINI_MODELS.get(model, GEMINI_MODELS[_DEFAULT_MODEL])

    def translate(self, segments: list[dict]) -> list[dict]:
        from google import generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model_id,
            system_instruction=_SYSTEM_PROMPT,
        )

        result = []
        for seg in segments:
            response = model.generate_content(seg["text"])
            result.append({**seg, "text_en": seg["text"], "text_ar": response.text.strip()})

        return result
