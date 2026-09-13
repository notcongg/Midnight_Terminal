from __future__ import annotations

from src.cmd.utils.registry import COMMANDS, MANUALS
from src.shell.context.context import ShellContext


def man_man() -> str:
    return """MAN(1)                   Midnight Terminal Manual                  MAN(1)

NAME
    man - show the manual page of a command

SYNOPSIS
    man COMMAND [COMMAND...]

DESCRIPTION
    Prints the manual page of one or more commands. Manual pages
    live next to the command implementations themselves (a man_<name>
    function in the same module as cmd_<name>); when a command has no
    dedicated manual page, its docstring is shown instead.

EXAMPLES
    man ps
    man grep
    man kill
    man echo

SEE ALSO
    help(1)
"""


def cmd_man(args: list[str], context: ShellContext) -> None:
    """
    Execute `man`.

    Shows the manual page for one or more commands:

        man <command> [<command>...]
    """

    if not args:
        print("What manual page do you want?")
        print("Usage: man <command>")
        return

    for name in args:
        manual = MANUALS.get(name)

        if manual is not None:
            print(manual().rstrip())
            continue

        handler = COMMANDS.get(name)

        if handler is not None and handler.__doc__:
            print(handler.__doc__.strip())
            continue

        print(f"No manual entry for {name}")
