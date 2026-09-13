import socket

from src.shell.context.context import ShellContext


def man_hostname() -> str:
    return """HOSTNAME(1)              Midnight Terminal Manual             HOSTNAME(1)

NAME

    hostname - display the system hostname

SYNOPSIS

    hostname

DESCRIPTION

    Prints the hostname of the current machine.

EXAMPLES

    hostname

SEE ALSO

    whoami(1)

"""


def cmd_hostname(args: list[str], context: ShellContext) -> None:
    print(socket.gethostname())
