import platform
from datetime import datetime
from pathlib import Path

from src.shell.context.context import ShellContext
from src.ui.display_path.dp import display_path

try:
    from src.cmd.rootfs.platform.windows.get_vol_info import get_volume_label, get_volume_serial
except ImportError:
    # Linux fallback - no volume info available
    def get_volume_label(p):
        return ""

    def get_volume_serial(p):
        return "0000-0000"


def man_ls() -> str:
    return """LS(1)                    Midnight Terminal Manual                   LS(1)

NAME

    ls - list directory contents

SYNOPSIS

    ls [options] [directory]

DESCRIPTION

    Lists files and directories.

OPTIONS

    -a      show hidden files
    -h      human-readable sizes

EXAMPLES

    ls
    ls -la
    ls /home

SEE ALSO

    dir(1), tree(1), find(1), pwd(1)

"""


def human_size(size: int) -> str:
    value = float(size)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} EiB"


def cmd_ls(args: list[str], context: ShellContext) -> str:
    show_all = False
    human = False
    target = Path(context.cwd)

    for arg in args:
        if arg.startswith("-"):
            if "a" in arg:
                show_all = True
            if "h" in arg:
                human = True
        else:
            target = context.resolve_path(arg)

    if not target.exists():
        return "Path not found."

    if not target.is_dir():
        return f"{target}: Not a directory."

    lines: list[str] = []
    serial = get_volume_serial(target)

    lines.append(f" Volume in drive {target.drive} {get_volume_label(target)}.")
    lines.append(f" Volume Serial Number is {serial}")
    lines.append("")
    lines.append(f" Directory of {display_path(target)}")
    lines.append("")
    lines.append(f"{'Time':<22}|| {'Name':<28}|| {'Size':>12}")
    lines.append("-" * 66)

    try:
        for f in target.iterdir():
            if not show_all and f.name.startswith("."):
                continue

            try:
                stat = f.stat()
            except OSError:
                continue

            modified = datetime.fromtimestamp(stat.st_mtime)
            time_str = modified.strftime("%d/%m/%Y %H:%M")

            name = f.name
            if len(name) > 28:
                name = name[:25] + "..."

            if f.is_dir():
                size = "<DIR>"
            else:
                size_bytes = stat.st_size
                size = human_size(size_bytes) if human else f"{size_bytes} B"

            lines.append(f"{time_str:<22}|| {name:<28}|| {size:>12}")

    except PermissionError:
        lines.append("Access denied.")

    return "\n".join(lines)
