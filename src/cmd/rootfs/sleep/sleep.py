from __future__ import annotations
from src.shell.context.context import ShellContext

import time

def cmd_sleep(args: list[str], context: ShellContext) -> str:
    for arg in args:
        time.sleep(int(arg))