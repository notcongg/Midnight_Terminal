from src.sot import MIDHSTY_PATH

from src.utils.paths import midhsty_path

<<<<<<< HEAD
path = MIDHSTY_PATH
=======

path: Path = midhsty_path()
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)


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
<<<<<<< HEAD

    -cmd=<count>    show last <count> commands

=======
    -cmd=<count>     show last <count> commands
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    -index=<number> show command at specific index

EXAMPLES
    history

    history -cmd=10

    history -index=5

SEE ALSO
    .midhsty(5)
"""


def cmd_history(*args, context=None):
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

<<<<<<< HEAD
    # Create config directory if it does not exist.
    path.parent.mkdir(
        parents=True,
        exist_ok=True
=======
    # Make sure the Midnight config directory exists.
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    )

    # Create history file if it does not exist.
    if not path.exists():
        path.touch()

<<<<<<< HEAD
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
=======
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        lines = file.read().splitlines()
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

    commands = []

    for i, line in enumerate(lines):
        if line.startswith("+"):
            commands.append(
                "\n".join(
<<<<<<< HEAD
                    lines[max(0, i - 1):i + 1]
=======
                    lines[
                        max(0, i - 1):i + 1
                    ]
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
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