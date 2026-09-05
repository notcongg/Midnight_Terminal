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
from src.cmd.rootfs.env.env import reload_envconfig

from src.cmd.rootfs.env.env import ENV

import os


def run() -> None:
    os.system("cls")

    load_commands()

    shell = Shell()

    reload_envconfig(shell.context)
    load_aliases(shell.context)

    ver = "1.000.0001"

    print("Welcome to Midnight Terminal.")
    print(f"[VERSION {ver}] RELEASE - (c) Congg 2026.")
    print()

    while not shell.context.exit_requested:
        # ----------------------------------------------------
        # SYNC CURRENT WORKING DIRECTORY
        # ----------------------------------------------------

        current_path = Path(shell.context.cwd)

        ENV["PWD"] = display_path(current_path)

        midnight_path = display_path(
            current_path
        )

        # ----------------------------------------------------
        # INPUT
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # EMPTY INPUT
        # ----------------------------------------------------

        if not cmd.strip():
            continue

        # ----------------------------------------------------
        # SYNTAX CORRECTION
        # ----------------------------------------------------

        cmd = correct_command(cmd)

        # ----------------------------------------------------
        # SYNTAX VALIDATION
        # ----------------------------------------------------

        result = validate(cmd)

        if not result.valid:
            print(
                f"syntax error: {result.error}"
            )
            continue

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        try:
            shell.execute_line(cmd)

        except ShellError as exc:
            print(exc)
