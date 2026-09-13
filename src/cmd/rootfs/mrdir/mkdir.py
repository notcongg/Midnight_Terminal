from pathlib import Path

from src.shell.context.context import ShellContext


def man_mkdir() -> str:
    return """MKDIR(1)                 Midnight Terminal Manual                 MKDIR(1)

NAME

    mkdir - create directories

SYNOPSIS

    mkdir <directory>...

DESCRIPTION

    Creates one or more directories.

EXAMPLES

    mkdir new_folder
    mkdir path/to/folder

SEE ALSO

    rm(1), cp(1)

"""


def cmd_mkdir(args: list[str], context: ShellContext) -> str | None:
    if not args:
        return None

    for name in args:
        target = context.resolve_path(name)
        target.mkdir(parents=True, exist_ok=True)

    return None
