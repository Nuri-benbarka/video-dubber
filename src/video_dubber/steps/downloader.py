from __future__ import annotations

from pathlib import Path

import ffmpeg
import yt_dlp
from rich.console import Console

from video_dubber.cache import CacheManager

console = Console()

_YT_URL_PREFIXES = ("https://www.youtube.com", "https://youtu.be", "http://www.youtube.com", "http://youtu.be", "www.youtube.com", "youtu.be")


def is_url(input: str) -> bool:
    return input.startswith(("http://", "https://")) or any(input.startswith(p) for p in _YT_URL_PREFIXES)


def run(input: str, cache: CacheManager) -> dict:
    """
    Download (if URL) and extract audio from video.

    Returns:
        {
            "video_path": Path,   # original or downloaded video file
            "audio_path": Path,   # extracted mono 16kHz WAV
        }
    """
    key = cache.get_key(input)
    audio_path = cache.path(key, "audio.wav")

    if cache.exists(key, "audio.wav"):
        console.print(f"[dim]  download: using cached audio ({audio_path})[/dim]")
        video_path = _find_cached_video(cache, key)
        return {"video_path": video_path, "audio_path": audio_path}

    cache.ensure_dir(key)

    if is_url(input):
        console.print(f"[cyan]  download: fetching video from URL...[/cyan]")
        video_path = _download_youtube(input, cache.cache_dir / key)
    else:
        video_path = Path(input).resolve()
        if not video_path.exists():
            raise FileNotFoundError(f"Local file not found: {video_path}")
        console.print(f"[cyan]  download: using local file {video_path.name}[/cyan]")

    console.print("[cyan]  download: extracting audio...[/cyan]")
    _extract_audio(video_path, audio_path)
    console.print(f"[green]  download: audio saved to {audio_path}[/green]")

    return {"video_path": video_path, "audio_path": audio_path}


def _download_youtube(url: str, dest_dir: Path) -> Path:
    ydl_opts = {
        # 720p max — sufficient for dubbing, avoids multi-GB 4K downloads
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": str(dest_dir / "video.%(ext)s"),
        "quiet": False,
        "no_warnings": True,
        "progress_hooks": [_progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "mp4")
    return dest_dir / f"video.{ext}"


def _progress_hook(d: dict) -> None:
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "?").strip()
        speed = d.get("_speed_str", "?").strip()
        eta = d.get("_eta_str", "?").strip()
        print(f"\r  download: {pct} at {speed}, ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print()  # newline after progress line


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    (
        ffmpeg
        .input(str(video_path))
        .output(
            str(audio_path),
            ac=1,          # mono
            ar=16000,      # 16kHz — optimal for Whisper
            acodec="pcm_s16le",
        )
        .overwrite_output()
        .run(quiet=True)
    )


def _find_cached_video(cache: CacheManager, key: str) -> Path | None:
    for ext in ("mp4", "mkv", "webm", "mov"):
        p = cache.cache_dir / key / f"video.{ext}"
        if p.exists():
            return p
    return None
