from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rich.console import Console

from video_dubber.cache import CacheManager

console = Console()

_MODEL = "htdemucs"


def run(audio_path: Path, cache: CacheManager, key: str) -> dict:
    """
    Separate vocals from background music/SFX using Demucs.

    Returns:
        {
            "vocals_path": Path,      # speech-only track
            "background_path": Path,  # music + SFX, no vocals
        }
    """
    vocals_path = cache.path(key, "vocals.wav")
    background_path = cache.path(key, "background.wav")

    if cache.exists(key, "vocals.wav") and cache.exists(key, "background.wav"):
        console.print(f"[dim]  separate: using cached tracks[/dim]")
        return {"vocals_path": vocals_path, "background_path": background_path}

    console.print(f"[cyan]  separate: running Demucs ({_MODEL})...[/cyan]")

    tmp_out = cache.ensure_dir(key, "demucs_tmp")

    result = subprocess.run(
        [
            sys.executable, "-m", "demucs",
            "--two-stems", "vocals",
            "--name", _MODEL,
            "--out", str(tmp_out),
            str(audio_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed:\n{result.stderr}")

    # Demucs writes to: <out>/<model>/<stem_name>/<vocals|no_vocals>.wav
    stem_name = audio_path.stem
    demucs_vocals = tmp_out / _MODEL / stem_name / "vocals.wav"
    demucs_background = tmp_out / _MODEL / stem_name / "no_vocals.wav"

    if not demucs_vocals.exists() or not demucs_background.exists():
        raise RuntimeError(
            f"Demucs output not found. Expected:\n  {demucs_vocals}\n  {demucs_background}\n"
            f"Demucs stderr:\n{result.stderr}"
        )

    demucs_vocals.rename(vocals_path)
    demucs_background.rename(background_path)

    # Clean up tmp directory
    import shutil
    shutil.rmtree(tmp_out, ignore_errors=True)

    console.print(f"[green]  separate: vocals → {vocals_path}[/green]")
    console.print(f"[green]  separate: background → {background_path}[/green]")

    return {"vocals_path": vocals_path, "background_path": background_path}
