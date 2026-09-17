from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    TEXT = auto()
    COMMENT = auto()
    DOUBLE_STRING = auto()
    SINGLE_STRING = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    text: str


def highlight(text: str) -> list[Token]:
    """
    Tokenize text for Midnight syntax highlighting.

    Supported syntax:
        // comment
        /* multi-line comment */
        "double-quoted string"
        'single-quoted string'

    Comments have precedence over strings.

    Therefore:
        // "hello"

        /* 'hello' */

    are entirely COMMENT tokens.
    """
    tokens: list[Token] = []
    buffer: list[str] = []

    i = 0
    length = len(text)

    def flush_text() -> None:
        if buffer:
            tokens.append(
                Token(
                    TokenType.TEXT,
                    "".join(buffer),
                )
            )
            buffer.clear()

    while i < length:
        # ----------------------------------------------------
        # Single-line comment
        # ----------------------------------------------------
        if text.startswith("//", i):
            flush_text()
            end = text.find("\n", i)

            if end == -1:
                end = length

            tokens.append(
                Token(
                    TokenType.COMMENT,
                    text[i:end],
                )
            )

            i = end
            continue

        # ----------------------------------------------------
        # Multi-line comment
        # ----------------------------------------------------
        if text.startswith("/*", i):
            flush_text()
            end = text.find("*/", i + 2)

            if end == -1:
                # Unterminated comment:
                # highlight everything until EOF.
                tokens.append(
                    Token(
                        TokenType.COMMENT,
                        text[i:],
                    )
                )
                break

            end += 2

            tokens.append(
                Token(
                    TokenType.COMMENT,
                    text[i:end],
                )
            )

            i = end
            continue

        # ----------------------------------------------------
        # Double-quoted string
        # ----------------------------------------------------
        if text[i] == '"':
            flush_text()
            start = i
            i += 1

            while i < length:
                if text[i] == "\\":
                    # Skip escaped character.
                    i += 2
                    continue

                if text[i] == '"':
                    i += 1
                    break

                i += 1

            tokens.append(
                Token(
                    TokenType.DOUBLE_STRING,
                    text[start:i],
                )
            )
            continue

        # ----------------------------------------------------
        # Single-quoted string
        # ----------------------------------------------------
        if text[i] == "'":
            flush_text()
            start = i
            i += 1

            while i < length:
                if text[i] == "\\":
                    # Skip escaped character.
                    i += 2
                    continue

                if text[i] == "'":
                    i += 1
                    break

                i += 1

            tokens.append(
                Token(
                    TokenType.SINGLE_STRING,
                    text[start:i],
                )
            )
            continue

        # ----------------------------------------------------
        # Normal text
        # ----------------------------------------------------
        buffer.append(text[i])
        i += 1

    flush_text()
    return tokens