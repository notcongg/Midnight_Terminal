import json
from pathlib import Path

from src.shell.context.context import ShellContext


ALIAS_FILE = Path(__file__).resolve().parent / "aliases.json"


def _load_aliases() -> dict[str, str]:
    if not ALIAS_FILE.exists():
        return {}

    try:
        with ALIAS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        return {str(name): str(command) for name, command in data.items()}

    except (OSError, json.JSONDecodeError):
        return {}


def _save_aliases(aliases: dict[str, str]) -> None:
    try:
        with ALIAS_FILE.open("w", encoding="utf-8") as file:
            json.dump(aliases, file, indent=4, ensure_ascii=False)
    except OSError as error:
        print(f"Failed to save aliases: {error}")


def load_aliases(context: ShellContext) -> None:
    context.aliases = _load_aliases()


def expand_alias(command: str, context: ShellContext) -> str:
    parts = command.split()

    if not parts:
        return command

    alias = context.aliases.get(parts[0])

    if alias is None:
        return command

    if len(parts) == 1:
        return alias

    return f"{alias} {' '.join(parts[1:])}"


def cmd_alias(args: list[str], context: ShellContext) -> None:
    aliases = context.aliases

    if not args:
        if not aliases:
            print("No aliases.")
            return

        for name, command in aliases.items():
            print(f"{name} -> {command}")
        return

    if len(args) < 3 or args[1] != "=":
        print("alias <name> = <command>")
        return

    name = args[0]
    command = " ".join(args[2:])

    if not name:
        print("Alias name cannot be empty.")
        return

    aliases[name] = command
    _save_aliases(aliases)


def cmd_unalias(args: list[str], context: ShellContext) -> None:
    if not args:
        print("unalias <name>")
        return

    name = args[0]
    aliases = context.aliases

    if name not in aliases:
        print(f"Alias '{name}' not found.")
        return

    del aliases[name]
    _save_aliases(aliases)
    print(f"Alias '{name}' removed.")
