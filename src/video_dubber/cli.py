from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from video_dubber import __version__
from video_dubber.config import load_settings

app = typer.Typer(
    name="dub",
    help="Dub English YouTube videos or local files into Arabic.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"dub version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.command()
def dub(
    input: Annotated[str, typer.Argument(help="YouTube URL or path to local video file")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output directory")] = None,
    transcription: Annotated[Optional[str], typer.Option("--transcription", help="Transcription backend override")] = None,
    translation: Annotated[Optional[str], typer.Option("--translation", help="Translation backend override")] = None,
    tts: Annotated[Optional[str], typer.Option("--tts", help="TTS backend override")] = None,
    config_file: Annotated[Path, typer.Option("--config", "-c", help="Path to config.yaml")] = Path("config.yaml"),
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Ignore cached intermediate results")] = False,
    only_step: Annotated[Optional[str], typer.Option("--only-step", help="Run only a single pipeline step")] = None,
    version: Annotated[Optional[bool], typer.Option("--version", "-v", callback=version_callback, is_eager=True)] = None,
) -> None:
    """Dub a video from English to Arabic."""
    settings = load_settings(config_file)

    if transcription:
        settings.transcription.backend = transcription  # type: ignore[assignment]
    if translation:
        settings.translation.backend = translation  # type: ignore[assignment]
    if tts:
        settings.tts.backend = tts  # type: ignore[assignment]

    table = Table(title="Configuration", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Input", input)
    table.add_row("Output dir", str(output or "same as input"))
    table.add_row("Transcription", settings.transcription.backend)
    table.add_row("Translation", settings.translation.backend)
    table.add_row("TTS", settings.tts.backend)
    table.add_row("Cache", "disabled" if no_cache else "enabled")
    if only_step:
        table.add_row("Only step", only_step)
    console.print(table)

    console.print("\n[yellow]Pipeline not yet implemented — scaffold complete.[/yellow]")


def main() -> None:
    app()
