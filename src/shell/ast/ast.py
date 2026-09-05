"""
ast.py

Abstract Syntax Tree node definitions for the shell grammar.

Grammar (informal):

    pipeline    := command (PIPE command)*
    command     := WORD (WORD | redirection)*
    redirection := (GT | APPEND | LT) WORD

Design notes:
- These are pure data containers (no behavior). The parser constructs
  them; the executor traverses them. This keeps the AST reusable and
  trivially testable in isolation from parsing/execution logic.
- `Pipeline.commands` holds `Command` objects only, in left-to-right
  pipeline order. Each `Command` carries its own `redirections` list
  (a command can have zero or more redirections attached to it, e.g.
  `sort < in.txt > out.txt`). This matches conventional shell grammar,
  where redirections bind to the command they appear alongside rather
  than existing as free-floating pipeline elements.
- Frozen dataclasses are intentionally NOT used: nothing in the spec
  requires immutability, and mutability keeps future extension (e.g.
  attaching resolved env vars during execution) simple without needing
  to reconstruct nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Redirection:
    """
    A single I/O redirection attached to a command.

    type   : one of '>', '>>', '<'
    target : the filename/path operand (already unquoted by the lexer)
    """

    type: str
    target: str

    def __post_init__(self) -> None:
        valid_types = (">", ">>", "<")
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid redirection type {self.type!r}; expected one of {valid_types}"
            )


@dataclass
class Command:
    """
    A single command invocation: a name plus its positional arguments,
    plus any redirections attached to it.

    name          : the command/program name (first word)
    args          : positional arguments (strings, already unquoted/
                    unescaped by the lexer)
    redirections  : zero or more Redirection nodes attached to this
                    command (e.g. `grep err < in.txt > out.txt`)
    """

    name: str
    args: list[str] = field(default_factory=list)
    redirections: list[Redirection] = field(default_factory=list)


@dataclass
class Pipeline:
    """
    An ordered sequence of commands connected by pipes.

    commands : left-to-right list of Command nodes. A "plain" command
               with no pipe is simply a Pipeline with a single Command.

    Note: per the task spec's example --
        cat file.txt | grep ERR
        -> Pipeline(commands=[Command('cat', ['file.txt']), Command('grep', ['ERR'])])
    `commands` holds Command nodes; each Command carries its own
    `redirections` list rather than Redirection appearing as a sibling
    list element. This is equivalent in expressive power (every
    redirection is still represented, attached to the command it
    modifies) while matching how redirections are conventionally
    scoped in shell grammars.
    """

    commands: list[Command] = field(default_factory=list)


VALID_CONNECTORS = ("&&", "||", ";")


@dataclass
class Sequence:
    """
    One or more Pipelines connected by shell operators:

        pipeline ('&&' pipeline | '||' pipeline | ';' pipeline)*

    pipelines  : left-to-right list of Pipeline nodes.
    connectors : operator between consecutive pipelines, so
                 len(connectors) == len(pipelines) - 1.
                 connectors[i] connects pipelines[i] and pipelines[i+1].

    A "plain" single command line is a Sequence with one Pipeline and
    no connectors. The executor evaluates the sequence left-to-right:

        '&&' runs the next pipeline only when the previous one succeeded
        '||' runs the next pipeline only when the previous one failed
        ';'  always runs the next pipeline
    """

    pipelines: list[Pipeline] = field(default_factory=list)
    connectors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for connector in self.connectors:
            if connector not in VALID_CONNECTORS:
                raise ValueError(
                    f"Invalid connector {connector!r}; "
                    f"expected one of {VALID_CONNECTORS}"
                )

        if self.pipelines and (
            len(self.connectors) != len(self.pipelines) - 1
        ):
            raise ValueError(
                "Sequence connectors must link consecutive pipelines "
                f"(got {len(self.pipelines)} pipelines and "
                f"{len(self.connectors)} connectors)"
            )
