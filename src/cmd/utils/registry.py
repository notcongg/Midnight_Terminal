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


def _register_module_functions(
    module,
    source: str,
) -> None:
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

        _register_module_functions(module, module_name)

    # Load platform-specific commands
    if platform_pkg == "linux":
        # The linux package also exposes the same linux-only commands
        # via its __init__, so register those when present.
        try:
            package_module = importlib.import_module(
                f"{PACKAGE}.platform.linux",
            )
        except Exception as e:
            print(f"[CMD] Failed to load {PACKAGE}.platform.linux: {e}")
        else:
            _register_module_functions(
                package_module,
                f"{PACKAGE}.platform.linux",
            )

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

        _register_module_functions(module, module_name)
