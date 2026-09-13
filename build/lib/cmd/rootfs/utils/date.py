from datetime import datetime

from src.shell.context.context import ShellContext


def cmd_date(args: list[str], context: ShellContext) -> None:
    print(datetime.now())
