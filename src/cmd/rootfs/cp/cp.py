from __future__ import annotations

import shutil

from src.shell.context.context import ShellContext


def man_cp() -> str:
    return """CP(1)                    Midnight Terminal Manual                   CP(1)

NAME

    cp - copy files and directories

SYNOPSIS

    cp <source> <destination>

DESCRIPTION

    Copies a file or directory from source to destination.

EXAMPLES

    cp file.txt backup.txt
    cp -r dir1 dir2

SEE ALSO

    mv(1), rm(1)

"""


def cmd_cp(args: list[str], context: ShellContext) -> str:
    if len(args) != 2:
        return "Usage: cp <source> <destination>\n"

    source = context.resolve_path(args[0])
    destination = context.resolve_path(args[1])

    if not source.exists():
        return f"cp: cannot stat '{args[0]}': File not found\n"

    try:
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)
    except OSError as exc:
        return f"cp: cannot copy '{args[0]}': {exc}\n"

    return ""
