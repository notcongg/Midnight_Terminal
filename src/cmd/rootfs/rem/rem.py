from src.shell.context.context import ShellContext


def cmd_rem(args: list[str], context: ShellContext) -> None:
    if len(args) < 2:
        print("rem <old> <new>")
        return

    old = context.resolve_path(args[0])
    new = context.resolve_path(args[1])

    if not old.exists():
        print("Target not found.")
        return

    try:
        old.rename(new)
        print(f"Renamed -> {new}")
    except OSError as error:
        print(f"Rename failed: {error}")
