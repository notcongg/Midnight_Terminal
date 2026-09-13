
from __future__ import annotations

from src.shell.context.context import ShellContext


def cmd_grep(
    args: list[str],
    context: ShellContext,
) -> str:
    """
    Filter lines from stdin.

    Usage:

        grep code
        ps | grep code

    For process-table input from `ps`, the header and
    separator are preserved automatically.
    """

    if not args:
        raise ValueError(
            "missing pattern"
        )

    pattern = args[0].lower()

    input_data = context.stdin.read()

    if not input_data:
        return ""

    lines = input_data.splitlines()

    # --------------------------------------------------------
    # Detect ps-style table header.
    # --------------------------------------------------------

    header: list[str] = []
    matches: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Keep the process table header.
        if stripped.startswith("PID") and "NAME" in stripped:
            header.append(line)
            continue

        # Keep separator.
        if stripped and set(stripped) == {"-"}:
            header.append(line)
            continue

        # Normal grep matching.
        if pattern in line.lower():
            matches.append(line)

    # --------------------------------------------------------
    # Preserve ps header when there are matches.
    # --------------------------------------------------------

    if matches and header:
        return "\n".join(
            (*header, *matches)
        )

    return "\n".join(
        matches
    )
