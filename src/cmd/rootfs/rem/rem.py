from src.shell.context.context import ShellContext


def man_rem() -> str:
    return """REM(1)                   Midnight Terminal Manual                  REM(1)

NAME

    rem - rename files or directories

SYNOPSIS

    rem <old> <new>

DESCRIPTION

    Renames a file or directory.

EXAMPLES

    rem old.txt new.txt
    rem old_folder new_folder

SEE ALSO

    mv(1), cp(1), rm(1)

"""


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
