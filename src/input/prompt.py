from __future__ import annotations

from textwrap import dedent

from prompt_toolkit import prompt as toolkit_prompt
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from src.cmd.rootfs.env.env import ENV
from src.input.autocomplete import MidnightCompleter
from src.input.history import get_history


# ============================================================
# STYLE
# ============================================================

STYLE = Style.from_dict(
    {
        "username": "bold",
        "hostname": "bold",
        "path": "bold",
        "prompt": "bold",
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


# ============================================================
# PROMPT
# ============================================================

def _prompt_message(
    username: str,
    hostname: str,
    path: str,
) -> HTML:
    template = _get_env("UP1")

    if not template:
        return HTML(
            (
                "<username>"
                f"╭─[{username}@{hostname}]-[{path}]"
                "</username>\n"
                "<prompt>╰─$ </prompt>"
            )
        )

    lines = template.splitlines()

    # --------------------------------------------------------
    # Remove multiline wrapper
    # --------------------------------------------------------

    if lines and lines[0].strip() == "[":
        lines = lines[1:]

    if lines and lines[-1].strip() == "]":
        lines = lines[:-1]

    # --------------------------------------------------------
    # Remove nested environment assignments
    # --------------------------------------------------------

    lines = [
        line
        for line in lines
        if not line.strip().startswith("set ")
    ]

    # --------------------------------------------------------
    # Remove quote wrapper
    # --------------------------------------------------------

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
) -> str:
    lines = [first_line]

    while True:
        line = toolkit_prompt(
            _continuation_prompt(),
            history=None,
            style=STYLE,
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

    line = toolkit_prompt(
        message,
        history=history,
        style=STYLE,
        cursor=_cursor_shape(),
        completer=MidnightCompleter(),
        key_bindings=_ctrl_c_bindings(),
    )

    if _is_multiline_start(line):
        return _read_multiline(
            line,
            history,
        )

    return line
