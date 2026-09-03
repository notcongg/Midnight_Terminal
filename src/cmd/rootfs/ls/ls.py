from datetime import datetime
from pathlib import Path

from src.cmd.rootfs.ls.get_vol_info import get_volume_label, get_volume_serial
from src.shell.context.context import ShellContext
from src.ui.display_path.dp import display_path


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
