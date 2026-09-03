from pathlib import Path

from src.shell.context.context import ShellContext


def cmd_mkdir(args: list[str], context: ShellContext) -> str | None:
    if not args:
        return None

    for name in args:
        target = context.resolve_path(name)
        target.mkdir(parents=True, exist_ok=True)

    return None
