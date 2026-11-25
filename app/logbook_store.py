"""Read the saved logbook pool and update its .env fallback values."""

import fcntl
import hashlib
import json
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from dotenv import dotenv_values, set_key

LogbookField = Literal["activity_log", "lesson_learned", "obstacles"]
FIELD_ENV_KEYS: dict[LogbookField, str] = {
    "activity_log": "ACTIVITY_LOG",
    "lesson_learned": "LESSON_LEARNED",
    "obstacles": "OBSTACLES",
}
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
LOGS_POOL_FILE = ENV_FILE.parent / "logs_pool.json"


def _lock_path(env_file: Path) -> Path:
    digest = hashlib.sha256(str(env_file.resolve()).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / f"auto-absen-logbook-{digest}.lock"


@contextmanager
def _exclusive_env_lock(env_file: Path) -> Iterator[None]:
    with _lock_path(env_file).open("a", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def get_logbook_fields(env_file: Path | None = None) -> dict[str, str] | None:
    path = env_file or ENV_FILE
    if not path.is_file():
        return None

    try:
        with _exclusive_env_lock(path):
            values = dotenv_values(path)
    except (OSError, ValueError):
        return None

    return {
        field: values.get(env_key) or ""
        for field, env_key in FIELD_ENV_KEYS.items()
    }


def get_logbook_entries(pool_file: Path | None = None) -> list[Any] | None:
    """Read every saved pool entry, including entries already marked used."""
    path = pool_file or LOGS_POOL_FILE
    if not path.is_file():
        return []

    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None

    return entries if isinstance(entries, list) else None


def update_logbook_field(
    field: LogbookField, value: str, env_file: Path | None = None
) -> bool:
    env_key = FIELD_ENV_KEYS.get(field)
    if env_key is None or not isinstance(value, str):
        return False

    path = env_file or ENV_FILE
    if not path.is_file():
        return False

    try:
        with _exclusive_env_lock(path):
            success, _, _ = set_key(
                str(path), env_key, value, quote_mode="always", export=False
            )
        return success is True
    except (OSError, ValueError):
        return False
