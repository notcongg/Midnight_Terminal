from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable


def similarity(source: str, target: str) -> float:
    return SequenceMatcher(
        None,
        source.lower(),
        target.lower(),
    ).ratio()


def find_matches(
    command: str,
    commands: Iterable[str],
    threshold: float = 0.6,
) -> list[tuple[str, float]]:
    matches: list[tuple[str, float]] = []

    for candidate in commands:
        score = similarity(command, candidate)

        if score >= threshold:
            matches.append((candidate, score))

    matches.sort(
        key=lambda match: match[1],
        reverse=True,
    )

    return matches


def find_best_match(
    command: str,
    commands: Iterable[str],
    threshold: float = 0.6,
) -> str | None:
    matches = find_matches(
        command,
        commands,
        threshold,
    )

    if not matches:
        return None

    return matches[0][0]
