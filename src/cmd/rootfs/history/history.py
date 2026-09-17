from src.sot import MIDHSTY_PATH


path = MIDHSTY_PATH


def man_history() -> str:
    return """HISTORY(1)               Midnight Terminal Manual              HISTORY(1)

NAME

    history - display command history

SYNOPSIS

    history

    history -cmd=<count>

    history -index=<number>

DESCRIPTION

    Shows previously executed commands.

OPTIONS

    -cmd=<count>    show last <count> commands

    -index=<number> show command at specific index

EXAMPLES

    history

    history -cmd=10

    history -index=5

SEE ALSO

    .midhsty(5)

"""


def cmd_history(args, context):
    command_number = None
    command_index = None

    for arg in args:
        if arg.startswith("-cmd="):
            command_number = int(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-index="):
            command_index = int(
                arg.split("=", 1)[1]
            )

    # Create config directory if it does not exist.
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Create history file if it does not exist.
    if not path.exists():
        path.touch()

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            lines = file.read().splitlines()

    except OSError as error:
        raise RuntimeError(
            f"history: failed to read history file: {error}"
        ) from error

    commands = []

    for i, line in enumerate(lines):
        if line.startswith("+"):
            commands.append(
                "\n".join(
                    lines[max(0, i - 1):i + 1]
                )
            )

    if command_number is not None:
        return "\n\n".join(
            commands[-command_number:]
        )

    if command_index is not None:
        if not 1 <= command_index <= len(commands):
            raise ValueError(
                f"history: index {command_index} out of range"
            )

        return commands[command_index - 1]

    return "\n\n".join(commands)