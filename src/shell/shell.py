from __future__ import annotations

from src.cmd.rootfs.alias.alias import expand_alias
from src.shell.context.context import ShellContext
from src.shell.executor.executor import execute
from src.shell.lexer.lexer import tokenize
from src.shell.parser.parser import parse


class Shell:
    def __init__(self, context: ShellContext | None = None) -> None:
        self.context = context or ShellContext()

    def execute_line(self, source: str) -> None:
        source = expand_alias(source, self.context)
        tokens = tokenize(source)

        if not tokens:
            return

        pipeline = parse(tokens)
        execute(pipeline, self.context)
