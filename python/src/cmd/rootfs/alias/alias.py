import json
from pathlib import Path

# ================= ALIAS =================

ALIAS_FILE = Path(__file__).resolve().parent / "aliases.json"
alias_map = {}


def load_aliases():
    global alias_map

    if not ALIAS_FILE.exists():
        alias_map = {}
        return

    try:
        with ALIAS_FILE.open("r", encoding="utf-8") as f:
            alias_map = json.load(f)

        if not isinstance(alias_map, dict):
            alias_map = {}

    except (json.JSONDecodeError, OSError):
        alias_map = {}


def save_aliases():
    try:
        with ALIAS_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                alias_map,
                f,
                indent=4,
                ensure_ascii=False
            )
    except OSError as e:
        print(f"Failed to save aliases: {e}")


# ================= EXPAND ALIAS =================

def expand_alias(cmd):
    parts = cmd.split()

    if parts and parts[0] in alias_map:
        return alias_map[parts[0]] + " " + " ".join(parts[1:])

    return cmd


# ================= ALIAS CMD =================

def cmd_alias(args):
    # alias
    if len(args) == 1:
        if not alias_map:
            print("No aliases.")
            return

        for name, command in alias_map.items():
            print(f"{name} -> {command}")

        return

    # alias <name> = <command>
    if len(args) < 4:
        print("alias <name> = <command>")
        return

    if args[2] != "=":
        print("Missing '='")
        return

    name = args[1]
    command = " ".join(args[3:])

    alias_map[name] = command
    save_aliases()



def cmd_unalias(args):
    if len(args) < 2:
        print("unalias <name>")
        return

    name = args[1]

    if name not in alias_map:
        print(f"Alias '{name}' not found.")
        return

    del alias_map[name]
    save_aliases()

    print(f"Alias '{name}' removed.")