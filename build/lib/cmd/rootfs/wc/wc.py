from __future__ import annotations

from src.shell.context.context import ShellContext


def _human(value: int) -> str:
    units = ["", "k", "M", "G", "T", "P"]

    size = float(value)
    unit = 0

    while size >= 1000 and unit < len(units) - 1:
        size /= 1000
        unit += 1

    if unit == 0:
        return str(value)

    if size >= 100:
        number = f"{size:.0f}"
    elif size >= 10:
        number = f"{size:.1f}"
    else:
        number = f"{size:.2f}"

    number = number.rstrip("0").rstrip(".")

    return f"{number}{units[unit]}"


def _count(data: str) -> tuple[int, int, int]:
    lines = len(data.splitlines())
    words = len(data.split())
    chars = len(data)

    return lines, words, chars


def _format_counts(
    lines: int,
    words: int,
    chars: int,
    selected: list[str],
    human: bool,
) -> str:
    if selected:
        values: list[str] = []

        for option in selected:
            if option == "lines":
                value = lines
                suffix = "L"

            elif option == "words":
                value = words
                suffix = "W"

            else:
                value = chars
                suffix = "C"

            if human:
                values.append(f"{_human(value)}{suffix}")
            else:
                values.append(str(value))

        return " ".join(values)

    if human:
        return (
            f"{_human(lines)}L "
            f"{_human(words)}W "
            f"{_human(chars)}C"
        )

    return f"{lines} {words} {chars}"


def _read_file(
    filename: str,
    context: ShellContext,
) -> str:
    path = context.resolve_path(filename)

    if not path.exists():
        raise ValueError(
            f"wc: {filename}: No such file or directory"
        )

    if not path.is_file():
        raise ValueError(
            f"wc: {filename}: Is a directory"
        )

    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except OSError as exc:
        raise ValueError(
            f"wc: {filename}: {exc}"
        ) from exc


def _run_wc(
    args: list[str],
    context: ShellContext,
) -> str:
    human = False
    selected: list[str] = []
    files: list[str] = []

    for arg in args:
        if arg in {"-h", "--human"}:
            human = True

        elif arg in {"-l", "--lines"}:
            selected.append("lines")

        elif arg in {"-w", "--words"}:
            selected.append("words")

        elif arg in {"-c", "--chars", "-m", "--characters"}:
            selected.append("chars")

        elif arg.startswith("-"):
            raise ValueError(
                f"unknown option: {arg}"
            )

        else:
            files.append(arg)

    if files:
        results: list[str] = []

        for filename in files:
            data = _read_file(filename, context)

            lines, words, chars = _count(data)

            output = _format_counts(
                lines,
                words,
                chars,
                selected,
                human,
            )

            results.append(
                f"{output} {filename}"
            )

        return "\n".join(results)

    data = context.stdin.read()

    lines, words, chars = _count(data)

    return _format_counts(
        lines,
        words,
        chars,
        selected,
        human,
    )


def cmd_wc(
    args: list[str],
    context: ShellContext,
) -> str:
    if not args:
        raise ValueError("missing argument")

    # Easter egg: wc -h -h
    if args.count("-h") == 2 and all(
        arg in {"-h", "--human"} or not arg.startswith("-")
        for arg in args
    ):
        normal_args = args.copy()
        normal_args.remove("-h")

        result = _run_wc(normal_args, context)

        return (
            "Why you don't even know this??\n"
            f"{result}\n"
            "(L=Line, W=Words, C=Chars, ok?)"
        )

    return _run_wc(args, context)
