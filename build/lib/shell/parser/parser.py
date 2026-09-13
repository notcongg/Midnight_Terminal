"""
parser.py

Converts a flat list of Token objects (from lexer.py) into a Sequence AST
(from ast.py), using straightforward recursive-descent parsing.

Grammar implemented:

    sequence    := pipeline (('&&' | '||' | ';') pipeline)*
    pipeline    := command (PIPE command)*
    command     := WORD word_or_redir*
    word_or_redir := WORD | redirection
    redirection := (GT | APPEND | LT) WORD

Validation performed (raising ParserError with a clear message):
    - Empty input                              -> "Empty command"
    - Leading pipe            (`| ls`)         -> empty command before '|'
    - Trailing pipe           (`ls |`)         -> empty command after '|'
    - Consecutive pipes       (`ls | | grep x`)-> empty command between '|'
    - Redirection with no operand at all       (`echo >`, `cat <`)
    - Redirection immediately followed by
      another operator instead of a WORD       (`echo > | grep x`)
    - A command segment that contains only
      redirections and no actual command name  (`> out.txt` alone)
    - Leading/trailing/doubled connectors      (`&& ls`, `ls &&`,
                                                `ls && && ls`)
"""

from __future__ import annotations

from src.shell.ast.ast import Command, Pipeline, Redirection, Sequence
from src.shell.errors.errors import ParserError
from src.shell.lexer.lexer import Token, TokenType

_REDIRECT_TOKEN_TYPES = {
    TokenType.GT: ">",
    TokenType.APPEND: ">>",
    TokenType.LT: "<",
}

_CONNECTOR_TOKEN_TYPES = {
    TokenType.AND: "&&",
    TokenType.OR: "||",
    TokenType.SEMI: ";",
}


class _TokenStream:
    """Internal cursor-based helper walking the token list."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.length = len(tokens)
        self.i = 0

    def eof(self) -> bool:
        return self.i >= self.length

    def peek(self) -> Token | None:
        return None if self.eof() else self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.tokens[self.i]
        self.i += 1
        return tok


def parse(tokens: list[Token]) -> Sequence:
    """
    Parse a token list into a Sequence AST node (one or more
    Pipelines connected by '&&', '||' or ';').

    Raises ParserError on any syntactically invalid sequence, including
    (but not limited to) the required cases from the spec:
        | ls      -> empty command before pipe
        ls |     -> empty command after pipe
        echo >   -> missing redirection target
        cat <    -> missing redirection source
        ls &&    -> empty command after '&&'
    """
    if not tokens:
        raise ParserError("Empty command")

    stream = _TokenStream(tokens)

    pipelines: list[Pipeline] = []
    connectors: list[str] = []

    # A sequence is one or more pipe-delimited pipelines connected by
    # '&&', '||' or ';'. We split on connector tokens, validating that
    # no pipeline is empty (which covers leading/trailing/doubled
    # connectors uniformly).
    segment_tokens: list[Token] = []

    while not stream.eof():
        tok = stream.advance()

        if tok.type in _CONNECTOR_TOKEN_TYPES:
            if not segment_tokens:
                raise ParserError(
                    f"Syntax error: expected a command "
                    f"before '{tok.value}' (found empty command)"
                )

            pipelines.append(_parse_pipeline(segment_tokens))
            connectors.append(_CONNECTOR_TOKEN_TYPES[tok.type])
            segment_tokens = []
        else:
            segment_tokens.append(tok)

    if not segment_tokens:
        raise ParserError(
            f"Syntax error: expected a command "
            f"after '{connectors[-1]}' (found empty command)"
        )

    pipelines.append(_parse_pipeline(segment_tokens))

    return Sequence(pipelines=pipelines, connectors=connectors)


def _parse_pipeline(seg: list[Token]) -> Pipeline:
    """
    Parse one connector-delimited segment (a sequence of tokens
    containing no '&&'/'||'/';' tokens) into a single Pipeline node.
    """
    commands: list[Command] = []

    # A pipeline is one or more pipe-separated command segments. We
    # split on PIPE tokens, validating that no segment is empty (which
    # covers leading/trailing/consecutive pipes uniformly).
    stream = _TokenStream(seg)

    segment_tokens: list[Token] = []
    all_segments: list[list[Token]] = []

    while not stream.eof():
        tok = stream.advance()
        if tok.type is TokenType.PIPE:
            all_segments.append(segment_tokens)
            segment_tokens = []
        else:
            segment_tokens.append(tok)
    all_segments.append(segment_tokens)  # final (or only) segment

    total_segments = len(all_segments)
    for idx, seg in enumerate(all_segments):
        if not seg:
            if total_segments == 1:
                # Single empty segment with no pipes at all was already
                # caught by the `if not tokens` check above, but guard
                # defensively in case of whitespace-only edge cases.
                raise ParserError("Empty command")
            if idx == 0:
                raise ParserError(
                    "Syntax error: expected a command before '|' (found empty command)"
                )
            if idx == total_segments - 1:
                raise ParserError(
                    "Syntax error: expected a command after '|' (found empty command)"
                )
            raise ParserError(
                "Syntax error: expected a command between '|' and '|' "
                "(found empty command)"
            )
        commands.append(_parse_command_segment(seg))

    return Pipeline(commands=commands)


def _parse_command_segment(seg: list[Token]) -> Command:
    """
    Parse one pipe-delimited segment (a sequence of tokens containing no
    PIPE tokens) into a single Command node, including any redirections
    attached to it.
    """
    segment = _TokenStream(seg)

    name: str | None = None
    args: list[str] = []
    redirections: list[Redirection] = []

    while not segment.eof():
        tok = segment.advance()

        if tok.type is TokenType.WORD:
            if name is None:
                name = tok.value
            else:
                args.append(tok.value)
            continue

        if tok.type in _REDIRECT_TOKEN_TYPES:
            redir_symbol = _REDIRECT_TOKEN_TYPES[tok.type]
            target_tok = segment.peek()
            if target_tok is None:
                raise ParserError(
                    f"Syntax error: missing target after redirection '{redir_symbol}'"
                )
            if target_tok.type is not TokenType.WORD:
                raise ParserError(
                    f"Syntax error: expected a filename after '{redir_symbol}', "
                    f"found operator '{target_tok.value}'"
                )
            segment.advance()  # consume the target WORD token
            redirections.append(Redirection(type=redir_symbol, target=target_tok.value))
            continue

        # Defensive: PIPE cannot appear here because segments were split
        # on PIPE before this function is called.
        raise ParserError(f"Unexpected token '{tok.value}'")  # pragma: no cover

    if name is None:
        # The segment consisted entirely of redirections with no actual
        # command name, e.g. "> out.txt" on its own.
        raise ParserError("Syntax error: missing command name before redirection")

    return Command(name=name, args=args, redirections=redirections)
