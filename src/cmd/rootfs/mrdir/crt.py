from src.shell.context.context import ShellContext


def cmd_crt(args: list[str], context: ShellContext) -> str | None:
    if not args:
        return None

    create_path = False
    arguments: list[str] = []

    for arg in args:
        if arg == "-p":
            create_path = True
        else:
            arguments.append(arg)

    if not arguments:
        return None

    name = arguments[0]

    if len(arguments) == 1:
        target = context.resolve_path(name)
        parent = target.parent
    else:
        destination = context.resolve_path(arguments[1])

        if destination.exists() and not destination.is_dir():
            return f"Cannot create file: '{destination}' is not a directory"

        if not destination.exists():
            if not create_path:
                context.stdout.write(
                    f"Path '{destination}' does not exist. Create it? (y/n): "
                )
                context.stdout.flush()
                answer = context.stdin.readline().strip().lower()
                if answer != "y":
                    return None

            try:
                destination.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return f"Cannot create path '{destination}': {exc}"

        target = destination / name
        parent = target.parent

    try:
        parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            if target.is_file():
                return None
            return f"Cannot create file '{target}': path is a directory"

        target.touch()
    except OSError as exc:
        return f"Cannot create file '{target}': {exc}"

    return None
