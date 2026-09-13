import os
import platform
import subprocess


def man_cls() -> str:
    return """CLS(1)                   Midnight Terminal Manual                  CLS(1)

NAME

    cls - clear the terminal screen

SYNOPSIS

    cls

DESCRIPTION

    Clears the terminal screen.

EXAMPLES

    cls

SEE ALSO

    clear(1), trm(1)

"""


def cmd_cls(args):
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)


def man_clear() -> str:
    return """CLEAR(1)                 Midnight Terminal Manual                CLEAR(1)

NAME

    clear - clear the terminal screen

SYNOPSIS

    clear

DESCRIPTION

    Clears the terminal screen.

EXAMPLES

    clear

SEE ALSO

    cls(1), trm(1)

"""


def cmd_clear(args):
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)
