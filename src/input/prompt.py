from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import (
    AutoSuggestFromHistory,
)

from src.cmd.rootfs.env.env import ENV
from src.cmd.rootfs.msup.msup import is_active
from src.input.autocomplete import MidnightCompleter
from src.input.history import get_history


# ============================================================
# STYLE
# ============================================================

STYLE = Style.from_dict(
    {
        "username": "#ffffff bold",
        "hostname": "#ffffff bold",
        "path": "#ffffff bold",
        "prompt": "#ffffff bold",
    }
)


# ============================================================
# ENV
# ============================================================

def _get_env(
    name: str,
    default: str = "",
) -> str:
    return ENV.get(name, default)


# ============================================================
# CURSOR
# ============================================================

def _cursor_shape() -> CursorShape:
    value = _get_env(
        "CURSOR",
        "CURSORSHAPE.BLINKING_BEAM",
    ).strip()

    shapes = {
        "CURSORSHAPE.BLINKING_BEAM":
            CursorShape.BLINKING_BEAM,

        "CURSORSHAPE.BEAM":
            CursorShape.BEAM,

        "CURSORSHAPE.BLINKING_UNDERLINE":
            CursorShape.BLINKING_UNDERLINE,

        "CURSORSHAPE.UNDERLINE":
            CursorShape.UNDERLINE,

        "CURSORSHAPE.BLINKING_BLOCK":
            CursorShape.BLINKING_BLOCK,

        "CURSORSHAPE.BLOCK":
            CursorShape.BLOCK,
    }

    return shapes.get(
        value,
        CursorShape.BLINKING_BEAM,
    )


def _auto_suggest() -> AutoSuggestFromHistory | None:
    """Return an auto-suggestion provider when enabled in .midconf."""

    if (
        ENV.get(
            "INPUT.SUGGESTIONS",
            "true",
        ).lower() == "true"
    ):
        return AutoSuggestFromHistory()

    return None


# ============================================================
# PROMPT
# ============================================================

def _prompt_message(
    username: str,
    hostname: str,
    path: str,
) -> HTML:
    msup_active = is_active()
    msup = "-[MSUP]" if msup_active else ""
    prompt_symbol = "#>" if msup_active else "$>"

    template = _get_env("UP1")

    if not template:
        return HTML(
            (
                "<username>"
                f"╭─[{username}@{hostname}]-[{path}]{msup}"
                "</username>\n"
                f"<prompt>╰─{prompt_symbol} </prompt>"
            )
        )

    lines = template.splitlines()

    if lines and lines[0].strip() == "[":
        lines = lines[1:]

    if lines and lines[-1].strip() == "]":
        lines = lines[:-1]

    lines = [
        line
        for line in lines
        if not line.strip().startswith("set ")
    ]

    if lines and lines[0].strip() == '"':
        lines = lines[1:]

    if lines and lines[-1].strip() == '"':
        lines = lines[:-1]

    template = "\n".join(lines).strip("\r\n")

    template = (
        template
        .replace("$NAME", username)
        .replace("$HOST", hostname)
        .replace("$PWD", path)
        .replace("$MSUP", msup)
        .replace("$PROMPT", prompt_symbol)
    )

    return HTML(template)


# ============================================================
# CONTINUATION PROMPT
# ============================================================

def _continuation_prompt() -> str:
    value = _get_env(
        "UP2",
        "> ",
    ).strip()

    if (
        len(value) >= 2
        and value[0] in {"'", '"'}
        and value[-1] == value[0]
    ):
        value = value[1:-1]

    return value


# ============================================================
# MULTILINE
# ============================================================

def _is_multiline_start(value: str) -> bool:
    return value.rstrip().endswith("=[")


def _is_multiline_end(value: str) -> bool:
    return value.strip() == "]"


# ============================================================
# CTRL+C
# ============================================================

def _ctrl_c_bindings() -> KeyBindings:
    bindings = KeyBindings()

    @bindings.add(
        "c-c",
        eager=True,
        record_in_macro=False,
    )
    def _handle_ctrl_c(event) -> None:
        """
        Show ^C at the current cursor position and terminate
        the current prompt with KeyboardInterrupt.
        The ^C is inserted into the prompt buffer first, so
        prompt_toolkit renders it directly after the prompt
        instead of printing it on a separate line.
        """

        event.current_buffer.insert_text("^C")

        event.app.exit(
            exception=KeyboardInterrupt()
        )

    return bindings


# ============================================================
# MULTILINE INPUT
# ============================================================

def _read_multiline(
    first_line: str,
    history,
    session: PromptSession,
) -> str:

    lines = [first_line]

    while True:
        line = session.prompt(
            _continuation_prompt(),
            history=None,
            cursor=_cursor_shape(),
            completer=MidnightCompleter(),
            key_bindings=_ctrl_c_bindings(),
        )

        lines.append(line)

        if _is_multiline_end(line):
            break

    result = "\n".join(lines)

    if history is not None:
        history.replace_last_string(
            first_line,
            result,
        )

    return result


# ============================================================
# PROMPT
# ============================================================

def prompt(
    *,
    username: str,
    hostname: str,
    path: str,
) -> str:

    message = _prompt_message(
        username,
        hostname,
        path,
    )

    history = get_history()

    session = PromptSession(
        style=STYLE,
        cursor=_cursor_shape(),
        history=history,
        auto_suggest=_auto_suggest(),
    )

    line = session.prompt(
        message,
        completer=MidnightCompleter(),
        key_bindings=_ctrl_c_bindings(),
        reserve_space_for_menu=0,
        complete_while_typing=False,
    )

    if _is_multiline_start(line):
        return _read_multiline(
            line,
            history,
            session,
        )

    return line