from __future__ import annotations

import json
import os
from pathlib import Path

from rich.console import Console

from video_dubber.cache import CacheManager
from video_dubber.config import TranslationConfig

console = Console()


def run(transcription: list[dict], cache: CacheManager, key: str, config: TranslationConfig) -> dict:
    """
    Translate English segments to MSA Arabic.

    Returns:
        {
            "translation": list[dict],   # [{speaker, start, end, text_en, text_ar}, ...]
            "translation_path": Path,
        }
    """
    translation_path = cache.path(key, "translation.json")

    if cache.exists(key, "translation.json"):
        console.print("[dim]  translate: using cached translation[/dim]")
        translation = json.loads(translation_path.read_text())
        return {"translation": translation, "translation_path": translation_path}

    backend = _get_backend(config)
    console.print(f"[cyan]  translate: using {config.backend}/{config.model}...[/cyan]")

    translation = backend.translate(transcription)

    translation_path.write_text(json.dumps(translation, indent=2, ensure_ascii=False))
    console.print(f"[green]  translate: {len(translation)} segments saved to {translation_path}[/green]")

    return {"translation": translation, "translation_path": translation_path}


def _get_backend(config: TranslationConfig):
    if config.backend == "claude":
        from video_dubber.backends.translation.claude import ClaudeBackend
        return ClaudeBackend(api_key=os.environ.get("ANTHROPIC_API_KEY", ""), model=config.model)

    if config.backend == "gemini":
        from video_dubber.backends.translation.gemini import GeminiBackend
        return GeminiBackend(api_key=os.environ.get("GEMINI_API_KEY", ""), model=config.model)

    if config.backend == "fireworks_llm":
        from video_dubber.backends.translation.fireworks_llm import FireworksLLMBackend
        return FireworksLLMBackend(api_key=os.environ.get("FIREWORKS_API_KEY", ""), model=config.model)

    raise ValueError(f"Unknown translation backend: {config.backend}")
