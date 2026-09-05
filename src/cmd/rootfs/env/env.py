from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path
from typing import Any

from src.cmd.utils.multiline import read_multiline
from src.cmd.utils.registry import COMMANDS
from src.shell.context.context import ShellContext


ENV: dict[str, str] = {}

_VARIABLE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_.]*)")
_COMMAND = re.compile(r"\(cmd\.([A-Za-z_][A-Za-z0-9_]*)\)")


def man_env() -> str:
    return """ENV(1)                   Midnight Terminal Manual                  ENV(1)

NAME

    env - print the shell session environment

SYNOPSIS

    env

DESCRIPTION

    Prints every environment variable defined in envconfig.dream,
    preserving the order in which they are defined.

FILES

    envconfig.dream
        Midnight Terminal environment configuration.

SEE ALSO

    set(1), unset(1)

"""


def _envconfig_path() -> Path:
    return Path(__file__).with_name("envconfig.dream")


def _resolve_variables(value: str) -> str:
    value = value.replace("~space", " ")

    def replace(match: re.Match[str]) -> str:
        return ENV.get(match.group(1), "")

    return _VARIABLE.sub(replace, value)


def _run_command(
    name: str,
    context: ShellContext,
) -> str:
    handler = COMMANDS.get(name)

    if handler is None:
        raise ValueError(f"env: command not found: {name}")

    output = io.StringIO()

    command_context = context.clone_streams_reset()
    command_context.stdout = output

    try:
        with contextlib.redirect_stdout(output):
            try:
                try:
                    result: Any = handler([], command_context)
                except TypeError:
                    result = handler([])
            except Exception as exc:
                raise ValueError(
                    f"env: failed to execute cmd.{name}: {exc}"
                ) from exc

    finally:
        context.cwd = command_context.cwd
        context.exit_requested = command_context.exit_requested

    text = output.getvalue()

    if result is not None:
        text += str(result)

    return text.rstrip("\r\n")


def _resolve_commands(
    value: str,
    context: ShellContext,
) -> str:
    def replace(match: re.Match[str]) -> str:
        return _run_command(match.group(1), context)

    return _COMMAND.sub(replace, value)


def _resolve_value(
    value: str,
    context: ShellContext,
) -> str:
    value = _resolve_commands(value, context)
    value = _resolve_variables(value)

    return value


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
        name = name[1:]

    if not name:
        return

    value = _resolve_value(value.strip(), context)

    ENV[name] = value


def _store_multiline(
    assignment: str,
    content: str,
    context: ShellContext,
) -> None:
    """
    Store a multiline assignment and process nested `set` statements.
    """

    name, separator = assignment.split("=", 1)

    name = name.strip()

    if name.startswith("set "):
        name = name[4:].lstrip()

    if name.startswith("$"):
        name = name[1:]

    if not name:
        return

    value_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()

        if not stripped:
            value_lines.append(line)
            continue

        if stripped.startswith("//"):
            continue

        if stripped.startswith("set "):
            _store_assignment(stripped, context)
            continue

        value_lines.append(line)

    value = "\n".join(value_lines)
    value = _resolve_value(value, context)

    ENV[name] = value


def _load_envconfig(
    context: ShellContext,
) -> None:
    path = _envconfig_path()

    if not path.exists():
        raise FileNotFoundError(
            f"env: configuration file not found: {path}"
        )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("//"):
            index += 1
            continue

        if not stripped.startswith("set "):
            index += 1
            continue

        if "[" not in stripped:
            _store_assignment(
                stripped,
                context,
            )
            index += 1
            continue

        opening = line.find("[")

        assignment = line[:opening].rstrip()

        content, next_index = read_multiline(
            lines,
            index,
        )

        _store_multiline(
            assignment,
            content,
            context,
        )

        index = next_index


def _print_env() -> str:
    return "\n".join(
        f"{name}={value}"
        for name, value in ENV.items()
    )

def reload_envconfig(context: ShellContext) -> None:
    ENV.clear()
    _load_envconfig(context)


def cmd_env(
    args: list[str],
    context: ShellContext,
) -> str:
    if args:
        raise ValueError("env: unexpected arguments")

    ENV.clear()

    _load_envconfig(context)

    return _print_env()
