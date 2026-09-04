import os
import subprocess
from src.shell.context.context import ShellContext


def _clear_screen() -> None:
    command = "cls" if os.name == "nt" else "clear"
    subprocess.run(command, shell=True, check=False)


def cmd_trm(args: list[str], context: ShellContext) -> None:
    _clear_screen()
    print("Welcome to Midnight Terminal.")
    print("[VER 0.000.0012] ALPHA - (c) Congg 2026.")
