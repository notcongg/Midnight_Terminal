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
from src.shell.lexer.prelexer import (
    prelex,
    restore_literal_dollars,
)

from src.shell.errors.errors import LexerError

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


def tokenize(
    raw_input: str,
    context: ShellContext | None = None,
) -> list[Token]:
    """
    Tokenize a raw shell input string into Token objects.
    """

    raw_input = prelex(raw_input)

    scanner = _Scanner(raw_input)
    tokens: list[Token] = []

    while True:
        _skip_unquoted_whitespace(scanner)

        if scanner.eof():
            break

        start_pos = scanner.i
        ch = scanner.peek()

        # Logical AND (&&)
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

        # Pipe / logical OR
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

        # Command separator
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
        "&",
        ";",
    )


def _is_name_char(ch: str | None) -> bool:
    """Characters allowed in a variable name after the first one."""
    return ch is not None and (ch.isalnum() or ch == "_")


def _lookup_variable(
    context: ShellContext,
    name: str,
) -> str:
    """Look up a variable in the session environment ('' when unset)."""
    return context.environment.get(name, "")


def _scan_variable(
    scanner: _Scanner,
    context: ShellContext,
) -> str:
    """
    Consume a '$' and the variable reference that follows it.

    Supported forms:

        $NAME     -> environment lookup ('' when unset)
        ${NAME}   -> same, with explicit braces
        $?        -> exit status of the previous command

    A '$' not followed by a name or '?' is preserved literally.
    """

    dollar_pos = scanner.i

    # Consume '$'
    scanner.advance()

    ch = scanner.peek()

    # Special parameter: exit status of the previous command.
    if ch == "?":
        scanner.advance()
        return str(context.last_exit_code)

    # Braced form: ${NAME}
    if ch == "{":
        scanner.advance()

        chars: list[str] = []

        while not scanner.eof() and scanner.peek() != "}":
            chars.append(scanner.advance())

        if scanner.eof():
            raise LexerError(
                "Unterminated variable reference '${'",
                position=dollar_pos,
            )

        # Consume '}'
        scanner.advance()

        return _lookup_variable(context, "".join(chars))

    # Bare form: $NAME
    if ch is not None and (ch.isalpha() or ch == "_"):
        chars: list[str] = [scanner.advance()]

        while _is_name_char(scanner.peek()):
            chars.append(scanner.advance())

        return _lookup_variable(context, "".join(chars))

    # '$' followed by nothing meaningful stays literal.
    return "$"


def _scan_word(
    scanner: _Scanner,
    context: ShellContext | None = None,
) -> str:
    """
    Scan one WORD token.

    A word may contain:

        bare text
        'single quoted text'   (never expanded)
        "double quoted text"   (expanded when context is given)
        escaped characters
        $VAR / ${VAR} / $?     (expanded when context is given)

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
                _scan_double_quoted(scanner, context)
            )
            continue

        # Backslash
        if ch == "\\":
            pieces.append(
                _scan_escape(scanner)
            )
            continue

        # Variable expansion (unquoted)
        if ch == "$" and context is not None:
            pieces.append(
                _scan_variable(scanner, context)
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


def _scan_double_quoted(
    scanner: _Scanner,
    context: ShellContext | None = None,
) -> str:
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

        # Variable expansion inside double quotes
        if ch == "$" and context is not None:
            chars.append(
                _scan_variable(scanner, context)
            )
            continue

        # Backslash
        if ch == "\\":
            nxt = scanner.peek()

            if nxt in ('"', "\\", "$"):
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
