from pathlib import Path

from src.cmd.init import hostname, username
from src.cmd.rootfs.alias.alias import load_aliases
from src.cmd.utils.registry import load_commands
from src.shell.errors.errors import ShellError
from src.shell.shell import Shell
from src.ui.display_path.dp import display_path
from src.ui.ui import ui
from src.input.input import get_input


def run() -> None:
    load_commands()

    shell = Shell()
    load_aliases(shell.context)

    ui()

    while not shell.context.exit_requested:
        midnight_path = display_path(Path(shell.context.cwd))

        try:
            cmd = get_input(
                username=username,
                hostname=hostname,
                path=midnight_path,
            )
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        if not cmd.strip():
            continue

        try:
            shell.execute_line(cmd)
        except ShellError as exc:
            print(exc)
