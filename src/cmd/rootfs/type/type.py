from __future__ import annotations

import shutil

from src.cmd.utils.registry import COMMANDS
from src.shell.context.context import ShellContext


def cmd_type(args: list[str], context: ShellContext) -> str:
    if not args:
        return "Usage: type <command>\n"

    output: list[str] = []

    for name in args:
        if name in context.aliases:
            output.append(
                f"{name} is an alias for '{context.aliases[name]}'"
            )
            continue

        if name in COMMANDS:
            output.append(f"{name} is a builtin command")
            continue

        executable = shutil.which(name)

        if executable:
            output.append(
                f"{name} is an external command\n"
                f"Path: {executable}"
            )
            continue

        output.append(f"{name}: command not found")

    return "\n".join(output) + "\n"
