from src.shell.context.context import ShellContext


def man_cat() -> str:
    return """CAT(1)                   Midnight Terminal Manual                  CAT(1)

NAME

    cat - display file contents

SYNOPSIS

    cat <file>...

DESCRIPTION

    Reads and displays the contents of one or more files.

EXAMPLES

    cat file.txt
    cat file1.txt file2.txt

SEE ALSO

    echo(1), head(1), tail(1), type(1)

"""


def cmd_cat(args: list[str], context: ShellContext) -> str:
    if not args:
        return context.stdin.read()

    output: list[str] = []

    for arg in args:
        target = context.resolve_path(arg)

        if not target.exists() or not target.is_file():
            output.append(f"File not found: {arg}\n")
            continue

        try:
            output.append(
                target.read_text(encoding="utf-8", errors="ignore")
            )
        except OSError as exc:
            output.append(f"Cannot read file: '{arg}': ERROR: {exc}\n")

    return "".join(output)
