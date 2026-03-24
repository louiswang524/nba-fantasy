import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

# Default to project root cache/ regardless of notebook working directory.
# Override with CACHE_DIR env var if needed.
_DEFAULT_CACHE_DIR = Path(__file__).parent.parent / "cache"

def _cache_dir() -> Path:
    d = Path(os.environ.get("CACHE_DIR", str(_DEFAULT_CACHE_DIR)))
    d.mkdir(exist_ok=True)
    return d

def _cache_path(key: str) -> Path:
    hashed = hashlib.md5(key.encode()).hexdigest()
    return _cache_dir() / f"{hashed}.json"

def cached_call(key: str, ttl: int, fetch_fn: Callable[[], Any]) -> Any:
    """Return cached result if fresh, otherwise call fetch_fn and cache result."""
    path = _cache_path(key)
    if path.exists():
        entry = json.loads(path.read_text())
        if time.time() - entry["cached_at"] < ttl:
            return entry["data"]
    data = fetch_fn()
    entry = {"data": data, "cached_at": time.time()}
    # Atomic write: write to temp file then rename
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entry))
    tmp.rename(path)
    return data
