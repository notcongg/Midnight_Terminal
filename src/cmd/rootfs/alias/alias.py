
from __future__ import annotations

from pathlib import Path

from src.shell.context.context import ShellContext
from src.sot import MIDALIAS_PATH


def _midalias_path() -> Path:
    return MIDALIAS_PATH


def _read_midalias_lines() -> list[str]:
    path = _midalias_path()

    if not path.exists():
        return []

    try:
        return path.read_text(
            encoding="utf-8"
        ).splitlines()
    except OSError:
        return []


def _write_midalias_lines(lines: list[str]) -> None:
    path = _midalias_path()

    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        print(
            f"Failed to save .midalias: {error}"
        )


def _remove_block_comments(text: str) -> str:
    """Remove /* ... */ block comments."""

    result = []
    i = 0
    in_quote = False

    while i < len(text):
        ch = text[i]

        if ch == "'":
            in_quote = not in_quote
            result.append(ch)
            i += 1
            continue

        if (
            not in_quote
            and ch == "/"
            and i + 1 < len(text)
            and text[i + 1] == "*"
        ):
            i += 2

            while i < len(text) - 1:
                if (
                    text[i] == "*"
                    and text[i + 1] == "/"
                ):
                    i += 2
                    break

                i += 1

            continue

        result.append(ch)
        i += 1

    return "".join(result)


def man_alias() -> str:
    return """ALIAS(1)                 Midnight Terminal Manual                ALIAS(1)

NAME

    alias - create or manage command aliases

SYNOPSIS

    alias

    alias <name> = <command>

DESCRIPTION

    Creates command aliases. Aliases are stored in .midalias.

EXAMPLES

    alias ll = ls -la

    alias cls = clear

    alias

SEE ALSO

    unalias(1), .midalias(5)

"""


def man_unalias() -> str:
    return """UNALIAS(1)               Midnight Terminal Manual              UNALIAS(1)

NAME

    unalias - remove a command alias

SYNOPSIS

    unalias <name>

DESCRIPTION

    Removes an alias from the current session.

EXAMPLES

    unalias ll

SEE ALSO

    alias(1), .midalias(5)

"""


def load_aliases(context: ShellContext) -> None:
    """
    Load aliases from .midalias.

    Aliases are stored separately from .midconf.
    """

    path = _midalias_path()

    if not path.exists():
        return

    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except OSError:
        return

    text = _remove_block_comments(text)

    for line in text.splitlines():
        stripped = line.strip()

        if (
            not stripped
            or not stripped.startswith("alias ")
        ):
            continue

        rest = stripped[6:].strip()
        name, separator, value = rest.partition("=")

        if not separator:
            continue

        name = name.strip()
        value = value.strip()

        # Remove surrounding quotes from value.
        if (
            len(value) >= 2
            and value[0] in ("'", '"')
            and value[-1] == value[0]
        ):
            value = value[1:-1]

        if name and value:
            context.aliases[name] = value


def expand_alias(
    command: str,
    context: ShellContext,
) -> str:
    parts = command.split()

    if not parts:
        return command

    alias = context.aliases.get(parts[0])

    if alias is None:
        return command

    if len(parts) == 1:
        return alias

    return f"{alias} {' '.join(parts[1:])}"


def cmd_alias(
    args: list[str],
    context: ShellContext,
) -> None:
    aliases = context.aliases

    if not args:
        if not aliases:
            print("No aliases.")
            return

        for name, command in aliases.items():
            print(f"{name} -> {command}")

        return

    if len(args) < 3 or args[1] != "=":
        print("alias <name> = <command>")
        return

    name = args[0]
    command = " ".join(args[2:])

    if not name:
        print("Alias name cannot be empty.")
        return

    aliases[name] = command

    _save_alias_to_midalias(
        name,
        command,
    )


def cmd_unalias(
    args: list[str],
    context: ShellContext,
) -> None:
    if not args:
        print("unalias <name>")
        return

    name = args[0]
    aliases = context.aliases

    if name not in aliases:
        print(
            f"Alias '{name}' not found."
        )
        return

    del aliases[name]

    _remove_alias_from_midalias(name)

    print(
        f"Alias '{name}' removed."
    )


def _save_alias_to_midalias(
    name: str,
    command: str,
) -> None:
    """Append or update an alias in .midalias."""

    lines = _read_midalias_lines()

    alias_prefix = f"alias {name}="
    new_line = f"alias {name}={command}"

    for i, line in enumerate(lines):
        if line.strip().startswith(alias_prefix):
            lines[i] = new_line

            _write_midalias_lines(lines)
            return

    lines.append(new_line)

    _write_midalias_lines(lines)


def _remove_alias_from_midalias(
    name: str,
) -> None:
    """Remove an alias from .midalias."""

    lines = _read_midalias_lines()

    alias_prefix = f"alias {name}="

    new_lines = [
        line
        for line in lines
        if not line.strip().startswith(alias_prefix)
    ]

    _write_midalias_lines(new_lines)