
def cmd_help(args):
    print("""
Midnight Terminal HELP CENTER

SHELL & SYSTEM
ALIAS          Create or manage command aliases.
CD <path>      Change the current directory.
CLS            Clear the terminal.
DATE           Display the current date and time.
ECHO <text>    Print text.
ENV            Display the shell environment.
ENFIX          Edit environment configuration.
HELP           Display this help.
HISTORY        Display previously executed commands.
HOST           Display the hostname.
KILL           Terminate a running process.
PS             Display running processes.
PWD            Display the current directory.
SET            Set an environment variable.
SOURCE         Reload the shell environment configuration.
TASK           Manage and inspect system tasks.
TIME           Measure command execution time.
TRM            Clear and refresh the terminal.
TYPE           Identify whether a command is an alias, builtin, or external command.
UNALIAS        Remove a command alias.
UNSET          Remove an environment variable.
WC             Count lines, words, and characters.
WHICH          Find the path of a command.
WHOAMI         Display the current username.

FILE MANAGEMENT
CAT            Display file contents.
CP             Copy files and directories.
CRT            Create files and directories.
DF             Display filesystem disk usage.
DU             Display file and directory disk usage.
FIND           Find files and directories.
GREP           Search text inside files or command output.
HEAD           Display the first lines of input or files.
LS             List files and directories.
MKDIR          Create a directory.
MTE            Open the Midnight Text Editor.
MV             Move files and directories.
REM            Rename files and directories.
RM             Remove files and directories.
STAT           Display file or directory information.
TAIL           Display the last lines of input or files.
TREE           Display a directory tree.

AI & HARDWARE
AI             Ask an AI model a question.
HWINFO         Display hardware information.

PIPELINES
Use | to connect commands.

Example:
echo "Hello world" | grep Hello

REDIRECTION
>              Redirect output to a file.
>>             Append output to a file.
<              Read input from a file.

Examples:
echo "Hello" > hello.txt
echo "World" >> hello.txt
cat < hello.txt

COMMAND OPERATORS
&&             Execute the next command if the previous succeeds.
||             Execute the next command if the previous fails.
;              Execute commands sequentially.

Examples:
python -c "print('ok')" && echo success
python -c "import sys; sys.exit(1)" || echo fallback
echo one; echo two

ALIASES
Create an alias:
alias ll = ls -la

List aliases:
alias

Remove an alias:
unalias ll

Aliases are stored persistently in:
src/cmd/rootfs/alias/aliases.dream

COMMAND INSPECTION
type ls
type python
type ll

The type command identifies built-in commands,
aliases, external commands, and unknown commands.

ENVIRONMENT
Configuration:
src/cmd/rootfs/env/envconfig.dream

Reload configuration:
source

HISTORY
History file:
src/history/.midnight_history

CONFIGURATION
Midnight Terminal supports configurable:
- Autocomplete
- History
- History size
- Multiline input
- Cursor style
- Shell environment
- Aliases

For detailed command information, use:
help
""")
