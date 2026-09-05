from __future__ import annotations

from pathlib import Path

from src.cmd.rootfs.env.env import ENV
from src.shell.context.context import ShellContext


def man_set() -> str:
    return """SET(1)                   Midnight Terminal Manual                  SET(1)

NAME

    set - assign a shell environment variable

SYNOPSIS

    set NAME=value

    set NAME=[
        ...
    ]

DESCRIPTION

    Assigns NAME=value in the Midnight Terminal environment.

    The value is stored in ENV and persisted to envconfig.dream.

    Multiline variables can also be replaced directly.

EXAMPLES

    set GREETING=hello

    set PATH=C:\\tools

    set NAME=Congg

    set UP1=[
        hello
        world
    ]

SEE ALSO

    env(1), unset(1)

"""


def _envconfig_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "env"
        / "envconfig.dream"
    )


def _find_variable(
    lines: list[str],
    name: str,
) -> int | None:
    target = f"set ${name}="

    for index, line in enumerate(lines):
        if line.strip().startswith(target):
            return index

    return None


def _multiline_length(
    lines: list[str],
    start: int,
) -> int:
    """
    Return the number of lines occupied by a multiline assignment.
    """

    depth = 0

    for index in range(start, len(lines)):
        line = lines[index]

        depth += line.count("[")
        depth -= line.count("]")

        if depth <= 0:
            return index - start + 1

    raise ValueError(
        "set: unterminated multiline block"
    )


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


def _replace_multiline(
    lines: list[str],
    index: int,
    name: str,
    value: str,
) -> None:
    """
    Replace an existing multiline variable.

    Example:

        set $UP1=[
            old
        ]

    becomes:

        set $UP1=[
            new
        ]
    """

    block = value.splitlines()

    if not block:
        raise ValueError(
            "set: empty multiline block"
        )

    if block[0].strip() != "[":
        raise ValueError(
            "set: multiline value must start with ["
        )

    if block[-1].strip() != "]":
        raise ValueError(
            "set: multiline block must end with ]"
        )

    original_indent = lines[index][
        : len(lines[index]) - len(lines[index].lstrip())
    ]

    block[0] = (
        f"{original_indent}set ${name}={block[0]}"
    )

    old_length = _multiline_length(
        lines,
        index,
    )

    lines[index:index + old_length] = block


def _write_variable(
    name: str,
    value: str,
) -> None:
    path = _envconfig_path()

    if not path.exists():
        raise ValueError(
            "set: envconfig.dream not found"
        )

    lines = path.read_text(
        encoding="utf-8",
    ).splitlines()

    index = _find_variable(
        lines,
        name,
    )

    # Variable does not exist.
    if index is None:
        if value.lstrip().startswith("["):
            block = value.splitlines()

            if not block or block[-1].strip() != "]":
                raise ValueError(
                    "set: multiline block must end with ]"
                )

            lines.extend(
                [
                    f"set ${name}={block[0]}",
                    *block[1:],
                ]
            )
        else:
            lines.append(
                f"set ${name}={value};"
            )

        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        return

    existing = lines[index].strip()

    # Existing variable is multiline.
    if "[" in existing:
        _replace_multiline(
            lines,
            index,
            name,
            value,
        )
    else:
        # Existing variable is normal.
        if value.lstrip().startswith("["):
            _replace_multiline(
                lines,
                index,
                name,
                value,
            )
        else:
            _replace_single(
                lines,
                index,
                name,
                value.strip(),
            )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _parse_multiline(
    args: list[str],
) -> tuple[str, str]:
    """
    Parse:

        set UP1=[
            hello
            world
        ]

    from shell arguments.
    """

    first = args[0]

    name, separator, value = first.partition("=")

    if not separator:
        raise ValueError(
            "invalid assignment"
        )

    name = name.strip()

    if name.startswith("$"):
        name = name[1:].strip()

    if not name:
        raise ValueError(
            "invalid variable name"
        )

    block: list[str] = [
        value.strip()
    ]

    for line in args[1:]:
        block.append(line)

        if line.strip() == "]":
            break

    if block[0] != "[":
        raise ValueError(
            "set: multiline value must start with ["
        )

    if block[-1].strip() != "]":
        raise ValueError(
            "set: multiline block must end with ]"
        )

    return name, "\n".join(block)


def cmd_set(
    args: list[str],
    context: ShellContext,
) -> None:
    """
    Execute `set`.

    Assigns and persists:

        set NAME=value

    or:

        set NAME=[
            ...
        ]
    """

    if not args:
        print("Usage: set NAME=value")
        return

    assignment = " ".join(args)

    if "=" not in assignment:
        print("Usage: set NAME=value")
        return

    name, _, value = assignment.partition("=")

    name = name.strip()

    if name.startswith("$"):
        name = name[1:].strip()

    if not name:
        print("Usage: set NAME=value")
        return

    # Multiline assignment.
    if value.strip() == "[":
        try:
            name, value = _parse_multiline(args)
        except ValueError as exc:
            print(exc)
            return

        ENV[name] = value

        _write_variable(
            name,
            value,
        )

        return

    # Normal assignment.
    value = value.strip()

    ENV[name] = value

    _write_variable(
        name,
        value,
    )
