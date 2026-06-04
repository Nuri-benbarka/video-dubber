from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from video_dubber.cache import CacheManager

console = Console()

_MODEL = "pyannote/speaker-diarization-3.1"


def run(vocals_path: Path, cache: CacheManager, key: str, auth_token: str) -> dict:
    """
    Detect speaker turns in the vocals track.

    Returns:
        {
            "diarization": list[dict],  # [{speaker, start, end}, ...]
            "diarization_path": Path,   # path to saved JSON
        }
    """
    diarization_path = cache.path(key, "diarization.json")

    if cache.exists(key, "diarization.json"):
        console.print("[dim]  diarize: using cached diarization[/dim]")
        diarization = json.loads(diarization_path.read_text())
        return {"diarization": diarization, "diarization_path": diarization_path}

    if not auth_token:
        raise ValueError(
            "PYANNOTE_AUTH_TOKEN is required for speaker diarization.\n"
            "1. Create an account at https://huggingface.co\n"
            "2. Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "3. Get your token at https://huggingface.co/settings/tokens\n"
            "4. Add PYANNOTE_AUTH_TOKEN=<token> to your .env file"
        )

    console.print(f"[cyan]  diarize: loading {_MODEL}...[/cyan]")

    from pyannote.audio import Pipeline
    import torch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    console.print(f"[dim]  diarize: using device={device}[/dim]")

    pipeline = Pipeline.from_pretrained(_MODEL, token=auth_token)
    pipeline.to(device)

    console.print("[cyan]  diarize: running diarization...[/cyan]")
    result = pipeline(str(vocals_path))

    # pyannote >= 4.x returns DiarizeOutput; use speaker_diarization annotation
    annotation = getattr(result, "speaker_diarization", result)
    diarization = [
        {
            "speaker": speaker,
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
        }
        for segment, _, speaker in annotation.itertracks(yield_label=True)
    ]

    diarization_path.write_text(json.dumps(diarization, indent=2))
    console.print(f"[green]  diarize: found {len(set(t['speaker'] for t in diarization))} speakers, {len(diarization)} segments[/green]")
    console.print(f"[green]  diarize: saved to {diarization_path}[/green]")

    return {"diarization": diarization, "diarization_path": diarization_path}
