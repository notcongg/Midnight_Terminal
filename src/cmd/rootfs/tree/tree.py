from __future__ import annotations

from pathlib import Path
from typing import Any

from src.shell.context.context import ShellContext
from src.shell.errors.errors import ShellError

from src.cmd.rootfs.ls.ls import human_size


def _resolve_target(context: ShellContext, value: str | None) -> Path:
    """Resolve a path against the shell's current working directory."""

    if value is None:
        return Path(context.cwd).resolve()

    return context.resolve_path(value).resolve()


def _format_size(target: Path, human: bool) -> str:
    """Return the formatted size of a filesystem entry."""

    if target.is_dir():
        return ""

    try:
        size = target.stat().st_size
    except OSError:
        return ""

    return human_size(size) if human else f"{size} B"


def _is_allowed(
    target: Path,
    show_all: bool,
    only_dir: bool,
) -> bool:
    """Check whether an entry should appear in the tree."""

    if not show_all and target.name.startswith("."):
        return False

    if only_dir and not target.is_dir():
        return False

    return True


def _get_children(
    folder: Path,
    show_all: bool,
    only_dir: bool,
) -> list[Path] | None:
    """Get visible children of a directory."""

    try:
        children = [
            item
            for item in folder.iterdir()
            if _is_allowed(item, show_all, only_dir)
        ]
    except PermissionError:
        return None
    except OSError:
        return []

    # Directories first, then files.
    children.sort(
        key=lambda item: (
            not item.is_dir(),
            item.name.lower(),
        )
    )

    return children


def _walk(
    folder: Path,
    prefix: str,
    depth: int,
    depth_limit: int | None,
    show_all: bool,
    only_dir: bool,
    human: bool,
) -> None:
    """Recursively print the directory tree."""

    if depth_limit is not None and depth >= depth_limit:
        return

    children = _get_children(
        folder,
        show_all=show_all,
        only_dir=only_dir,
    )

    if children is None:
        print(f"{prefix}└── [Access Denied]")
        return

    for index, item in enumerate(children):
        is_last = index == len(children) - 1

        connector = "└── " if is_last else "├── "
        name = item.name

        if item.is_dir():
            name += "/"
        else:
            size = _format_size(item, human)

            if size:
                name += f" {size}"

        print(prefix + connector + name)

        if item.is_dir():
            child_prefix = prefix + (
                "    " if is_last else "│   "
            )

            _walk(
                item,
                prefix=child_prefix,
                depth=depth + 1,
                depth_limit=depth_limit,
                show_all=show_all,
                only_dir=only_dir,
                human=human,
            )


def _parse_tree_args(
    args: list[Any],
) -> tuple[bool, bool, bool, int | None, str | None]:
    """
    Parse tree arguments.

    Returns:
        show_all,
        only_dir,
        human,
        depth_limit,
        target
    """

    show_all = False
    only_dir = False
    human = False
    depth_limit: int | None = None
    target: str | None = None

    i = 0

    while i < len(args):
        arg = str(args[i])

        if arg == "tree":
            i += 1
            continue

        if arg == "-a":
            show_all = True

        elif arg == "-d":
            only_dir = True

        elif arg == "-h":
            human = True

        elif arg == "-L":
            if i + 1 >= len(args):
                raise ShellError(
                    "tree: missing depth value after '-L'"
                )

            try:
                depth_limit = int(args[i + 1])
            except ValueError as exc:
                raise ShellError(
                    f"tree: invalid depth value: {args[i + 1]}"
                ) from exc

            if depth_limit < 0:
                raise ShellError(
                    "tree: depth cannot be negative"
                )

            i += 1

        elif arg.startswith("-"):
            raise ShellError(
                f"tree: unknown option '{arg}'"
            )

        elif target is None:
            target = arg

        else:
            raise ShellError(
                f"tree: unexpected argument '{arg}'"
            )

        i += 1

    return (
        show_all,
        only_dir,
        human,
        depth_limit,
        target,
    )


def cmd_tree(
    args: list[Any],
    context: ShellContext,
) -> None:
    """
    Display a directory tree.

    Usage:
        tree
        tree <path>
        tree -a
        tree -d
        tree -h
        tree -L <depth>
    """

    (
        show_all,
        only_dir,
        human,
        depth_limit,
        target_arg,
    ) = _parse_tree_args(args)

    try:
        target = _resolve_target(
            context,
            target_arg,
        )
    except OSError as exc:
        raise ShellError(
            f"tree: cannot resolve path"
        ) from exc

    if not target.exists():
        raise ShellError(
            f"tree: path not found: {target}"
        )

    if not target.is_dir():
        raise ShellError(
            f"tree: not a directory: {target}"
        )

    print(target)

    _walk(
        target,
        prefix="",
        depth=0,
        depth_limit=depth_limit,
        show_all=show_all,
        only_dir=only_dir,
        human=human,
    )
