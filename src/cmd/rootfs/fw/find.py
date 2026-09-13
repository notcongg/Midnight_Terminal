from __future__ import annotations

import os
from pathlib import Path

from src.shell.context.context import ShellContext


def man_find() -> str:
    return """FIND(1)                  Midnight Terminal Manual                 FIND(1)

NAME

    find - find files and directories

SYNOPSIS

    find <pattern>
    find <pattern> <directory>

DESCRIPTION

    Searches for files and directories matching the given pattern.

EXAMPLES

    find *.txt
    find *.py src/
    find test_*

SEE ALSO

    grep(1), ls(1), tree(1)

"""


def cmd_find(args: list[str], context: ShellContext) -> None:
    if not args:
        print("find: missing search pattern")
        return

    keyword = args[0]
    found = False

    for root, dirs, files in os.walk(context.cwd):
        for name in dirs + files:
            if keyword.lower() in name.lower():
                print(Path(root) / name)
                found = True

    if not found:
        print("Nothing found.")
