import socket

from src.shell.context.context import ShellContext


def cmd_hostname(args: list[str], context: ShellContext) -> None:
    print(socket.gethostname())
