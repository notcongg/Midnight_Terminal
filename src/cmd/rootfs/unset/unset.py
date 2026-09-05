from __future__ import annotations

from pathlib import Path

from src.cmd.rootfs.env.env import ENV
from src.shell.context.context import ShellContext


def man_unset() -> str:
    return """UNSET(1)                 Midnight Terminal Manual                UNSET(1)

NAME

    unset - remove a shell environment variable

SYNOPSIS

    unset NAME

DESCRIPTION

    Removes NAME from the Midnight Terminal environment.

    The variable is also removed from envconfig.dream.

    If NAME is a multiline variable, the entire multiline
    variable is removed.

EXAMPLES

    unset GREETING

    unset PATH

    unset UP1

SEE ALSO

    env(1), set(1)

"""


def _envconfig_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "env"
        / "envconfig.dream"
    )


def _multiline_length(
    lines: list[str],
    start: int,
) -> int:
    depth = 0

    for index in range(start, len(lines)):
        line = lines[index]

        depth += line.count("[")
        depth -= line.count("]")

        if depth <= 0:
            return index - start + 1

    raise ValueError(
        "unset: unterminated multiline block"
    )


def _remove_variable(name: str) -> None:
    path = _envconfig_path()

    if not path.exists():
        raise ValueError(
            "unset: envconfig.dream not found"
        )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    target = f"set ${name}="

    new_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped.startswith(target):
            new_lines.append(line)
            index += 1
            continue

        # Multiline variable.
        if stripped.endswith("[") or "=" in stripped and "[" in stripped:
            index += _multiline_length(
                lines,
                index,
            )
            continue

        # Normal variable.
        index += 1

    path.write_text(
        "\n".join(new_lines) + "\n",
        encoding="utf-8",
    )


def cmd_unset(
    args: list[str],
    context: ShellContext,
) -> None:
    """
    Execute `unset`.

    Removes variables from ENV and envconfig.dream.
    """

    if not args:
        print("Usage: unset NAME")
        return

    for name in args:
        name = name.strip()

        if not name:
            continue

        if name.startswith("$"):
            name = name[1:].strip()

        if not name:
            continue

        ENV.pop(name, None)
        _remove_variable(name)
