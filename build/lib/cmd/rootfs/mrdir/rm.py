import shutil

from src.shell.context.context import ShellContext


def cmd_rm(args: list[str], context: ShellContext) -> str:
    if not args:
        return ""

    force = False
    targets: list[str] = []

    for arg in args:
        if arg in ("-rf", "-fr", "-r", "-f"):
            force = True
        else:
            targets.append(arg)

    output: list[str] = []

    for target in targets:
        path = context.resolve_path(target)

        if not path.exists():
            output.append(f"Not found: {path}")
            continue

        if not force:
            context.stdout.write(f"Delete {path}? (y/n): ")
            context.stdout.flush()
            answer = context.stdin.readline().strip()
            if answer.lower() != "y":
                continue

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            output.append(f"Removed: {path}")
        except OSError as exc:
            output.append(f"Failed: {exc}")

    return "\n".join(output)
