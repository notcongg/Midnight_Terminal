from __future__ import annotations

from src.shell.context.context import ShellContext


def man_time() -> str:
    return """TIME(1)                   Midnight Terminal Manual                  TIME(1)

NAME

    time - measure command execution time

SYNOPSIS

    time command [arguments...]

DESCRIPTION

    Executes a command and displays the elapsed execution time.

    The command is executed by Midnight Terminal's normal shell
    executor, so pipelines and redirections remain supported.

EXAMPLES

    time echo Hello

    time ps

    time ps | grep python

    time cat file.txt | grep hello

OUTPUT

    [time] 0.001234s

SEE ALSO

    ps(1), grep(1)

"""


def cmd_time(
    args: list[str],
    context: ShellContext,
) -> str:
    if not args:
        raise ValueError(
            "time: missing command"
        )

    raise ValueError(
        "time: internal execution wrapper"
    )
