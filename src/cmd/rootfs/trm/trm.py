import platform
import subprocess
from src.shell.context.context import ShellContext


def man_trm() -> str:
    return """TRM(1)                   Midnight Terminal Manual                  TRM(1)

NAME

    trm - clear and refresh the terminal

SYNOPSIS

    trm

DESCRIPTION

    Clears the screen and shows the Midnight Terminal welcome message.

EXAMPLES

    trm

SEE ALSO

    cls(1), clear(1)

"""


def _clear_screen() -> None:
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)


def cmd_trm(args: list[str], context: ShellContext) -> None:
    _clear_screen()
    print("Welcome to Midnight Terminal.")
    print("[VER 1.000.0001] RELEASE - (c) Congg 2026.")
    print("")
