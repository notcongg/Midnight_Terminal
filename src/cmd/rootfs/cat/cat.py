from src.shell.context.context import ShellContext


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
