import platform
import subprocess
from src.shell.context.context import ShellContext


def _clear_screen() -> None:
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)


def cmd_trm(args: list[str], context: ShellContext) -> None:
    _clear_screen()
    print("Welcome to Midnight Terminal.")
    print("[VER 0.000.0012] ALPHA - (c) Congg 2026.")
