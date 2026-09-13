from __future__ import annotations

import os
from pathlib import Path

from src.shell.context.context import ShellContext


def cmd_which(args: list[str], context: ShellContext) -> None:
    if not args:
        print("which: missing command")
        return

    target = args[0]
    path_env = os.environ.get("PATH", "")

    if not path_env:
        print("Not found.")
        return

    if os.name == "nt":
        extensions = ("", ".exe", ".bat", ".cmd")
    else:
        extensions = ("",)

    for directory in path_env.split(os.pathsep):
        if not directory:
            continue

        base = Path(directory) / target

        for extension in extensions:
            candidate = Path(f"{base}{extension}")
            if candidate.is_file():
                print(candidate)
                return

    print("Not found.")
