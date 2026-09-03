from __future__ import annotations

from prompt_toolkit import prompt as toolkit_prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from src.input.autocomplete import MidnightCompleter
from src.input.history import history


STYLE = Style.from_dict(
    {
        "username": "bold",
        "hostname": "bold",
        "path": "bold",
        "prompt": "bold",
    }
)


def prompt(
    *,
    username: str,
    hostname: str,
    path: str,
) -> str:
    message = HTML(
        "<username>{}</username>"
        "<prompt>@</prompt>"
        "<hostname>{}</hostname>"
        "<prompt>[</prompt>"
        "<path>{}</path>"
        "<prompt>]$ </prompt>"
        .format(username, hostname, path)
    )

    return toolkit_prompt(
        message,
        history=history,
        style=STYLE,
        cursor=CursorShape.BLINKING_BEAM,
        completer=MidnightCompleter(),
    )
