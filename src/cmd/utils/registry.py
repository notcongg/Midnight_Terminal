import importlib
import inspect
from pathlib import Path

COMMANDS = {}

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
            if not name.startswith("cmd_"):
                continue

            if obj.__module__ != module.__name__:
                continue

            command_name = name[4:]
            COMMANDS[command_name] = obj
