
def cmd_help(args):
    print("""
Midnight Terminal HELP CENTER

ALIAS          Create or list aliases.  alias <name> = <command>
UNALIAS        Remove an alias.
AI             Ask an AI model a question.
CAT            Display file contents.   cat <file>
CD <path>      Change directory.
CLS / CLEAR    Clear the screen.
CP             Copy files and directories.  cp SOURCE DEST
CRT            Create files and directories.  crt <name> [dir] [-p]
DATE           Display the current date and time.
ECHO <text>    Print or write text.
EXIT           Exit the terminal.
FIND <name>    Search files/folders recursively from the current directory.
GREP           Search text inside files or command output.
HEAD           Display the first lines of input or files.
HELP           Show this help.
HOST           Display the hostname.
HWINFO         Display hardware information.
LS             List directory.  ls -a  ls -h  ls -ah
MKDIR <name>   Create a directory.
MTE <file>     Open the Midnight Text Editor.
MV             Move files and directories.  mv [-fiv] SOURCE DEST
PWD            Display the current directory.
REM <old> <new> Rename a file or directory.
RM <target>    Delete file/folder (asks confirmation).
RM -rf <t>     Force delete.
STAT           Display file or directory information.
TAIL           Display the last lines of input or files.
TREE           Display a directory tree.  tree -a -d -h -L <depth>
TRM            Clear and refresh the terminal.
WHICH          Locate an executable on PATH.
WHOAMI         Display the current username.
""")
