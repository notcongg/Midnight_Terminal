from __future__ import annotations

import contextlib
import io
import re

from typing import Any

from src.cmd.utils.registry import COMMANDS
from src.shell.context.context import ShellContext
<<<<<<< HEAD
from src.sot import MIDCONF_PATH
=======
from src.utils.paths import midconf_path
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)


ENV: dict[str, str] = {}

# Các biến template dành cho Prompt không giải phóng biến lúc parse config
PROMPT_VARS = {"UP1", "UP2", "UP3", "UP4"}

_VARIABLE = re.compile(
    r"\$([A-Za-z_][A-Za-z0-9_.]*)"
)

_COMMAND = re.compile(
    r"\(cmd\.([A-Za-z_][A-Za-z0-9_]*)\)"
)


def man_env() -> str:
    return """ENV(1)                  Midnight Terminal Manual                  ENV(1)

NAME
    env - print the shell session environment

SYNOPSIS
    env

DESCRIPTION
    Prints every environment variable defined in .midconf,
    preserving the order in which they are defined.

FILES
    .midconf
        Midnight Terminal unified configuration.

SEE ALSO
    set(1), unset(1)
"""


<<<<<<< HEAD
def _midconf_path() -> Path:
    return MIDCONF_PATH
=======
def _midconf_path():
    """Return the platform-specific Midnight .midconf path."""
    return midconf_path()
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)


def _resolve_variables(value: str) -> str:
    value = value.replace("~space", " ")

    def replace(match: re.Match[str]) -> str:
        return ENV.get(
            match.group(1),
            "",
        )

    return _VARIABLE.sub(
        replace,
        value,
    )


def _run_command(
    name: str,
    context: ShellContext,
) -> str:
    handler = COMMANDS.get(name)

    if handler is None:
        raise ValueError(
            f"env: command not found: {name}"
        )

    output = io.StringIO()

    command_context = (
        context.clone_streams_reset()
    )

    command_context.stdout = output

    try:
        with contextlib.redirect_stdout(output):
            try:
                try:
                    result: Any = handler(
                        [],
                        command_context,
                    )
                except TypeError:
                    result = handler([])

            except Exception as exc:
                raise ValueError(
                    f"env: failed to execute "
                    f"cmd.{name}: {exc}"
                ) from exc

    finally:
        context.cwd = command_context.cwd
        context.exit_requested = (
            command_context.exit_requested
        )

    text = output.getvalue()

    if result is not None:
        text += str(result)

    return text.rstrip("\r\n")


def _resolve_commands(
    value: str,
    context: ShellContext,
) -> str:
    def replace(match: re.Match[str]) -> str:
        return _run_command(
            match.group(1),
            context,
        )

    return _COMMAND.sub(
        replace,
        value,
    )


def _resolve_value(
    value: str,
    context: ShellContext,
) -> str:
    # Variables are expanded before command substitution.
    value = _resolve_variables(value)
    value = _resolve_commands(
        value,
        context,
    )

    return value


def _strip_line_comment(text: str) -> str:
    """Remove single-line // comments outside of quotes."""

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
            and text[i + 1] == "/"
        ):
            break

        result.append(ch)
        i += 1

    return "".join(result)


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


def _extract_quoted_value(
    text: str,
    start: int,
) -> tuple[str, int]:
    """
    Extract a single-quoted value starting at position start.

    Returns:
        (value, next_position)
    """

    i = start + 1
    chars = []

    while i < len(text):
        ch = text[i]

        if ch == "'":
            return "".join(chars), i + 1

        chars.append(ch)
        i += 1

    raise ValueError(
        "env: unterminated single quote in .midconf"
    )


def _store_assignment(
    assignment: str,
    context: ShellContext,
) -> None:
    assignment = assignment.strip()

    if assignment.startswith("set "):
        assignment = assignment[4:].lstrip()

        if assignment.endswith(";"):
            assignment = assignment[:-1].rstrip()

    name, separator, value = assignment.partition("=")

    if not separator:
        return

    name = name.strip()

    if name.startswith("$"):
        name = name[1:].strip()

    if not name:
        return

    value = value.strip()

    # Handle single-quoted value.
    if value.startswith("'"):
        eq_idx = assignment.index("=")

        value, _ = _extract_quoted_value(
            assignment,
            eq_idx + 1,
        )

    # Giữ nguyên placeholder biến đối với
    # các template Prompt.
    if name in PROMPT_VARS:
        value = value.replace(
            "~space",
            " ",
        )
    else:
        value = _resolve_value(
            value,
            context,
        )

    ENV[name] = value


def _parse_alias_statement(
    statement: str,
) -> tuple[str, str] | None:
    """
    Parse:
        alias name=command

    Returns:
        (name, command)
    """

    statement = statement.strip()

    if not statement.startswith("alias "):
        return None

    rest = statement[6:].strip()

    name, separator, value = rest.partition("=")

    if not separator:
        return None

    name = name.strip()
    value = value.strip()

    # Remove surrounding quotes.
    if (
        len(value) >= 2
        and value[0] in ("'", '"')
        and value[-1] == value[0]
    ):
        value = value[1:-1]

    if not name or not value:
        return None

    return name, value


def _execute_config_command(
    command: str,
    context: ShellContext,
) -> None:
    """Execute a command from .midconf."""

    if not command:
        return

    parts = command.split()

    handler = COMMANDS.get(parts[0])

    if handler is None:
        return

    try:
        handler(
            parts,
            context,
        )
    except Exception:
        pass


def _load_midconf(
    context: ShellContext,
) -> None:
    # Reloads replace the full config state:
    # aliases are re-read from .midconf.
    context.aliases = {}

    path = _midconf_path()

    if not path.exists():
        raise FileNotFoundError(
            f"env: configuration file not found: {path}"
        )

    text = path.read_text(
        encoding="utf-8",
    )

    # Remove block comments first.
    text = _remove_block_comments(text)

    lines = text.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        # Remove single-line comments.
        stripped = _strip_line_comment(
            stripped
        ).strip()

        if not stripped:
            index += 1
            continue

        # Handle set statement
        # (possibly multiline quoted value).
        if stripped.startswith("set "):
            eq_pos = stripped.find("=")

            if eq_pos > 0:
                after_eq = (
                    stripped[eq_pos + 1:]
                    .strip()
                )

                if (
                    after_eq.startswith("'")
                    and after_eq.count("'") < 2
                ):
                    # Multiline quoted value.
                    collected = line
                    next_idx = index + 1

                    while (
                        next_idx < len(lines)
                        and "'"
                        not in collected.split(
                            "=",
                            1,
                        )[1].strip()[1:]
                    ):
                        collected += (
                            "\n"
                            + lines[next_idx]
                        )
                        next_idx += 1

                    _store_assignment(
                        collected,
                        context,
                    )

                    index = next_idx
                    continue

            _store_assignment(
                stripped,
                context,
            )

            index += 1
            continue

        # Handle alias statement.
        if stripped.startswith("alias "):
            parsed = _parse_alias_statement(
                stripped
            )

            if parsed:
                context.aliases[
                    parsed[0]
                ] = parsed[1]

            index += 1
            continue

        # Handle command
        # (non-comment, non-set, non-alias).
        _execute_config_command(
            stripped,
            context,
        )

        index += 1


def _print_env() -> str:
    return "\n".join(
        f"{name}={value}"
        for name, value in ENV.items()
    )


def reload_envconfig(
    context: ShellContext,
) -> None:
    ENV.clear()

    _load_midconf(
        context
    )


def cmd_env(
    args: list[str],
    context: ShellContext,
) -> str:
    if args:
        raise ValueError(
            "env: unexpected arguments"
        )

    ENV.clear()

    _load_midconf(
        context
    )

    return _print_env()