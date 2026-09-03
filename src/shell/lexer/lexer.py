"""
lexer.py

Converts a raw shell input string into a flat list of Token objects.

Explicitly implemented as a character-by-character state machine per the
architecture spec -- str.split() is never used. This is required because
str.split() cannot correctly handle quoted strings containing spaces,
escape sequences, or operators that are not surrounded by whitespace
(e.g. `echo hi>out.txt` must tokenize as ['echo', 'hi', '>', 'out.txt']
even with zero spaces around `>`).

Supported syntax:
- Whitespace-separated words.
- Single quotes ' ... ' : contents are taken completely literally (no
  escape processing inside single quotes -- this matches POSIX sh
  behavior, where backslash has no special meaning inside single
  quotes).
- Double quotes " ... " : contents are taken literally except that a
  backslash can still escape a double quote or another backslash
  (`"say \"hi\""` -> `say "hi"`). This mirrors common shell double-quote
  escaping without implementing full POSIX double-quote semantics
  (which also treats $ and ` specially -- out of scope here, as this
  shell has no variable/command substitution).
- Backslash escape (\\) outside quotes: escapes the next character
  literally, e.g. a backslash followed by a pipe character becomes the
  literal character `|` instead of the pipe operator, a backslash
  followed by a space becomes a literal space that does not split the
  token, etc.
- Operators: |, >, >>, < . These are recognized even when directly
  adjacent to a word with no surrounding whitespace, since operators
  always terminate the current word token.

Output tokens are plain, unquoted, unescaped strings tagged with a
TokenType so the parser can distinguish an operator token (e.g. the two
characters `>` `>`) from a word token that happens to contain the same
characters (e.g. a quoted argument `">"`).

Windows path note: because backslash is this shell's escape character
(as in POSIX sh), an unquoted Windows-style path typed with backslash
separators will have each backslash consumed as an escape character
rather than preserved literally -- this matches how bash/sh also treat
unquoted Windows-style paths, but it means Windows users should wrap
such a path in single quotes to get it verbatim, since single-quoted
content is never escape-processed (see _scan_single_quoted below).
Forward slashes are unaffected either way, since they carry no special
meaning to this lexer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from src.shell.errors.errors import LexerError


class TokenType(Enum):
    WORD = auto()  # command name or argument (already unquoted/unescaped)
    PIPE = auto()  # |
    GT = auto()  # >
    APPEND = auto()  # >>
    LT = auto()  # <


@dataclass
class Token:
    type: TokenType
    value: str
    position: int  # index into the original input where this token started

    def __repr__(self) -> str:  # pragma: no cover - debug convenience
        return f"Token({self.type.name}, {self.value!r}, pos={self.position})"


class _Scanner:
    """Internal cursor-based helper walking the raw input one char at a time."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.length = len(text)
        self.i = 0  # current index

    def eof(self) -> bool:
        return self.i >= self.length

    def peek(self) -> str | None:
        return None if self.eof() else self.text[self.i]

    def advance(self) -> str:
        ch = self.text[self.i]
        self.i += 1
        return ch


def tokenize(raw_input: str) -> list[Token]:
    """
    Tokenize a raw shell input string into a list of Token objects.

    Raises LexerError on unterminated quotes or a trailing (dangling)
    escape character.
    """
    scanner = _Scanner(raw_input)
    tokens: list[Token] = []

    while True:
        _skip_unquoted_whitespace(scanner)
        if scanner.eof():
            break

        start_pos = scanner.i
        ch = scanner.peek()

        if ch == "|":
            scanner.advance()
            tokens.append(Token(TokenType.PIPE, "|", start_pos))
            continue

        if ch == "<":
            scanner.advance()
            tokens.append(Token(TokenType.LT, "<", start_pos))
            continue

        if ch == ">":
            scanner.advance()
            if scanner.peek() == ">":
                scanner.advance()
                tokens.append(Token(TokenType.APPEND, ">>", start_pos))
            else:
                tokens.append(Token(TokenType.GT, ">", start_pos))
            continue

        # Otherwise: this begins a WORD token (possibly containing quoted
        # segments and/or escapes glued together, e.g. foo"bar baz"qux).
        word_value = _scan_word(scanner)
        tokens.append(Token(TokenType.WORD, word_value, start_pos))

    return tokens


def _skip_unquoted_whitespace(scanner: _Scanner) -> None:
    while not scanner.eof() and scanner.peek() in (" ", "\t", "\n", "\r"):
        scanner.advance()


def _is_word_terminator(ch: str | None) -> bool:
    """Characters that end a WORD token when encountered unquoted/unescaped."""
    return ch is None or ch in (" ", "\t", "\n", "\r", "|", ">", "<")


def _scan_word(scanner: _Scanner) -> str:
    """
    Scans one WORD token starting at the current position. A single WORD
    may be composed of multiple adjacent pieces: bare characters, a
    single-quoted segment, a double-quoted segment, and/or escaped
    characters -- all concatenated with quotes stripped and escapes
    resolved. Scanning stops at unescaped whitespace or an unescaped
    operator character.
    """
    pieces: list[str] = []

    while not scanner.eof():
        ch = scanner.peek()

        if ch == "'":
            pieces.append(_scan_single_quoted(scanner))
            continue

        if ch == '"':
            pieces.append(_scan_double_quoted(scanner))
            continue

        if ch == "\\":
            pieces.append(_scan_escape(scanner))
            continue

        if _is_word_terminator(ch):
            break

        pieces.append(scanner.advance())

    return "".join(pieces)


def _scan_single_quoted(scanner: _Scanner) -> str:
    """
    Consumes a ' ... ' segment. Everything inside is completely literal
    (no escape processing at all inside single quotes, matching POSIX
    sh). Raises LexerError if the closing quote is never found.
    """
    open_pos = scanner.i
    scanner.advance()  # consume opening '
    chars: list[str] = []
    while True:
        if scanner.eof():
            raise LexerError("Unterminated single quote", position=open_pos)
        ch = scanner.advance()
        if ch == "'":
            return "".join(chars)
        chars.append(ch)


def _scan_double_quoted(scanner: _Scanner) -> str:
    """
    Consumes a " ... " segment. Backslash retains special meaning only
    before a double quote or another backslash (\" -> ", \\ -> \\);
    any other backslash is kept literally along with the following
    character, since this shell has no variable/command substitution
    that would otherwise need escaping inside double quotes. Raises
    LexerError if the closing quote is never found.
    """
    open_pos = scanner.i
    scanner.advance()  # consume opening "
    chars: list[str] = []
    while True:
        if scanner.eof():
            raise LexerError("Unterminated double quote", position=open_pos)
        ch = scanner.advance()
        if ch == '"':
            return "".join(chars)
        if ch == "\\":
            nxt = scanner.peek()
            if nxt in ('"', "\\"):
                chars.append(scanner.advance())
            else:
                # Not a recognized double-quote escape: keep the
                # backslash literally.
                chars.append(ch)
            continue
        chars.append(ch)


def _scan_escape(scanner: _Scanner) -> str:
    """
    Consumes a backslash-escape outside of quotes: the backslash is
    dropped and the following character is taken completely literally
    (so a backslash followed by a pipe becomes a literal '|' character,
    a backslash followed by a space becomes a literal space that does
    not terminate the word, a backslash followed by another backslash
    becomes a literal single backslash). Raises LexerError if the
    backslash is the last character of the input.
    """
    escape_pos = scanner.i
    scanner.advance()  # consume backslash
    if scanner.eof():
        raise LexerError(
            "Dangling escape character '\\' at end of input", position=escape_pos
        )
    return scanner.advance()
