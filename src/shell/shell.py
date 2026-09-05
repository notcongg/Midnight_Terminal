from __future__ import annotations

from src.cmd.rootfs.alias.alias import expand_alias
from src.shell.context.context import ShellContext
from src.shell.errors.errors import ShellError
from src.shell.executor.executor import execute
from src.shell.lexer.lexer import tokenize
from src.shell.parser.parser import parse


class Shell:
    def __init__(self, context: ShellContext | None = None) -> None:
        self.context = context or ShellContext()

    def execute_line(self, source: str) -> None:
        source = expand_alias(source, self.context)

        try:
            tokens = tokenize(source, self.context)
        except ShellError:
            # Syntax/lexing failure: record the failure status so
            # `echo $?` and error handling see it.
            self.context.last_exit_code = 1
            raise

        if not tokens:
            return

        try:
            sequence = parse(tokens)
        except ShellError:
            self.context.last_exit_code = 1
            raise

        execute(sequence, self.context)
