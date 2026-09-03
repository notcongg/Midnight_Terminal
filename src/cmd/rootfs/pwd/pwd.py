from pathlib import Path

from src.shell.context.context import ShellContext
from src.ui.display_path.dp import display_path


def cmd_pwd(args, context: ShellContext):
    return display_path(Path(context.cwd))
