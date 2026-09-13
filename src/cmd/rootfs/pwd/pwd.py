from pathlib import Path

from src.shell.context.context import ShellContext
from src.ui.display_path.dp import display_path


def man_pwd() -> str:
    return """PWD(1)                   Midnight Terminal Manual                  PWD(1)

NAME

    pwd - print the current working directory

SYNOPSIS

    pwd

DESCRIPTION

    Prints the absolute path of the current working directory.

EXAMPLES

    pwd

SEE ALSO

    cd(1), ls(1)

"""


def cmd_pwd(args, context: ShellContext):
    return display_path(Path(context.cwd))
