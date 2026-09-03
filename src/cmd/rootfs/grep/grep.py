from __future__ import annotations

from src.shell.context.context import ShellContext


def cmd_grep(args: list[str], context: ShellContext) -> str:
    if not args:
        raise ValueError("missing pattern")

    pattern = args[0]
    input_data = context.stdin.read()

    lines = input_data.splitlines()

    return "\n".join(
        line
        for line in lines
        if pattern in line
    )
