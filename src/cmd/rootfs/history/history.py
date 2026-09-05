from pathlib import Path

from src.cmd.rootfs.tail.tail import cmd_tail


path = Path(__file__).resolve().parents[3] / "history" / ".midnight_history"


def cmd_history(args, context):
    command_number = None
    command_index = None

    for arg in args:
        if arg.startswith("-cmd="):
            command_number = int(arg.split("=", 1)[1])

        elif arg.startswith("-index="):
            command_index = int(arg.split("=", 1)[1])

    with open(path, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    commands = []

    for i, line in enumerate(lines):
        if line.startswith("+"):
            commands.append("\n".join(lines[max(0, i - 1):i + 1]))

    if command_number is not None:
        return "\n\n".join(commands[-command_number:])

    if command_index is not None:
        if not 1 <= command_index <= len(commands):
            raise ValueError(
                f"history: index {command_index} out of range"
            )

        return commands[command_index - 1]

    return "\n\n".join(commands)
