"""
lexer.py

Converts raw shell input into a flat list of Token objects.

Supported syntax:

- Whitespace-separated words.
- Single quotes: '...'
  Everything inside is literal.
- Double quotes: "..."
  Backslash may escape '"' or '\\'.
- Backslash escapes outside quotes.
- Operators: |, >, >>, <, &&, ||, ;
- Operators may be adjacent to words.
- Variable expansion outside quotes and inside double quotes:
  $VAR, ${VAR}, $? (only when tokenize() is given a ShellContext;
  single-quoted text is never expanded).

Windows compatibility:

- A trailing '\\' is treated as a literal path separator instead of
  a dangling escape.
- Backslash escaping behavior is otherwise preserved for compatibility
  with the existing shell syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from src.cmd.rootfs.env.env import ENV
from src.shell.errors.errors import LexerError
from src.shell.lexer.prelexer import (
    prelex,
    restore_literal_dollars,
)

if TYPE_CHECKING:
    from src.shell.context.context import ShellContext


class TokenType(Enum):
    WORD = auto()
    PIPE = auto()
    GT = auto()
    APPEND = auto()
    LT = auto()
    AND = auto()
    OR = auto()
    SEMI = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int

    def __repr__(self) -> str:
        return (
            f"Token({self.type.name}, "
            f"{self.value!r}, "
            f"pos={self.position})"
        )


class _Scanner:
    def __init__(self, text: str) -> None:
        self.text = text
        self.length = len(text)
        self.i = 0

    def eof(self) -> bool:
        return self.i >= self.length

    def peek(self) -> str | None:
        if self.eof():
            return None
        return self.text[self.i]

    def advance(self) -> str:
        ch = self.text[self.i]
        self.i += 1
        return ch


def tokenize(
    raw_input: str,
    context: ShellContext | None = None,
) -> list[Token]:
    raw_input = prelex(raw_input)

    scanner = _Scanner(raw_input)
    tokens: list[Token] = []

    while True:
        _skip_unquoted_whitespace(scanner)

        if scanner.eof():
            break

        start_pos = scanner.i
        ch = scanner.peek()

        if ch == "&":
            scanner.advance()

            if scanner.peek() == "&":
                scanner.advance()
                tokens.append(
                    Token(
                        TokenType.AND,
                        "&&",
                        start_pos,
                    )
                )
                continue

            raise LexerError(
                "Unexpected '&' "
                "(background jobs are not supported; "
                "quote it or use '&&')",
                position=start_pos,
            )

        if ch == "|":
            scanner.advance()

            if scanner.peek() == "|":
                scanner.advance()
                tokens.append(
                    Token(
                        TokenType.OR,
                        "||",
                        start_pos,
                    )
                )
            else:
                tokens.append(
                    Token(
                        TokenType.PIPE,
                        "|",
                        start_pos,
                    )
                )

            continue

        if ch == ";":
            scanner.advance()

            tokens.append(
                Token(
                    TokenType.SEMI,
                    ";",
                    start_pos,
                )
            )

            continue

        if ch == "<":
            scanner.advance()

            tokens.append(
                Token(
                    TokenType.LT,
                    "<",
                    start_pos,
                )
            )

            continue

        if ch == ">":
            scanner.advance()

            if scanner.peek() == ">":
                scanner.advance()

                tokens.append(
                    Token(
                        TokenType.APPEND,
                        ">>",
                        start_pos,
                    )
                )
            else:
                tokens.append(
                    Token(
                        TokenType.GT,
                        ">",
                        start_pos,
                    )
                )

            continue

        word_value = _scan_word(
            scanner,
            context,
        )

        tokens.append(
            Token(
                TokenType.WORD,
                word_value,
                start_pos,
            )
        )

    for token in tokens:
        if token.type is TokenType.WORD:
            token.value = restore_literal_dollars(
                token.value
            )

    return tokens


def _skip_unquoted_whitespace(
    scanner: _Scanner,
) -> None:
    while (
        not scanner.eof()
        and scanner.peek() in (
            " ",
            "\t",
            "\n",
            "\r",
        )
    ):
        scanner.advance()


def _is_word_terminator(
    ch: str | None,
) -> bool:
    return ch is None or ch in (
        " ",
        "\t",
        "\n",
        "\r",
        "|",
        ">",
        "<",
        "&",
        ";",
    )


def _is_name_char(
    ch: str | None,
) -> bool:
    return (
        ch is not None
        and (
            ch.isalnum()
            or ch == "_"
        )
    )


def _lookup_variable(
    context: ShellContext,
    name: str,
) -> str:
    """
    Look up a variable in Midnight Terminal's ENV.

    envconfig.dream is the source of truth for shell
    environment variables.
    """
    return ENV.get(name, "")


def _scan_variable(
    scanner: _Scanner,
    context: ShellContext,
) -> str:
    dollar_pos = scanner.i

    scanner.advance()

    ch = scanner.peek()

    if ch == "?":
        scanner.advance()
        return str(context.last_exit_code)

    if ch == "{":
        scanner.advance()

        chars: list[str] = []

        while (
            not scanner.eof()
            and scanner.peek() != "}"
        ):
            chars.append(
                scanner.advance()
            )

        if scanner.eof():
            raise LexerError(
                "Unterminated variable reference '${'",
                position=dollar_pos,
            )

        scanner.advance()

        return _lookup_variable(
            context,
            "".join(chars),
        )

    if (
        ch is not None
        and (
            ch.isalpha()
            or ch == "_"
        )
    ):
        chars: list[str] = [
            scanner.advance()
        ]

        while _is_name_char(
            scanner.peek()
        ):
            chars.append(
                scanner.advance()
            )

        return _lookup_variable(
            context,
            "".join(chars),
        )

    return "$"


def _scan_word(
    scanner: _Scanner,
    context: ShellContext | None = None,
) -> str:
    pieces: list[str] = []

    while not scanner.eof():
        ch = scanner.peek()

        if ch == "'":
            pieces.append(
                _scan_single_quoted(scanner)
            )
            continue

        if ch == '"':
            pieces.append(
                _scan_double_quoted(
                    scanner,
                    context,
                )
            )
            continue

        if ch == "\\":
            pieces.append(
                _scan_escape(scanner)
            )
            continue

        if ch == "$" and context is not None:
            pieces.append(
                _scan_variable(
                    scanner,
                    context,
                )
            )
            continue

        if _is_word_terminator(ch):
            break

        pieces.append(
            scanner.advance()
        )

    return "".join(pieces)


def _scan_single_quoted(
    scanner: _Scanner,
) -> str:
    open_pos = scanner.i

    scanner.advance()

    chars: list[str] = []

    while True:
        if scanner.eof():
            raise LexerError(
                "Unterminated single quote",
                position=open_pos,
            )

        ch = scanner.advance()

        if ch == "'":
            return "".join(chars)

        chars.append(ch)


def _scan_double_quoted(
    scanner: _Scanner,
    context: ShellContext | None = None,
) -> str:
    open_pos = scanner.i

    scanner.advance()

    chars: list[str] = []

    while True:
        if scanner.eof():
            raise LexerError(
                "Unterminated double quote",
                position=open_pos,
            )

        ch = scanner.advance()

        if ch == '"':
            return "".join(chars)

        if ch == "$" and context is not None:
            chars.append(
                _scan_variable(
                    scanner,
                    context,
                )
            )
            continue

        if ch == "\\":
            nxt = scanner.peek()

            if nxt in (
                '"',
                "\\",
                "$",
            ):
                chars.append(
                    scanner.advance()
                )
            else:
                chars.append(ch)

            continue

        chars.append(ch)


def _scan_escape(
    scanner: _Scanner,
) -> str:
    escape_pos = scanner.i

    scanner.advance()

    if scanner.eof():
        return "\\"

    return scanner.advance()
