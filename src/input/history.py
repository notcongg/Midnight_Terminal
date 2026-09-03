from __future__ import annotations

from pathlib import Path
import shutil

from prompt_toolkit.history import FileHistory


HISTORY_DIR = Path(__file__).resolve().parent.parent / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = HISTORY_DIR / ".midnight_history"

MAX_HISTORY_SIZE = 1 * 1024 * 1024  # 1 MB
MAX_HISTORY_FILES = 3


def rotate_history() -> None:
    """Rotate history files when the current history becomes too large."""

    if not HISTORY_FILE.exists():
        return

    if HISTORY_FILE.stat().st_size < MAX_HISTORY_SIZE:
        return

    oldest = HISTORY_DIR / f".midnight_history.{MAX_HISTORY_FILES}"

    if oldest.exists():
        oldest.unlink()

    for index in range(MAX_HISTORY_FILES - 1, 0, -1):
        current = HISTORY_DIR / f".midnight_history.{index}"

        if current.exists():
            next_file = HISTORY_DIR / f".midnight_history.{index + 1}"
            current.rename(next_file)

    HISTORY_FILE.rename(HISTORY_DIR / ".midnight_history.1")


rotate_history()

history = FileHistory(str(HISTORY_FILE))
