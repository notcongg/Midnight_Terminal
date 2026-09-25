
from __future__ import annotations

from pathlib import Path

from src.cmd.rootfs.env.env import ENV
from src.cmd.utils.multiline import read_multiline
from src.shell.context.context import ShellContext
<<<<<<< HEAD
from src.sot import MIDCONF_PATH
=======
from src.utils.paths import midconf_path
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)


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
<<<<<<< HEAD
    return MIDCONF_PATH
=======
    """Return the platform-specific Midnight .midconf path."""
    return midconf_path()
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)


def _variable_name(assignment: str) -> str:
    name = assignment.split(
        "=",
        1,
    )[0].strip()

    if name.startswith("set "):
        name = name[4:].strip()

    if name.startswith("$"):
        name = name[1:].strip()

    return name


def _find_variable(
    lines: list[str],
    name: str,
) -> int | None:
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

    indent = line[
        : len(line) - len(line.lstrip())
    ]

    lines[index] = (
        f"{indent}set ${name}={value};"
    )


<<<<<<< HEAD
def _multiline_length(lines: list[str], start: int) -> int:
=======
def _replace_multiline(
    lines: list[str],
    index: int,
    name: str,
    block: str,
) -> list[str]:
    """
    Replace the existing multiline variable with a new block.

    The block must already contain the opening and closing brackets.
    """

    old_line = lines[index]

    indent = old_line[
        : len(old_line) - len(old_line.lstrip())
    ]

    block_lines = block.splitlines()

    if not block_lines:
        return lines

    block_lines[0] = (
        f"{indent}set ${name}={block_lines[0]}"
    )

    lines[
        index:
        index + _multiline_length(lines, index)
    ] = block_lines

    return lines


def _multiline_length(
    lines: list[str],
    start: int,
) -> int:
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    """
    Return the number of lines occupied by a single-quoted assignment.
    """

    first_line = lines[start]

<<<<<<< HEAD
    # Count quotes in the assignment.
    quote_count = first_line.count("'")
=======
    for index in range(
        start,
        len(lines),
    ):
        line = lines[index]
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

    # The opening and closing quote are on the same line.
    if quote_count % 2 == 0:
        return 1

    for index in range(start + 1, len(lines)):
        quote_count += lines[index].count("'")

        if quote_count % 2 == 0:
            return index - start + 1

    raise ValueError(
<<<<<<< HEAD
        "enfix: unterminated single quote"
=======
        "enfix: unterminated multiline block"
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    )


def _replace_variable(
    lines: list[str],
    index: int,
    name: str,
    value: str,
) -> None:
    stripped_value = value.lstrip()

<<<<<<< HEAD
    # Multiline single-quoted assignment.
    if stripped_value.startswith("'"):
        block_lines = stripped_value.splitlines()
=======
    # Multiline assignment.
    if stripped_value.startswith("["):
        new_block = stripped_value
        block_lines = new_block.splitlines()
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

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
            : len(lines[index])
            - len(lines[index].lstrip())
        ]

        block_lines[0] = (
            f"{indent}set ${name}="
            + block_lines[0]
        )

        old_length = _multiline_length(
            lines,
            index,
        )
<<<<<<< HEAD
=======

        lines[
            index:
            index + old_length
        ] = block_lines
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

        return

    # Normal one-line assignment.
    _replace_single(
        lines,
        index,
        name,
        value.strip(),
    )


def _write_variable(
    name: str,
    value: str,
) -> None:
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
<<<<<<< HEAD
=======

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

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

<<<<<<< HEAD
    if not lines[-1].rstrip().endswith("'"):
=======
    if lines[-1].strip() != "]":
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
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
<<<<<<< HEAD
        assignment,
=======
        assignment
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    )

    if not name:
        print("Usage: enfix NAME=value")
        return

<<<<<<< HEAD
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
=======
    # Multiline mode.
    if (
        args[0].rstrip().endswith("=[")
        or (
            "=" in args[0]
            and args[0]
            .split("=", 1)[1]
            .strip() == "["
        )
    ):
        name, value = _extract_multiline(
            args
        )

>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    else:
        _, value = assignment.split(
            "=",
            1,
        )

        value = value.strip()

    _write_variable(
        name,
        value,
<<<<<<< HEAD
    )
=======
    )
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
