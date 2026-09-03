def cmd_help(args):
    print("""
Midnight Terminal HELP CENTER

ALIAS          Create or list aliases.  alias <name> = <command>
UNALIAS        Remove an alias.
CAT            Display file contents.   cat <file>
CD <path>      Change directory.
CLS / CLEAR    Clear the screen.
CRT            Create a file.           crt <name> [dir] [-p]
DATE           Display the current date and time.
ECHO <text>    Print text, or read file content if the path exists.
EXIT           Exit the terminal.
FIND <name>    Search files/folders recursively from the current directory.
HELP           Show this help.
HOSTNAME       Display the hostname.
HWINFO         Display hardware information.
LS             List directory.  ls -a  ls -h  ls -ah
MKDIR <name>   Create a directory.
MV             Move files and directories.  mv [-fiv] SOURCE DEST
PWD            Display the current directory.
REM <old> <new> Rename a file or directory.
RM <target>    Delete file/folder (asks confirmation).
RM -rf <t>     Force delete.
TREE           Display a directory tree.  tree -a -d -h -L <depth>
TRM            Reload the terminal banner.
WHICH          Locate an executable on PATH.
WHOAMI         Display the current username.
""")
