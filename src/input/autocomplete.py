from __future__ import annotations

from collections.abc import Iterable

from prompt_toolkit.completion import Completer, Completion

from src.cmd.utils.registry import COMMANDS


class MidnightCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Chỉ autocomplete command đầu tiên.
        if " " in text or "\t" in text:
            return

        current = text.lower()

        if not current:
            return

        for command in COMMANDS:
            if command.lower().startswith(current):
                yield Completion(
                    command,
                    start_position=-len(text),
                )
