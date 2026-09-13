from __future__ import annotations


def read_multiline(
    lines: list[str],
    start: int,
) -> tuple[str, int]:
    """
    Read a multiline block starting with `[` and ending with `]`.

    The brackets are preserved.

    Returns:
        (block, next_line_index)
    """

    first = lines[start]

    opening = first.find("[")

    if opening == -1:
        return first, start + 1

    content: list[str] = ["["]

    depth = 1
    index = start + 1

    while index < len(lines):
        line = lines[index]

        # Closing bracket on its own line.
        if line.strip() == "]":
            content.append("]")
            return "\n".join(content), index + 1

        depth += line.count("[")
        depth -= line.count("]")

        if depth <= 0:
            before_closing = line.rsplit("]", 1)[0]

            if before_closing:
                content.append(before_closing)

            content.append("]")
            return "\n".join(content), index + 1

        content.append(line)
        index += 1

    raise ValueError("unterminated multiline block")
