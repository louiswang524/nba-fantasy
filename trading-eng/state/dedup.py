from __future__ import annotations
import json
import logging
from datetime import date
from pathlib import Path

from signals.base import SignalResult

logger = logging.getLogger(__name__)


class DedupStore:
    """
    Tracks fired signals as {ticker}:{signal_name}:{date} keys.
    Resets stale entries (prior calendar days) on load.
    """

    def __init__(self, state_path: Path = Path("state/fired_signals.json")) -> None:
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._store: set[str] = self._load()

    def _load(self) -> set[str]:
        if not self._path.exists():
            return set()
        try:
            data = json.loads(self._path.read_text())
            today = str(date.today())
            # Only keep today's entries
            return {k for k in data if k.endswith(f":{today}")}
        except Exception:
            logger.warning(f"Dedup state corrupt — resetting: {self._path}")
            return set()

    def _save(self) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(list(self._store)))
        tmp.replace(self._path)

    def _key(self, result: SignalResult) -> str:
        return f"{result.ticker}:{result.signal_name}:{date.today()}"

    def already_fired(self, result: SignalResult) -> bool:
        return self._key(result) in self._store

    def mark_fired(self, result: SignalResult) -> None:
        self._store.add(self._key(result))
        self._save()
