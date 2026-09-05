from __future__ import annotations

import shutil
from pathlib import Path


def _format_size(size: int, human: bool) -> str:
    if not human:
        return str(size)

    units = ("B", "K", "M", "G", "T", "P")
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{int(size)} B"


def _get_windows_drives() -> list[Path]:
    drives: list[Path] = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = Path(f"{letter}:/")

        try:
            if drive.exists():
                shutil.disk_usage(drive)
                drives.append(drive)
        except OSError:
            continue

    return drives


def cmd_df(args: list[str], context) -> str:
    human = False
    show_all = False
    paths: list[str] = []

    for arg in args:
        if arg == "--":
            continue

        if arg.startswith("-") and arg != "-":
            if arg.startswith("--"):
                flag = arg[2:]

                if flag == "human-readable":
                    human = True
                elif flag == "all":
                    show_all = True
                else:
                    return f"df: invalid option '--{flag}'\n"

                continue

            for flag in arg[1:]:
                if flag == "h":
                    human = True
                elif flag == "a":
                    show_all = True
                else:
                    return f"df: invalid option '-{flag}'\n"

            continue

        paths.append(arg)

    # No path:
    # show all available Windows drives when -a is used.
    # Otherwise show the current filesystem.
    if not paths:
        if show_all:
            targets = _get_windows_drives()
        else:
            targets = [context.resolve_path(".")]
    else:
        targets = [
            context.resolve_path(path)
            for path in paths
        ]

    output: list[str] = []

    output.append(
        f"{'Filesystem':<14}"
        f"{'Total':>14}"
        f"{'Used':>14}"
        f"{'Available':>14}"
        f"{'Use%':>8}"
        f"  Mounted on"
    )

    for target in targets:
        try:
            usage = shutil.disk_usage(target)

            total = usage.total
            used = usage.used
            free = usage.free

            percent = (
                (used / total) * 100
                if total
                else 0
            )

            try:
                filesystem = target.anchor or str(target)
            except Exception:
                filesystem = str(target)

            output.append(
                f"{filesystem:<14}"
                f"{_format_size(total, human):>14}"
                f"{_format_size(used, human):>14}"
                f"{_format_size(free, human):>14}"
                f"{percent:>7.1f}%"
                f"  {target}"
            )

        except OSError as exc:
            output.append(
                f"df: cannot access '{target}': {exc}"
            )

    return "\n".join(output)
