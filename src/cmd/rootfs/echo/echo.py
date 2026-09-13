from src.shell.context.context import ShellContext


def man_echo() -> str:
    return """ECHO(1)                  Midnight Terminal Manual                 ECHO(1)

NAME

    echo - print text or file contents

SYNOPSIS

    echo <text>
    echo <file_path>

DESCRIPTION

    Prints text to the terminal. If the text is a path to an
    existing file, the file contents are printed instead.

EXAMPLES

    echo Hello World
    echo ~/notes.txt

SEE ALSO

    cat(1), type(1)

"""


def cmd_echo(args: list[str], context: ShellContext) -> str:
    if not args:
        return ""

    content = " ".join(args)
    target = context.resolve_path(content)

    if target.exists() and target.is_file():
        try:
            return target.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return f"Cannot read file: {exc}"

    return content
