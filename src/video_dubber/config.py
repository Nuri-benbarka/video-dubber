from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TranscriptionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRANSCRIPTION_")

    backend: Literal["whisper_local", "openai_whisper", "fireworks_whisper"] = "whisper_local"
    model: str = "large-v3"


class TranslationConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRANSLATION_")

    backend: Literal["claude", "openai_gpt", "fireworks_llm"] = "claude"
    model: str = "claude-sonnet-4-6"
    target_dialect: Literal["msa"] = "msa"


class TTSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS_")

    backend: Literal["indextts2", "elevenlabs", "openai_tts"] = "indextts2"
    voice_cloning: bool = True


class AudioConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUDIO_")

    preserve_background: bool = True
    background_volume: float = 0.8


class ProcessingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PROCESSING_")

    chunk_size_seconds: int = 30
    cache_dir: Path = Path(".cache")


class OutputConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OUTPUT_")

    suffix: str = "_ar"
    include_subtitles: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    fireworks_api_key: str = ""
    elevenlabs_api_key: str = ""
    pyannote_auth_token: str = ""


def load_settings(config_file: Path | None = None) -> Settings:
    if config_file and config_file.exists():
        raw = yaml.safe_load(config_file.read_text())
        for section, values in (raw or {}).items():
            if isinstance(values, dict):
                for k, v in values.items():
                    os.environ.setdefault(f"{section}__{k}".upper(), str(v))
            else:
                os.environ.setdefault(section.upper(), str(values))

    return Settings()
