from __future__ import annotations

from src.input.prompt import prompt


def get_input(
    *,
    username: str,
    hostname: str,
    path: str,
) -> str:
    return prompt(
        username=username,
        hostname=hostname,
        path=path,
    )
