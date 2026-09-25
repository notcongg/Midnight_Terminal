from __future__ import annotations

from pathlib import Path

from prompt_toolkit.history import FileHistory

from src.cmd.rootfs.env.env import ENV
from src.utils.paths import midhsty_path


HISTORY_FILE: Path = midhsty_path()


def _env_bool(
    name: str,
    default: bool = True,
) -> bool:
    value = ENV.get(name)

    if value is None:
        return default

    return value.lower() == "true"


def history_enabled() -> bool:
    return _env_bool(
        "INPUT.HISTORY",
        True,
    )


def history_size() -> int:
    try:
        return max(
            int(
                ENV.get(
                    "INPUT.HISTORY_SIZE",
                    "1000",
                )
            ),
            1,
        )
    except ValueError:
        return 1000


def ignore_consecutive_duplicates() -> bool:
    return _env_bool(
        "INPUT.HISTORY_IGNORE_CONSECUTIVE_DUPLICATES",
        True,
    )


def _ensure_history_path() -> None:
    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def _read_entries() -> list[str]:
    if not HISTORY_FILE.exists():
        return []

    text = HISTORY_FILE.read_text(
        encoding="utf-8",
    )

    if not text.strip():
        return []

    blocks = text.split("\n\n")

    return [
        block
        for block in blocks
        if block.strip()
    ]


def _write_entries(
    entries: list[str],
) -> None:
    _ensure_history_path()

    HISTORY_FILE.write_text(
        "\n\n".join(entries) + "\n\n",
        encoding="utf-8",
    )


def _trim_history() -> None:
    entries = _read_entries()
    limit = history_size()

    if len(entries) <= limit:
        return

    _write_entries(
        entries[-limit:]
    )


def _last_command() -> str | None:
    entries = _read_entries()

    if not entries:
        return None

    last = entries[-1]
    lines = last.splitlines()

    commands = [
        line[1:]
        for line in lines
        if line.startswith("+")
    ]

    if not commands:
        return None

    return "\n".join(commands)


class MidnightHistory(FileHistory):

    def append_string(
        self,
        string: str,
    ) -> None:
        if (
            ignore_consecutive_duplicates()
            and _last_command() == string
        ):
            return

        super().append_string(string)
        _trim_history()

    def replace_last_string(
        self,
        original: str,
        replacement: str,
    ) -> None:
        entries = _read_entries()

        if not entries:
            return

        last = entries[-1]
        lines = last.splitlines()

        if not any(
            line.startswith("+")
            for line in lines
        ):
            return

        timestamp = [
            line
            for line in lines
            if not line.startswith("+")
        ]

        new_entry = "\n".join(
            timestamp
            + [
                f"+{line}"
                for line in replacement.splitlines()
            ]
        )

        entries[-1] = new_entry
        _write_entries(entries)

        self._loaded_strings = list(
            self.load_history_strings()
        )


def get_history() -> MidnightHistory | None:
    if not history_enabled():
        return None

    _ensure_history_path()

    if not HISTORY_FILE.exists():
        HISTORY_FILE.touch(
            exist_ok=True,
        )

    _trim_history()

    return MidnightHistory(
        str(HISTORY_FILE)
    )