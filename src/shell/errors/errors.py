"""
errors.py

Custom exception hierarchy for the shell parsing/execution pipeline.

All exceptions in this module are designed to carry user-readable messages.
The main REPL loop should catch ShellError (or its subclasses) and print
`str(exc)` directly to the user WITHOUT printing a Python traceback. Raw
Python tracebacks must never leak to the user for ordinary syntax/runtime
shell errors -- only truly unexpected internal bugs should ever surface a
traceback, and that is a decision made by the integration layer, not by
these classes.
"""

from __future__ import annotations


class ShellError(Exception):
    """
    Base class for all shell-related errors.

    Every subclass is guaranteed to produce a clean, user-readable message
    via str(exc). Callers (e.g. the REPL loop) should catch ShellError at
    the top level to guarantee no raw traceback is ever shown to the user
    during normal operation.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class LexerError(ShellError):
    """
    Raised when the lexer cannot tokenize the raw input string.

    Examples: unterminated quotes, dangling escape character at end of
    input, or other malformed character sequences.
    """

    def __init__(self, message: str, position: int | None = None) -> None:
        self.position = position
        if position is not None:
            message = f"{message} (at position {position})"
        super().__init__(message)


class ParserError(ShellError):
    """
    Raised when the token stream does not form a valid command sequence.

    Examples: leading/trailing pipe (`| ls`, `ls |`), missing redirection
    target (`echo >`), missing redirection source (`cat <`).
    """

    def __init__(self, message: str, token_index: int | None = None) -> None:
        self.token_index = token_index
        super().__init__(message)


class ExecutionError(ShellError):
    """
    Raised when a parsed, valid AST fails during execution.

    Examples: unknown command name (not found in the existing registry),
    a command callable raising an exception, or a redirection target that
    cannot be opened/written.
    """

    def __init__(self, message: str, command_name: str | None = None) -> None:
        self.command_name = command_name
        super().__init__(message)
