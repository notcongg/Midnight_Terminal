import getpass

from src.shell.context.context import ShellContext


def man_whoami() -> str:
    return """WHOAMI(1)                Midnight Terminal Manual                WHOAMI(1)

NAME

    whoami - display the current username

SYNOPSIS

    whoami

DESCRIPTION

    Prints the username of the current user.

EXAMPLES

    whoami

SEE ALSO

    hostname(1)

"""


def cmd_whoami(args: list[str], context: ShellContext) -> None:
    print(getpass.getuser())
