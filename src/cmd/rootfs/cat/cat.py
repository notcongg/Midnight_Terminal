from src.cmd.rootfs.mte.mte import _resolve_config_path
from src.shell.context.context import ShellContext


def man_cat() -> str:
    return """CAT(1)                   Midnight Terminal Manual                  CAT(1)

NAME

    cat - display file contents

SYNOPSIS

    cat <file>...
    cat ~/.midconf
    cat ~/.midhsty

DESCRIPTION

    Reads and displays the contents of one or more files.

    The project shortcuts ~/.midconf and ~/.midhsty resolve to the
    canonical src/.midconf and src/.midhsty files.

EXAMPLES

    cat file.txt
    cat file1.txt file2.txt
    cat ~/.midconf

SEE ALSO

    echo(1), head(1), tail(1), type(1)

"""


def cmd_cat(args: list[str], context: ShellContext) -> str:
    if not args:
        return context.stdin.read()

    output: list[str] = []

    for arg in args:
        target, _ = _resolve_config_path(
            context,
            arg,
        )

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
