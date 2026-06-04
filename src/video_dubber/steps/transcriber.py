from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from video_dubber.cache import CacheManager
from video_dubber.config import TranscriptionConfig

console = Console()


def run(vocals_path: Path, diarization: list[dict], cache: CacheManager, key: str, config: TranscriptionConfig) -> dict:
    """
    Transcribe vocals and merge with speaker diarization.

    Returns:
        {
            "transcription": list[dict],   # [{speaker, start, end, text}, ...]
            "transcription_path": Path,
        }
    """
    transcription_path = cache.path(key, "transcription.json")

    if cache.exists(key, "transcription.json"):
        console.print("[dim]  transcribe: using cached transcription[/dim]")
        transcription = json.loads(transcription_path.read_text())
        return {"transcription": transcription, "transcription_path": transcription_path}

    backend = _get_backend(config)
    segments = backend.transcribe(vocals_path)

    transcription = _merge_with_diarization(segments, diarization)

    transcription_path.write_text(json.dumps(transcription, indent=2))
    console.print(f"[green]  transcribe: {len(transcription)} segments saved to {transcription_path}[/green]")

    return {"transcription": transcription, "transcription_path": transcription_path}


def _get_backend(config: TranscriptionConfig):
    if config.backend == "whisper_local":
        from video_dubber.backends.transcription.whisper_local import WhisperLocalBackend
        return WhisperLocalBackend(model_name=config.model)

    if config.backend == "openai_whisper":
        import os
        from video_dubber.backends.transcription.openai_whisper import OpenAIWhisperBackend
        return OpenAIWhisperBackend(api_key=os.environ.get("OPENAI_API_KEY", ""))

    if config.backend == "fireworks_whisper":
        import os
        from video_dubber.backends.transcription.fireworks_whisper import FireworksWhisperBackend
        return FireworksWhisperBackend(api_key=os.environ.get("FIREWORKS_API_KEY", ""))

    raise ValueError(f"Unknown transcription backend: {config.backend}")


def _merge_with_diarization(segments: list[dict], diarization: list[dict]) -> list[dict]:
    """Assign a speaker to each Whisper segment based on maximum overlap with diarization turns."""
    result = []
    for seg in segments:
        speaker = _dominant_speaker(seg["start"], seg["end"], diarization)
        result.append({
            "speaker": speaker,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
        })
    return result


def _dominant_speaker(start: float, end: float, diarization: list[dict]) -> str:
    """Return the speaker with the most overlap in [start, end]."""
    overlap: dict[str, float] = {}
    for turn in diarization:
        o = min(end, turn["end"]) - max(start, turn["start"])
        if o > 0:
            overlap[turn["speaker"]] = overlap.get(turn["speaker"], 0) + o
    if not overlap:
        return "SPEAKER_00"
    return max(overlap, key=overlap.__getitem__)
