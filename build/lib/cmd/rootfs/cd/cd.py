from pathlib import Path

from src.shell.context.context import ShellContext


def cmd_cd(
    args: list[str],
    context: ShellContext,
) -> str | None:
    if not args:
        return str(context.cwd)

    target = args[0]

    # --------------------------------------------------------
    # WINDOWS DRIVE
    # --------------------------------------------------------
    # "D:" and "d:" mean switching to the D drive.
    # Treat them explicitly instead of passing them to
    # Path.resolve_path(), where "D:" is drive-relative.
    if (
        len(target) == 2
        and target[1] == ":"
        and target[0].isalpha()
    ):
        drive = target[0].upper()

        new_path = Path(f"{drive}:\\").resolve()

        if new_path.exists() and new_path.is_dir():
            context.cwd = str(new_path)
            return None

        return "The system cannot find the path specified."

    # --------------------------------------------------------
    # NORMAL PATH
    # --------------------------------------------------------

    new_path = context.resolve_path(target)

    if new_path.exists() and new_path.is_dir():
        context.cwd = str(new_path.resolve())
        return None

    return "The system cannot find the path specified."
