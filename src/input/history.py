from pathlib import Path

from prompt_toolkit.history import FileHistory


HISTORY_DIR = Path(__file__).resolve().parent.parent / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

history = FileHistory(
    str(HISTORY_DIR / ".midnight_history")
)
