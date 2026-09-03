from __future__ import annotations

from src.cmd.utils.registry import COMMANDS
from src.shell.syntax.matcher import find_matches


SUGGESTION_THRESHOLD = 0.6
MAX_SUGGESTIONS = 3


def get_suggestions(command: str) -> list[str]:
    """
    Find the closest valid commands for an unknown command.
    """

    command = command.strip()

    if not command:
        return []

    matches = find_matches(
        command,
        COMMANDS.keys(),
        threshold=SUGGESTION_THRESHOLD,
    )

    return [
        candidate
        for candidate, _ in matches[:MAX_SUGGESTIONS]
    ]


def format_suggestions(command: str) -> str:
    """
    Format command suggestions for shell output.

    Examples:
        gerp -> Did you mean: grep?
        cta  -> Did you mean: cat, ...?
    """

    suggestions = get_suggestions(command)

    if not suggestions:
        return ""

    if len(suggestions) == 1:
        return f"Did you mean: {suggestions[0]}?"

    return "Did you mean: " + ", ".join(suggestions) + "?"
