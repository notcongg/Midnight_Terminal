import importlib
import inspect
import platform
from pathlib import Path

COMMANDS = {}
MANUALS = {}

ROOTFS_PATH = Path(__file__).resolve().parent.parent / "rootfs"
PACKAGE = f"{__package__.rsplit('.', 1)[0]}.rootfs"

_SKIP_DIR_NAMES = {"platform", "collection"}

# Platform-specific module mapping
# Maps module paths to platform-specific implementations
_PLATFORM_WINDOWS_MODULES = {
    "kill": "platform.windows.kill",
    "task": "platform.windows.task",
    "ps": "platform.windows.ps",
    "mv": "platform.windows.mv",
    "ls.get_vol_info": "platform.windows.get_vol_info",
}


def _get_platform_package() -> str:
    """Get the current platform identifier."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    return "linux"


def load_commands():
    COMMANDS.clear()
    MANUALS.clear()

    platform_pkg = _get_platform_package()

    for file in ROOTFS_PATH.rglob("*.py"):
        if file.name.startswith("_"):
            continue

        relative = file.relative_to(ROOTFS_PATH).with_suffix("")
        relative_parts = list(relative.parts)

        # Skip platform-specific directories - they are loaded separately
        if relative_parts[0] == "platform":
            continue

        # Skip other excluded directories
        if any(part in _SKIP_DIR_NAMES for part in relative_parts):
            continue

        module_name = f"{PACKAGE}." + ".".join(relative_parts)

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

    # Load platform-specific commands
    _load_platform_commands(platform_pkg)


def _load_platform_commands(platform_pkg: str) -> None:
    """Load platform-specific commands from the platform directory."""
    platform_path = ROOTFS_PATH / "platform" / platform_pkg

    if not platform_path.exists():
        return

    for file in platform_path.glob("*.py"):
        if file.name.startswith("_"):
            continue

        module_name = f"{PACKAGE}.platform.{platform_pkg}.{file.stem}"

        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"[CMD] Failed to load {module_name}: {e}")
            continue

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module.__name__:
                continue

            if name.startswith("man_"):
                MANUALS[name[4:]] = obj
                continue

            if not name.startswith("cmd_"):
                continue

            command_name = name[4:]
            COMMANDS[command_name] = obj
