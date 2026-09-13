from __future__ import annotations

import os
from pathlib import Path

from src.shell.context.context import ShellContext


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
