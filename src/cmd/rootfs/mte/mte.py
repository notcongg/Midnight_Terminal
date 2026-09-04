from __future__ import annotations

from pathlib import Path

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import (
    BufferControl,
    FormattedTextControl,
)
from prompt_toolkit.styles import Style

from src.shell.context.context import ShellContext


# ============================================================
# FILE IO
# ============================================================

def _read_file(path: Path) -> str:
    if not path.exists():
        return ""

    if not path.is_file():
        raise IsADirectoryError(
            f"mte: '{path}' is a directory"
        )

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def _write_file(path: Path, content: str) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


# ============================================================
# TITLE BAR
# ============================================================

def _title_bar(
    path: Path,
    modified: bool,
) -> FormattedText:

    filename = path.name or "New Buffer"
    modified_text = "Modified" if modified else ""

    return FormattedText(
        [
            (
                "class:title",
                f" MTE 1.0"
                f"                    "
                f"{filename}"
                f"                    "
                f"{modified_text}",
            ),
        ]
    )


# ============================================================
# STATUS BAR
# ============================================================

def _status_bar(
    buffer: Buffer,
    message: str,
) -> FormattedText:

    document = buffer.document

    line = document.cursor_position_row + 1
    column = document.cursor_position_col + 1

    if message:
        text = message
    else:
        text = f"Line {line}, Column {column}"

    return FormattedText(
        [
            (
                "class:status",
                f" {text}",
            ),
        ]
    )


# ============================================================
# SHORTCUT HELPER
#
# Shortcut:
#   ^X
#
# Help text:
#   Exit
# ============================================================

def _shortcut(key: str, text: str) -> list[tuple[str, str]]:
    return [
        (
            "class:shortcut",
            key,
        ),
        (
            "class:help",
            text,
        ),
    ]


# ============================================================
# HELP LINE 1
# ============================================================

def _help_line_1() -> FormattedText:

    fragments: list[tuple[str, str]] = []

    fragments.extend(
        _shortcut("^G", " Help     ")
    )

    fragments.extend(
        _shortcut("^O", " Write Out     ")
    )

    fragments.extend(
        _shortcut("^W", " Where Is     ")
    )

    fragments.extend(
        _shortcut("^K", " Cut Text     ")
    )

    fragments.extend(
        _shortcut("^T", " Execute")
    )

    return FormattedText(fragments)


# ============================================================
# HELP LINE 2
# ============================================================

def _help_line_2() -> FormattedText:

    fragments: list[tuple[str, str]] = []

    fragments.extend(
        _shortcut("^X", " Exit     ")
    )

    fragments.extend(
        _shortcut("^R", " Read File     ")
    )

    fragments.extend(
        _shortcut("^\\", " Replace     ")
    )

    fragments.extend(
        _shortcut("^U", " Paste     ")
    )

    fragments.extend(
        _shortcut("^C", " Cur Pos")
    )

    return FormattedText(fragments)


# ============================================================
# EXIT PROMPT
# ============================================================

def _exit_prompt() -> FormattedText:
    return FormattedText(
        [
            (
                "class:status",
                " Save modified buffer?  ",
            ),
            (
                "class:shortcut",
                "Y",
            ),
            (
                "class:status",
                " Yes   ",
            ),
            (
                "class:shortcut",
                "N",
            ),
            (
                "class:status",
                " No   ",
            ),
            (
                "class:shortcut",
                "C",
            ),
            (
                "class:status",
                " Cancel",
            ),
        ]
    )


# ============================================================
# EDITOR
# ============================================================

def _run_editor(path: Path) -> bool:

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    try:
        content = _read_file(path)

    except (OSError, UnicodeError) as exc:
        print(exc)
        return False

    # --------------------------------------------------------
    # Buffer
    # --------------------------------------------------------

    buffer = Buffer(
        multiline=True,
        document=Document(
            text=content,
            cursor_position=0,
        ),
    )

    modified = False
    confirm_exit = False
    status_message = ""

    # --------------------------------------------------------
    # Key bindings
    # --------------------------------------------------------

    kb = KeyBindings()

    # ========================================================
    # CTRL + O
    # WRITE OUT
    # ========================================================

    @kb.add("c-o", eager=True)
    def write_out(event) -> None:
        nonlocal modified
        nonlocal status_message

        try:
            _write_file(
                path,
                buffer.text,
            )

            modified = False
            status_message = "File written"

        except OSError as exc:
            status_message = (
                f"Error writing file: {exc}"
            )

        event.app.invalidate()

    # ========================================================
    # CTRL + S
    # SAVE
    # ========================================================

    @kb.add("c-s", eager=True)
    def save(event) -> None:
        nonlocal modified
        nonlocal status_message

        try:
            _write_file(
                path,
                buffer.text,
            )

            modified = False
            status_message = "File written"

        except OSError as exc:
            status_message = (
                f"Error writing file: {exc}"
            )

        event.app.invalidate()

    # ========================================================
    # CTRL + X
    # EXIT
    # ========================================================

    @kb.add("c-x", eager=True)
    def exit_editor(event) -> None:
        nonlocal confirm_exit

        if modified:
            confirm_exit = True
            event.app.invalidate()
            return

        event.app.exit(
            result=True
        )

    # ========================================================
    # CTRL + Q
    # FORCE EXIT
    # ========================================================

    @kb.add("c-q", eager=True)
    def force_exit(event) -> None:
        event.app.exit(
            result=False
        )

    # ========================================================
    # Y
    # SAVE + EXIT
    # ========================================================

    @kb.add("y", eager=True)
    def confirm_yes(event) -> None:
        nonlocal modified
        nonlocal confirm_exit
        nonlocal status_message

        if not confirm_exit:
            return

        try:
            _write_file(
                path,
                buffer.text,
            )

            modified = False
            confirm_exit = False

            event.app.exit(
                result=True
            )

        except OSError as exc:
            status_message = (
                f"Error writing file: {exc}"
            )

            event.app.invalidate()

    # ========================================================
    # N
    # DISCARD + EXIT
    # ========================================================

    @kb.add("n", eager=True)
    def confirm_no(event) -> None:
        nonlocal confirm_exit

        if not confirm_exit:
            return

        confirm_exit = False

        event.app.exit(
            result=True
        )

    # ========================================================
    # C
    # CANCEL EXIT
    # ========================================================

    @kb.add("c", eager=True)
    def confirm_cancel(event) -> None:
        nonlocal confirm_exit

        if not confirm_exit:
            return

        confirm_exit = False

        event.app.invalidate()

    # ========================================================
    # CTRL + C
    # CURSOR POSITION
    # ========================================================

    @kb.add("c-c", eager=True)
    def cursor_position(event) -> None:
        nonlocal status_message

        document = buffer.document

        line = document.cursor_position_row + 1
        column = document.cursor_position_col + 1

        status_message = (
            f"Line {line}, Column {column}"
        )

        event.app.invalidate()

    # ========================================================
    # CTRL + G
    # HELP
    # ========================================================

    @kb.add("c-g", eager=True)
    def help_screen(event) -> None:
        nonlocal status_message

        status_message = (
            "MTE: Ctrl+O Save | "
            "Ctrl+X Exit | "
            "Ctrl+S Save | "
            "Ctrl+Q Force Exit"
        )

        event.app.invalidate()

    # ========================================================
    # TRACK MODIFICATIONS
    # ========================================================

    def on_text_changed(_) -> None:
        nonlocal modified
        nonlocal status_message

        modified = True
        status_message = ""

    buffer.on_text_changed += on_text_changed

    # ========================================================
    # EDITOR WINDOW
    # ========================================================

    editor = Window(
        content=BufferControl(
            buffer=buffer,
        ),
        wrap_lines=True,
    )

    # ========================================================
    # TITLE BAR
    #
    # FULL WIDTH:
    #
    # ████████████████████████████████████████████████████████
    #  MTE 1.0                    test.txt
    # ████████████████████████████████████████████████████████
    #
    # White background / black text
    # ========================================================

    title = Window(
        content=FormattedTextControl(
            lambda: _title_bar(
                path,
                modified,
            )
        ),
        height=1,
        style="class:title",
    )

    # ========================================================
    # STATUS BAR
    # ========================================================

    status = Window(
        content=FormattedTextControl(
            lambda: (
                _exit_prompt()
                if confirm_exit
                else _status_bar(
                    buffer,
                    status_message,
                )
            )
        ),
        height=1,
        style="class:status",
    )

    # ========================================================
    # HELP LINE 1
    #
    # ^G = WHITE BG + BLACK TEXT
    # Help = BLACK BG + WHITE TEXT
    # ========================================================

    help_bar = Window(
        content=FormattedTextControl(
            _help_line_1,
        ),
        height=1,
        style="class:help",
    )

    # ========================================================
    # HELP LINE 2
    # ========================================================

    help_bar_2 = Window(
        content=FormattedTextControl(
            _help_line_2,
        ),
        height=1,
        style="class:help",
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    root = HSplit(
        [
            title,
            editor,
            status,
            help_bar,
            help_bar_2,
        ]
    )

    # ========================================================
    # STYLE
    # ========================================================

    style = Style.from_dict(
        {
            # ------------------------------------------------
            # Default editor
            # ------------------------------------------------

            "": (
                "bg:#000000 "
                "#ffffff"
            ),

            # ------------------------------------------------
            # Header
            #
            # FULL WIDTH WHITE
            # BLACK TEXT
            # ------------------------------------------------

            "title": (
                "bg:#ffffff "
                "#000000 "
                "bold"
            ),

            # ------------------------------------------------
            # Status
            #
            # BLACK BG
            # WHITE TEXT
            # ------------------------------------------------

            "status": (
                "bg:#000000 "
                "#ffffff"
            ),

            # ------------------------------------------------
            # Footer container
            #
            # BLACK BG
            # WHITE TEXT
            # ------------------------------------------------

            "help": (
                "bg:#000000 "
                "#ffffff"
            ),

            # ------------------------------------------------
            # Shortcut
            #
            # ONLY ^G / ^O / ^X / ...
            #
            # WHITE BG
            # BLACK TEXT
            # ------------------------------------------------

            "shortcut": (
                "bg:#ffffff "
                "#000000 "
                "bold"
            ),
        }
    )

    # ========================================================
    # APPLICATION
    # ========================================================

    app = Application(
        layout=Layout(
            root,
            focused_element=editor,
        ),
        key_bindings=kb,
        full_screen=True,
        mouse_support=False,
        style=style,
    )

    # ========================================================
    # RUN
    # ========================================================

    try:
        result = app.run()

    except KeyboardInterrupt:
        return False

    return result is not False


# ============================================================
# COMMAND
# ============================================================

def cmd_mte(
    args: list[str],
    context: ShellContext,
) -> str | None:

    if not args:
        return "mte: missing file operand"

    path = context.resolve_path(
        args[0]
    )

    try:
        _run_editor(path)

    except KeyboardInterrupt:
        pass

    return None
