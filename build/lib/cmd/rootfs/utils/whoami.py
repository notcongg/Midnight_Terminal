import getpass

from src.shell.context.context import ShellContext


def cmd_whoami(args: list[str], context: ShellContext) -> None:
    print(getpass.getuser())
