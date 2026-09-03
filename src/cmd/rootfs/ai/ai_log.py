from __future__ import annotations

from datetime import datetime
from pathlib import Path


LOG_PATH = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "log"
    / "AI_LOG.log"
)


def write_ai_log(
    *,
    model: str,
    engine: str,
    thinking: bool,
    stream: bool,
    question: str,
    response: str,
) -> None:
    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    entry = (
        "\n"
        + "=" * 64
        + "\n"
        f"[{timestamp}]\n"
        "\n"
        "[REQUEST]\n"
        f"model: {model}\n"
        f"engine: {engine}\n"
        f"thinking: {thinking}\n"
        f"stream: {stream}\n"
        f"question: {question}\n"
        "\n"
        "[RESPONSE]\n"
        f"{response.rstrip()}\n"
        + "=" * 64
        + "\n"
    )

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(entry)
