from __future__ import annotations

import hashlib
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.cache_dir = cache_dir
        self.enabled = enabled

    def get_key(self, input: str) -> str:
        """Stable cache key for a YouTube URL or local file path."""
        source = input.strip()
        if Path(source).exists():
            stat = Path(source).stat()
            source = f"{Path(source).resolve()}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha1(source.encode()).hexdigest()[:12]

    def step_dir(self, key: str, step: str) -> Path:
        return self.cache_dir / key / step

    def path(self, key: str, filename: str) -> Path:
        return self.cache_dir / key / filename

    def exists(self, key: str, filename: str) -> bool:
        if not self.enabled:
            return False
        return self.path(key, filename).exists()

    def ensure_dir(self, key: str, step: str | None = None) -> Path:
        if step:
            d = self.step_dir(key, step)
        else:
            d = self.cache_dir / key
        d.mkdir(parents=True, exist_ok=True)
        return d
