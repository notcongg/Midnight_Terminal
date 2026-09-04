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
- Operators: |, >, >>, <
- Operators may be adjacent to words.

Windows compatibility:

- A trailing '\\' is treated as a literal path separator instead of
  a dangling escape.
- Backslash escaping behavior is otherwise preserved for compatibility
  with the existing shell syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from src.shell.errors.errors import LexerError


class TokenType(Enum):
    WORD = auto()
    PIPE = auto()
    GT = auto()
    APPEND = auto()
    LT = auto()


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
    """Internal cursor-based helper walking the raw input one char at a time."""

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


def tokenize(raw_input: str) -> list[Token]:
    """
    Tokenize a raw shell input string into Token objects.

    Raises LexerError on unterminated quotes.

    A trailing backslash is preserved literally so Windows paths such as:

        cd Desktop\\
        cd C:\\
        cd C:\\Users\\Congg\\

    remain valid shell words.
    """

    scanner = _Scanner(raw_input)
    tokens: list[Token] = []

    while True:
        _skip_unquoted_whitespace(scanner)

        if scanner.eof():
            break

        start_pos = scanner.i
        ch = scanner.peek()

        # Pipe
        if ch == "|":
            scanner.advance()
            tokens.append(
                Token(
                    TokenType.PIPE,
                    "|",
                    start_pos,
                )
            )
            continue

        # Input redirection
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

        # Output redirection
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

        # WORD
        word_value = _scan_word(scanner)

        tokens.append(
            Token(
                TokenType.WORD,
                word_value,
                start_pos,
            )
        )

    return tokens


def _skip_unquoted_whitespace(scanner: _Scanner) -> None:
    while (
        not scanner.eof()
        and scanner.peek() in (" ", "\t", "\n", "\r")
    ):
        scanner.advance()


def _is_word_terminator(ch: str | None) -> bool:
    """
    Characters that terminate a WORD when unquoted/unescaped.
    """

    return ch is None or ch in (
        " ",
        "\t",
        "\n",
        "\r",
        "|",
        ">",
        "<",
    )


def _scan_word(scanner: _Scanner) -> str:
    """
    Scan one WORD token.

    A word may contain:

        bare text
        'single quoted text'
        "double quoted text"
        escaped characters

    All pieces are concatenated.
    """

    pieces: list[str] = []

    while not scanner.eof():
        ch = scanner.peek()

        # Single quote
        if ch == "'":
            pieces.append(
                _scan_single_quoted(scanner)
            )
            continue

        # Double quote
        if ch == '"':
            pieces.append(
                _scan_double_quoted(scanner)
            )
            continue

        # Backslash
        if ch == "\\":
            pieces.append(
                _scan_escape(scanner)
            )
            continue

        # Word terminator
        if _is_word_terminator(ch):
            break

        pieces.append(
            scanner.advance()
        )

    return "".join(pieces)


def _scan_single_quoted(scanner: _Scanner) -> str:
    """
    Consume a single-quoted segment.

    Everything inside single quotes is literal.
    """

    open_pos = scanner.i

    # Opening quote
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


def _scan_double_quoted(scanner: _Scanner) -> str:
    """
    Consume a double-quoted segment.

    Recognized escapes:

        \\" -> "
        \\\\ -> \\

    Any other backslash is preserved literally.
    """

    open_pos = scanner.i

    # Opening quote
    scanner.advance()

    chars: list[str] = []

    while True:
        if scanner.eof():
            raise LexerError(
                "Unterminated double quote",
                position=open_pos,
            )

        ch = scanner.advance()

        # Closing quote
        if ch == '"':
            return "".join(chars)

        # Backslash
        if ch == "\\":
            nxt = scanner.peek()

            if nxt in ('"', "\\"):
                chars.append(
                    scanner.advance()
                )
            else:
                # Preserve unknown backslash sequences.
                chars.append(ch)

            continue

        chars.append(ch)


def _scan_escape(scanner: _Scanner) -> str:
    """
    Consume a backslash outside quotes.

    Normal behavior:

        \\| -> |
        \\  -> space
        \\\\ -> \\

    Windows compatibility:

        If the backslash is the FINAL character of the input,
        preserve it literally.

    This specifically allows:

        cd Desktop\\
        cd C:\\
        cd C:\\Users\\Congg\\
    """

    escape_pos = scanner.i

    # Consume '\\'
    scanner.advance()

    # ---------------------------------------------------------
    # Windows path compatibility
    # ---------------------------------------------------------
    #
    # A trailing backslash is a valid Windows path separator.
    #
    # Example:
    #
    #     cd Desktop\
    #
    # The old implementation interpreted this as an incomplete
    # escape sequence and raised:
    #
    #     Dangling escape character '\' at end of input
    #
    # Preserve it instead.
    #
    if scanner.eof():
        return "\\"

    # Normal escape behavior.
    return scanner.advance()
