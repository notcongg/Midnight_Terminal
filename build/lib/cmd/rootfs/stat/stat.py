from __future__ import annotations

from datetime import datetime

from src.shell.context.context import ShellContext


def cmd_stat(args: list[str], context: ShellContext) -> str:
    if not args:
        return "Usage: stat <file>\n"

    output: list[str] = []

    for arg in args:
        target = context.resolve_path(arg)

        if not target.exists():
            output.append(f"stat: cannot stat '{arg}': File not found\n")
            continue

        try:
            info = target.stat()

            output.append(
                f"  File: {arg}\n"
                f"  Size: {info.st_size} bytes\n"
                f"  Type: {'directory' if target.is_dir() else 'file'}\n"
                f"  Modified: "
                f"{datetime.fromtimestamp(info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  Created: "
                f"{datetime.fromtimestamp(info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
        except OSError as exc:
            output.append(f"stat: cannot read '{arg}': {exc}\n")

    return "\n".join(output)
