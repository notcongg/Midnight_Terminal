from __future__ import annotations

from src.shell.context.context import ShellContext


def cmd_tail(args: list[str], context: ShellContext) -> str:
    lines_count = 10
    files: list[str] = []

    index = 0

    while index < len(args):
        arg = args[index]

        if arg == "-n":
            if index + 1 >= len(args):
                return "tail: option '-n' requires an argument\n"

            try:
                lines_count = int(args[index + 1])
            except ValueError:
                return f"tail: invalid number of lines: '{args[index + 1]}'\n"

            index += 2
            continue

        if arg.startswith("-n"):
            value = arg[2:]

            try:
                lines_count = int(value)
            except ValueError:
                return f"tail: invalid number of lines: '{value}'\n"

            index += 1
            continue

        files.append(arg)
        index += 1

    if lines_count < 0:
        return "tail: number of lines cannot be negative\n"

    if files:
        output: list[str] = []

        for file in files:
            target = context.resolve_path(file)

            if not target.exists() or not target.is_file():
                output.append(
                    f"tail: cannot open '{file}': File not found\n"
                )
                continue

            try:
                text = target.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                output.append(
                    "\n".join(text.splitlines()[-lines_count:])
                )
            except OSError as exc:
                output.append(
                    f"tail: cannot read '{file}': {exc}\n"
                )

        return "\n".join(output) + ("\n" if output else "")

    lines = context.stdin.read().splitlines()
    return "\n".join(lines[-lines_count:]) + "\n"
