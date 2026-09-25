from __future__ import annotations

import ctypes
import os
import stat
from datetime import datetime
from pathlib import Path

from src.shell.context.context import ShellContext
from src.ui.display_path.dp import display_path


BLUE = "\033[94m"
RESET = "\033[0m"


# ============================================================
# VOLUME INFO
# ============================================================

try:
    from src.cmd.rootfs.platform.windows.get_vol_info import (
        get_volume_label,
        get_volume_serial,
    )
except ImportError:

    def get_volume_label(path):
        return ""

    def get_volume_serial(path):
        return "0000-0000"


# ============================================================
# MAN
# ============================================================

def man_ls() -> str:
    return """LS(1)                    Midnight Terminal Manual                   LS(1)

NAME
    ls - list directory contents

SYNOPSIS
    ls
    ls -a
    ls -h
    ls -ah
    ls <directory>

DESCRIPTION
    Lists directory contents in a compact table.

    Directories are blue and end with '/'.
    File names are never truncated.

OPTIONS
    -a    show hidden files
    -h    show human-readable sizes

COLUMNS
    Mode
        Bash-style permission mode.

    Last Write Time
        Last modification time in 12-hour format.

    Size(B)
        File size in bytes.

    Size[h]
        Human-readable size when -h is used.

    Name
        File or directory name.

    Name[a]
        Header used when -a is enabled.

TIME
    00:00 - 11:59 = AM
    12:00 - 23:59 = PM

EXAMPLES
    ls
    ls -a
    ls -h
    ls -ah
    ls C:\\Users\\Congg

SEE ALSO
    dir(1), tree(1), find(1), pwd(1)
"""


# ============================================================
# HUMAN SIZE
# ============================================================

def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} EiB"


human_size = _human_size

# ============================================================
# WINDOWS HIDDEN
# ============================================================

def _is_hidden(path: Path) -> bool:
    if os.name != "nt":
        return path.name.startswith(".")

    try:
        get_attributes = (
            ctypes.windll.kernel32.GetFileAttributesW
        )
        get_attributes.argtypes = [ctypes.c_wchar_p]
        get_attributes.restype = ctypes.c_uint32

        attributes = get_attributes(str(path))

        if attributes == 0xFFFFFFFF:
            return path.name.startswith(".")

        FILE_ATTRIBUTE_HIDDEN = 0x2

        return bool(
            attributes & FILE_ATTRIBUTE_HIDDEN
        )

    except Exception:
        return path.name.startswith(".")


# ============================================================
# MODE
# ============================================================

def _mode(path: Path) -> str:
    """
    Return a Bash-style mode.

    Linux/Unix:
        use real POSIX mode bits.

    Windows:
        create a best-effort rwx representation using
        filesystem access checks.
    """

    try:
        mode = path.stat().st_mode
    except OSError:
        return "----------"

    if os.name != "nt":
        return stat.filemode(mode)

    # --------------------------------------------------------
    # Windows
    # --------------------------------------------------------

    try:
        is_dir = path.is_dir()

        readable = os.access(
            path,
            os.R_OK,
        )

        writable = os.access(
            path,
            os.W_OK,
        )

        executable = (
            os.access(path, os.X_OK)
            if not is_dir
            else False
        )

        prefix = "d" if is_dir else "-"

        r = "r" if readable else "-"
        w = "w" if writable else "-"
        x = "x" if executable else "-"

        # Windows does not use POSIX owner/group/other
        # permission bits, so mirror the available access
        # state into a Bash-style representation.
        return (
            prefix
            + r + w + x
            + r + w + x
            + r + w + x
        )

    except OSError:
        return "----------"


# ============================================================
# PATH RESOLUTION
# ============================================================

def _resolve_target(
    arg: str,
    context: ShellContext,
) -> Path:
    candidate = Path(arg)

    if candidate.is_absolute():
        return candidate

    return context.resolve_path(arg)


# ============================================================
# LS
# ============================================================

def cmd_ls(
    args: list[str],
    context: ShellContext,
) -> str:
    show_all = False
    human = False
    target = Path(context.cwd)

    for arg in args:
        if arg.startswith("-"):
            if "a" in arg:
                show_all = True

            if "h" in arg:
                human = True

            continue

        target = _resolve_target(
            arg,
            context,
        )

    if not target.exists():
        return "Path not found."

    if not target.is_dir():
        return f"{target}: Not a directory."

    entries: list[dict] = []

    try:
        for entry in target.iterdir():
            if (
                not show_all
                and _is_hidden(entry)
            ):
                continue

            try:
                info = entry.stat()
            except OSError:
                continue

            modified = datetime.fromtimestamp(
                info.st_mtime
            )

            entries.append(
                {
                    "path": entry,
                    "mode": _mode(entry),
                    "time": modified.strftime(
                        "%d/%m/%Y %I:%M %p"
                    ),
                    "size": info.st_size,
                    "name": entry.name,
                }
            )

    except PermissionError:
        return (
            f"Directory  : {display_path(target)}\n"
            "Access denied."
        )

    entries.sort(
        key=lambda item: item["name"].lower()
    )

    # ========================================================
    # HEADER NAMES
    # ========================================================

    size_header = (
        "Size[h]"
        if human
        else "Size(B)"
    )

    name_header = (
        "Name[a]"
        if show_all
        else "Name"
    )

    # ========================================================
    # COLUMN WIDTHS
    # ========================================================

    mode_width = max(
        len("Mode"),
        max(
            (
                len(item["mode"])
                for item in entries
            ),
            default=0,
        ),
    )

    time_width = max(
        len("Last Write Time"),
        max(
            (
                len(item["time"])
                for item in entries
            ),
            default=0,
        ),
    )

    size_width = max(
        len(size_header),
        max(
            (
                len(
                    _human_size(item["size"])
                    if human
                    else str(item["size"])
                )
                for item in entries
            ),
            default=0,
        ),
    )

    name_width = max(
        len(name_header),
        max(
            (
                len(item["name"])
                + (1 if item["path"].is_dir() else 0)
                for item in entries
            ),
            default=0,
        ),
    )

    # ========================================================
    # HEADER
    # ========================================================

    lines = [
        f"Directory  : {display_path(target)}",
        f"Disk name  : {get_volume_label(target)}",
        f"Disk serial: {get_volume_serial(target)}",
        "",
    ]

    lines.append(
        f"{'Mode':<{mode_width}}  "
        f"{'Last Write Time':<{time_width}}  "
        f"{size_header:>{size_width}}  "
        f"{name_header:<{name_width}}"
    )

    lines.append(
        f"{'-' * mode_width}  "
        f"{'-' * time_width}  "
        f"{'-' * size_width}  "
        f"{'-' * name_width}"
    )

    # ========================================================
    # ENTRIES
    # ========================================================

    for item in entries:
        path = item["path"]

        display_name = (
            f"{item['name']}/"
            if path.is_dir()
            else item["name"]
        )

        size_text = (
            _human_size(item["size"])
            if human
            else str(item["size"])
        )

        if path.is_dir():
            padded_name = (
                f"{display_name:<{name_width}}"
            )

            name_text = (
                f"{BLUE}{padded_name}{RESET}"
            )

        else:
            name_text = (
                f"{display_name:<{name_width}}"
            )

        lines.append(
            f"{item['mode']:<{mode_width}}  "
            f"{item['time']:<{time_width}}  "
            f"{size_text:>{size_width}}  "
            f"{name_text}"
        )

    return "\n".join(lines)