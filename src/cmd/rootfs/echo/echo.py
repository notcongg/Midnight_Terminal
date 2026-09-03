from src.shell.context.context import ShellContext


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
