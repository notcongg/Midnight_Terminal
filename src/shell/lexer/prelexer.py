from __future__ import annotations


_LITERAL_DOLLAR = "\x00MIDNIGHT_LITERAL_DOLLAR\x00"

_PROTECTED_COMMANDS = {
    "set",
    "enfix",
}


def prelex(raw_input: str) -> str:
    """
    Protect literal '$' characters for commands that store raw
    environment configuration.

    `set` and `enfix` must preserve values such as:

        $NAME
        $HOST
        $PWD
        $

    so the main lexer does not expand them.
    """

    stripped = raw_input.lstrip()

    if not stripped:
        return raw_input

    command = stripped.split(None, 1)[0].lower()

    if command not in _PROTECTED_COMMANDS:
        return raw_input

    return raw_input.replace(
        "$",
        _LITERAL_DOLLAR,
    )


def restore_literal_dollars(value: str) -> str:
    """
    Restore protected '$' characters after lexing.
    """

    return value.replace(
        _LITERAL_DOLLAR,
        "$",
    )
