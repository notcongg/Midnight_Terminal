from src.shell.context.context import ShellContext


def cmd_exit(args: list[str], context: ShellContext) -> None:
    context.exit_requested = True
