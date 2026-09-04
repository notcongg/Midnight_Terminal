from pathlib import Path

from src.cmd.init import hostname, username
from src.cmd.rootfs.alias.alias import load_aliases
from src.cmd.utils.registry import load_commands
from src.input.input import get_input
from src.shell.errors.errors import ShellError
from src.shell.shell import Shell
from src.shell.syntax.corrector import correct_command
from src.shell.syntax.validator import validate
from src.ui.display_path.dp import display_path
import os

def run() -> None:
    os.system('cls')
    load_commands()

    shell = Shell()

    load_aliases(shell.context)

    ver = "0.000.0013"

    print("Welcome to Midnight Terminal.")
    print(f"[VERSION {ver}] ALPHA - (c) Congg 2026.")
    print()

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

        cmd = correct_command(cmd)

        result = validate(cmd)

        if not result.valid:
            print(f"syntax error: {result.error}")
            continue

        try:
            shell.execute_line(cmd)
        except ShellError as exc:
            print(exc)
