
from __future__ import annotations

from pathlib import Path

from src.cmd.rootfs.env.env import ENV
from src.cmd.utils.multiline import read_multiline
from src.shell.context.context import ShellContext
from src.sot import MIDCONF_PATH


def man_enfix() -> str:
    return """ENFIX(1)                 Midnight Terminal Manual               ENFIX(1)

NAME

    enfix - modify an existing environment variable

SYNOPSIS

    enfix NAME=value

    enfix NAME='

    ...

    '

DESCRIPTION

    Changes an existing environment variable in .midconf.

    Multiline variables can be edited directly from the shell.

    The multiline block is replaced while preserving its structure.

EXAMPLES

    enfix UP2=>;

    enfix UP1='
    hello
    world
    '

SEE ALSO

    env(1), set(1), unset(1)

"""


def _envconfig_path() -> Path:
    return MIDCONF_PATH


def _variable_name(assignment: str) -> str:
    name = assignment.split("=", 1)[0].strip()

    if name.startswith("set "):
        name = name[4:].strip()

    if name.startswith("$"):
        name = name[1:].strip()

    return name


def _find_variable(lines: list[str], name: str) -> int | None:
    prefix = f"set ${name}="

    for index, line in enumerate(lines):
        if line.strip().startswith(prefix):
            return index

    return None


def _replace_single(
    lines: list[str],
    index: int,
    name: str,
    value: str,
) -> None:
    line = lines[index]
    indent = line[: len(line) - len(line.lstrip())]

    lines[index] = f"{indent}set ${name}={value};"


def _multiline_length(lines: list[str], start: int) -> int:
    """
    Return the number of lines occupied by a single-quoted assignment.
    """

    first_line = lines[start]

    # Count quotes in the assignment.
    quote_count = first_line.count("'")

    # The opening and closing quote are on the same line.
    if quote_count % 2 == 0:
        return 1

    for index in range(start + 1, len(lines)):
        quote_count += lines[index].count("'")

        if quote_count % 2 == 0:
            return index - start + 1

    raise ValueError(
        "enfix: unterminated single quote"
    )


def _replace_variable(
    lines: list[str],
    index: int,
    name: str,
    value: str,
) -> None:
    stripped_value = value.lstrip()

    # Multiline single-quoted assignment.
    if stripped_value.startswith("'"):
        block_lines = stripped_value.splitlines()

        if not block_lines:
            return

        quote_count = sum(
            line.count("'")
            for line in block_lines
        )

        if quote_count % 2 != 0:
            raise ValueError(
                "enfix: unterminated single quote"
            )

        indent = lines[index][
            : len(lines[index]) - len(lines[index].lstrip())
        ]

        block_lines[0] = (
            f"{indent}set ${name}="
            + block_lines[0]
        )

        old_length = _multiline_length(
            lines,
            index,
        )

        lines[index:index + old_length] = block_lines
        return

    # Normal one-line assignment.
    _replace_single(
        lines,
        index,
        name,
        value.strip(),
    )


def _write_variable(name: str, value: str) -> None:
    path = _envconfig_path()

    if not path.exists():
        raise ValueError(
            "enfix: .midconf not found"
        )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    index = _find_variable(
        lines,
        name,
    )

    if index is None:
        raise ValueError(
            f"enfix: variable not found: {name}"
        )

    _replace_variable(
        lines,
        index,
        name,
        value,
    )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _extract_multiline(
    args: list[str],
) -> tuple[str, str]:
    """
    Parse:

        enfix NAME='
        ...
        '

    Returns:

        (NAME, multiline_value)
    """

    first = args[0]

    if "=" not in first:
        raise ValueError(
            "invalid assignment"
        )

    name, value = first.split(
        "=",
        1,
    )

    name = name.strip()

    if name.startswith("$"):
        name = name[1:].strip()

    lines = [value]

    for line in args[1:]:
        lines.append(line)

        if line.rstrip().endswith("'"):
            break

    if not lines[-1].rstrip().endswith("'"):
        raise ValueError(
            "enfix: multiline block must end with '"
        )

    return name, "\n".join(lines)


def cmd_enfix(
    args: list[str],
    context: ShellContext,
) -> None:
    if not args:
        print("Usage: enfix NAME=value")
        return

    assignment = " ".join(args)

    if "=" not in assignment:
        print("Usage: enfix NAME=value")
        return

    name = _variable_name(
        assignment,
    )

    if not name:
        print("Usage: enfix NAME=value")
        return

    # Multiline single-quoted mode.
    if (
        args[0].rstrip().endswith("='")
        or (
            "=" in args[0]
            and args[0].split(
                "=",
                1,
            )[1].strip() == "'"
        )
    ):
        name, value = _extract_multiline(
            args,
        )
    else:
        _, value = assignment.split(
            "=",
            1,
        )

        value = value.strip()

    _write_variable(
        name,
        value,
    )
