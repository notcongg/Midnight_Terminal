import importlib
import inspect
from pathlib import Path

COMMANDS = {}
MANUALS = {}

ROOTFS_PATH = Path(__file__).resolve().parent.parent / "rootfs"
PACKAGE = f"{__package__.rsplit('.', 1)[0]}.rootfs"

_SKIP_DIR_NAMES = {"platform", "collection"}


def load_commands():
    COMMANDS.clear()

    for file in ROOTFS_PATH.rglob("*.py"):
        if file.name.startswith("_"):
            continue

        relative = file.relative_to(ROOTFS_PATH).with_suffix("")
        if any(part in _SKIP_DIR_NAMES for part in relative.parts):
            continue

        module_name = f"{PACKAGE}." + ".".join(relative.parts)

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"[CMD] Failed to load {module_name}: {e}")
            continue

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module.__name__:
                continue

            # Manual pages are associated with the command module that
            # defines the command itself (man_<name> next to cmd_<name>).
            if name.startswith("man_"):
                MANUALS[name[4:]] = obj
                continue

            if not name.startswith("cmd_"):
                continue

            command_name = name[4:]
            COMMANDS[command_name] = obj
