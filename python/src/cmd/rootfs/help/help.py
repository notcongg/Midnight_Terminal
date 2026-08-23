def cmd_help(args):
    print("""
MoonLight Terminal [V 0.001] HELP CENTER

CLS            Clears the screen.
CD <path>      Change directory.
LS             List directory.
LS -a          Show hidden files.
LS -h          Human readable size.
LS -ah         Combine both.

WHERE <name>   Search file/folder recursively.
ECHO <text>    Print text OR read file content if path exists.

TRM            Reload terminal UI (restart header).

MKDIR <name>   Create folder or file (auto .txt if file-like).

EDIT <file>    Open simple editor (Ctrl+S to save).

RM <target>    Delete file/folder (asks confirmation).
RM -rf <t>     Force delete without mercy.

EXIT           Exit terminal.
NOVACORE       Show system core.
HELP           Show commands.
""")
