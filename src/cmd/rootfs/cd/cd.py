from src.shell.context.context import ShellContext


def cmd_cd(args: list[str], context: ShellContext) -> str | None:
    if not args:
        return context.cwd

    new_path = context.resolve_path(args[0])

    if new_path.exists() and new_path.is_dir():
        context.cwd = str(new_path.resolve())
        return None

    return "The system cannot find the path specified."
