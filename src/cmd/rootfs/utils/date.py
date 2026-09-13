from datetime import datetime

from src.shell.context.context import ShellContext


def man_date() -> str:
    return """DATE(1)                  Midnight Terminal Manual                 DATE(1)

NAME

    date - display the current date and time

SYNOPSIS

    date

DESCRIPTION

    Prints the current date and time.

EXAMPLES

    date

SEE ALSO

    time(1)

"""


def cmd_date(args: list[str], context: ShellContext) -> None:
    print(datetime.now())
