"""
context.py

Defines ShellContext: a container for all per-session shell state.

Deliberately instantiated once per shell session (e.g. once in the REPL's
main() / __main__ entry point) and threaded explicitly through the
executor -- there is NO module-level/global instance anywhere in this
package.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


@dataclass
class ShellContext:
    """
    Holds all mutable state for a single shell session.

    cwd defaults to the user home directory, matching the original
    Midnight Terminal prompt (not the process working directory).
    """

    cwd: str = field(default_factory=lambda: str(Path.home()))
    environment: dict[str, str] = field(default_factory=lambda: dict(os.environ))
    aliases: dict[str, str] = field(default_factory=dict)
    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    stdout: TextIO = field(default_factory=lambda: sys.stdout)
    stderr: TextIO = field(default_factory=lambda: sys.stderr)
    exit_requested: bool = False

    def resolve_path(self, value: str) -> Path:
        target = Path(value).expanduser()
        if not target.is_absolute():
            target = Path(self.cwd) / target
        return target

    def clone_streams_reset(self) -> "ShellContext":
        """
        Shallow copy for per-command stdin/stdout redirection.
        cwd/environment/aliases/exit_requested are copied so the caller
        can copy session-visible mutations back after the command runs.
        environment and aliases are shared by reference (session tables).
        """
        return ShellContext(
            cwd=self.cwd,
            environment=self.environment,
            aliases=self.aliases,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            exit_requested=self.exit_requested,
        )
