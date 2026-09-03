from __future__ import annotations

from src.cmd.utils.registry import COMMANDS


def correct_command(source: str) -> str:
    if not source.strip():
        return source

    command_end = len(source)

    for index, char in enumerate(source):
        if char.isspace() or char in "|><":
            command_end = index
            break

    command = source[:command_end]

    if not command:
        return source

    normalized = command.lower()

    # Command tồn tại → normalize về lowercase.
    #
    # GREP hello
    # ↓
    # grep hello
    if normalized in COMMANDS:
        return normalized + source[command_end:]

    # Command không tồn tại → giữ nguyên.
    #
    # gerp hello
    # ↓
    # gerp hello
    #
    # suggestions.py sẽ xử lý "Did you mean...?"
    return source
