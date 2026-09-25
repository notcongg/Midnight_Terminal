from __future__ import annotations

from pathlib import Path

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
<<<<<<< HEAD
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
=======
from prompt_toolkit.layout.controls import (
    BufferControl,
    FormattedTextControl,
)
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

from src.shell.context.context import ShellContext
<<<<<<< HEAD
from src.sot import MIDCONF_PATH, MIDHSTY_PATH


# ============================================================
=======
from src.utils.paths import midconf_path, midhsty_path


# ============================================================
# COMMENT-ONLY SYNTAX HIGHLIGHTING
# ============================================================

class CommentLexer(Lexer):
    """
    Highlight only:
        // single-line comments
        /* multi-line comments */

    Everything else remains unstyled.
    """

    def lex_document(self, document: Document):
        lines = document.lines

        styled_lines: list[list[tuple[str, str]]] = []
        in_multiline = False

        for line in lines:
            fragments: list[tuple[str, str]] = []
            i = 0
            normal_start = 0

            while i < len(line):
                # ====================================================
                # Inside /* ... */ comment
                # ====================================================
                if in_multiline:
                    end = line.find("*/", i)

                    if end == -1:
                        if normal_start < i:
                            fragments.append(
                                ("", line[normal_start:i])
                            )

                        fragments.append(
                            ("class:comment", line[i:])
                        )

                        i = len(line)
                        normal_start = i
                        break

                    if normal_start < i:
                        fragments.append(
                            ("", line[normal_start:i])
                        )

                    comment_end = end + 2

                    fragments.append(
                        (
                            "class:comment",
                            line[i:comment_end],
                        )
                    )

                    i = comment_end
                    normal_start = i
                    in_multiline = False
                    continue

                # ====================================================
                # Find next comment
                # ====================================================
                slash_comment = line.find("//", i)
                block_comment = line.find("/*", i)

                positions = [
                    pos
                    for pos in (
                        slash_comment,
                        block_comment,
                    )
                    if pos != -1
                ]

                # No more comments on this line.
                if not positions:
                    break

                comment_start = min(positions)

                # Keep text before comment unchanged.
                if comment_start > normal_start:
                    fragments.append(
                        (
                            "",
                            line[
                                normal_start:comment_start
                            ],
                        )
                    )

                # ====================================================
                # // single-line comment
                # ====================================================
                if (
                    slash_comment != -1
                    and slash_comment == comment_start
                    and (
                        block_comment == -1
                        or slash_comment < block_comment
                    )
                ):
                    fragments.append(
                        (
                            "class:comment",
                            line[slash_comment:],
                        )
                    )

                    i = len(line)
                    normal_start = i
                    break

                # ====================================================
                # /* multi-line comment
                # ====================================================
                fragments.append(
                    (
                        "class:comment",
                        line[comment_start:comment_start + 2],
                    )
                )

                i = comment_start + 2
                normal_start = i
                in_multiline = True

            # Remaining normal text.
            if normal_start < len(line):
                fragments.append(
                    (
                        "",
                        line[normal_start:],
                    )
                )

            if not fragments:
                fragments.append(("", ""))

            styled_lines.append(fragments)

        def get_line(lineno: int):
            if 0 <= lineno < len(styled_lines):
                return styled_lines[lineno]

            return [("", "")]

        return get_line


# ============================================================
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
# MANUAL
# ============================================================

def man_mte() -> str:
    return """MTE(1)                    Midnight Terminal Manual                   MTE(1)

NAME
    mte - Midnight Text Editor

SYNOPSIS
    mte <file>

DESCRIPTION
    Opens a full-screen text editor for the given file.

    The editor supports editing, saving, searching and quitting.

SHORTCUTS
    ^G      help
    ^O      save (write out)
    ^W      search
    ^X      exit

EXAMPLES
    mte notes.txt
    mte .midconf
    mte .midhsty

    mte ~/.midconf
    mte ~/.midhsty

SEE ALSO
    cat(1), echo(1), crt(1)
"""


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


def _write_file(
    path: Path,
    content: str,
) -> None:
<<<<<<< HEAD
=======
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
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
# ============================================================

def _shortcut(
    key: str,
    text: str,
) -> list[tuple[str, str]]:
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
# SYNTAX HIGHLIGHTING
# ============================================================

class MidnightLexer(Lexer):
    """
    Lightweight syntax highlighter for Midnight config files.

    Syntax:
        // single-line comment
        /* multi-line comment */
        "double quoted string"
        'single quoted string'

    Comments have precedence over strings.

    The lexer keeps track of multi-line comments between
    prompt_toolkit line calls.
    """

    def lex_document(self, document: Document):
        lines = document.lines

        def get_line(
            line_no: int,
        ) -> list[tuple[str, str]]:
            return self._highlight_document(
                lines,
                line_no,
            )

        return get_line

    @staticmethod
    def _highlight_document(
        lines: list[str],
        target_line: int,
    ) -> list[tuple[str, str]]:
        in_multiline_comment = False

        for line_no, line in enumerate(lines):
            fragments: list[tuple[str, str]] = []
            i = 0
            length = len(line)

            while i < length:
                # ------------------------------------------------
                # Already inside /* ... */
                # ------------------------------------------------
                if in_multiline_comment:
                    end = line.find(
                        "*/",
                        i,
                    )

                    if end == -1:
                        fragments.append(
                            (
                                "class:comment",
                                line[i:],
                            )
                        )
                        i = length
                        continue

                    fragments.append(
                        (
                            "class:comment",
                            line[i:end + 2],
                        )
                    )
                    i = end + 2
                    in_multiline_comment = False
                    continue

                # ------------------------------------------------
                # Single-line comment
                # ------------------------------------------------
                if line.startswith(
                    "//",
                    i,
                ):
                    fragments.append(
                        (
                            "class:comment",
                            line[i:],
                        )
                    )
                    i = length
                    continue

                # ------------------------------------------------
                # Multi-line comment
                # ------------------------------------------------
                if line.startswith(
                    "/*",
                    i,
                ):
                    end = line.find(
                        "*/",
                        i + 2,
                    )

                    if end == -1:
                        fragments.append(
                            (
                                "class:comment",
                                line[i:],
                            )
                        )
                        in_multiline_comment = True
                        i = length
                        continue

                    fragments.append(
                        (
                            "class:comment",
                            line[i:end + 2],
                        )
                    )
                    i = end + 2
                    continue

                # ------------------------------------------------
                # Double-quoted string
                # ------------------------------------------------
                if line[i] == '"':
                    start = i
                    i += 1

                    while i < length:
                        if line[i] == "\\":
                            i += 2
                            continue

                        if line[i] == '"':
                            i += 1
                            break

                        i += 1

                    fragments.append(
                        (
                            "class:double-string",
                            line[start:i],
                        )
                    )
                    continue

                # ------------------------------------------------
                # Single-quoted string
                # ------------------------------------------------
                if line[i] == "'":
                    start = i
                    i += 1

                    while i < length:
                        if line[i] == "\\":
                            i += 2
                            continue

                        if line[i] == "'":
                            i += 1
                            break

                        i += 1

                    fragments.append(
                        (
                            "class:single-string",
                            line[start:i],
                        )
                    )
                    continue

                # ------------------------------------------------
                # Normal text
                # ------------------------------------------------
                start = i

                while i < length:
                    if line.startswith(
                        "//",
                        i,
                    ):
                        break

                    if line.startswith(
                        "/*",
                        i,
                    ):
                        break

                    if line[i] in {
                        '"',
                        "'",
                    }:
                        break

                    i += 1

                if start != i:
                    fragments.append(
                        (
                            "",
                            line[start:i],
                        )
                    )

            if line_no == target_line:
                return fragments

        return []


# ============================================================
# EDITOR
# ============================================================

<<<<<<< HEAD
def _run_editor(
    path: Path,
) -> bool:
=======
def _run_editor(path: Path) -> bool:
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
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
        line = (
            document.cursor_position_row
            + 1
        )
        column = (
            document.cursor_position_col
            + 1
        )

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
<<<<<<< HEAD
            lexer=MidnightLexer(),
=======
            lexer=CommentLexer(),
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
        ),
        wrap_lines=True,
    )

    # ========================================================
    # TITLE BAR
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
<<<<<<< HEAD
            "":
=======
            "": (
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
                "bg:#000000 "
                "#ffffff",

            # ------------------------------------------------
            # Header
            # ------------------------------------------------
<<<<<<< HEAD
            "title":
=======
            "title": (
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
                "bg:#ffffff "
                "#000000 "
                "bold",

            # ------------------------------------------------
            # Status
            # ------------------------------------------------
<<<<<<< HEAD
            "status":
=======
            "status": (
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
                "bg:#000000 "
                "#ffffff",

            # ------------------------------------------------
            # Footer
            # ------------------------------------------------
<<<<<<< HEAD
            "help":
=======
            "help": (
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
                "bg:#000000 "
                "#ffffff",

            # ------------------------------------------------
            # Shortcut
            # ------------------------------------------------
<<<<<<< HEAD
            "shortcut":
                "bg:#ffffff "
                "#000000 "
                "bold",

            # ------------------------------------------------
            # Midnight syntax highlighting
            # ------------------------------------------------
            "comment":
                "#808080",

            "double-string":
                "#00ffff",

            "single-string":
                "#00ffff",
=======
            "shortcut": (
                "bg:#ffffff "
                "#000000 "
                "bold"
            ),

            # ------------------------------------------------
            # Comments
            # ------------------------------------------------
            "comment": (
                "fg:#808080"
            ),
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
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
# MIDNIGHT CONFIG PATHS
# ============================================================

<<<<<<< HEAD
=======
# ~/.midconf
# ~/.midhsty
#
# resolve to the platform-specific Midnight config directory:
#
# Windows:
#   %APPDATA%\Midnight\
#
# Linux:
#   ~/.config/Midnight/


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
def _resolve_config_path(
    context: ShellContext,
    value: str,
) -> tuple[Path, bool]:
    """
<<<<<<< HEAD
    Resolve Midnight config shortcuts.
=======
    Resolve config/history shortcuts.
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

    Returns:
        (path, is_home_shortcut)
    """
<<<<<<< HEAD
=======

>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)
    normalized = (
        value
        .strip()
        .replace("\\", "/")
        .rstrip("/")
    )

    if normalized in {
        "~/.midconf",
        "$HOME/.midconf",
    }:
<<<<<<< HEAD
        return MIDCONF_PATH, True
=======
        return midconf_path(), True
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

    if normalized in {
        "~/.midhsty",
        "$HOME/.midhsty",
    }:
<<<<<<< HEAD
        return MIDHSTY_PATH, True
=======
        return midhsty_path(), True
>>>>>>> b471ff9 (feat + fix: add sleep, true, false (feat) | fix: midnight terminal config, history , alias, pass path + fix ls into new ui)

    return context.resolve_path(value), False


def _resolve_editor_path(
    context: ShellContext,
    value: str,
) -> Path:
    path, _ = _resolve_config_path(
        context,
        value,
    )

    return path


# ============================================================
# COMMAND
# ============================================================

def cmd_mte(
    args: list[str],
    context: ShellContext,
) -> str | None:
    if not args:
        return "mte: missing file operand"

    path = _resolve_editor_path(
        context,
        args[0],
    )

    try:
        _run_editor(path)
    except KeyboardInterrupt:
        pass

    return None