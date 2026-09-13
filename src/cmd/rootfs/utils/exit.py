from src.shell.context.context import ShellContext


def man_exit() -> str:
    return """EXIT(1)                  Midnight Terminal Manual                 EXIT(1)

NAME

    exit - exit the shell

SYNOPSIS

    exit

DESCRIPTION

    Exits Midnight Terminal and returns to the system shell.

EXAMPLES

    exit

SEE ALSO

    help(1)

"""


def cmd_exit(args: list[str], context: ShellContext) -> None:
    context.exit_requested = True
