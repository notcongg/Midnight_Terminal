from __future__ import annotations

from dataclasses import dataclass

from src.cmd.rootfs.ai.models import DEFAULT_MODEL, MODELS


@dataclass(slots=True)
class AIOptions:
    model: str = DEFAULT_MODEL
    thinking: bool = False
    stream: bool = False
    temperature: float = 1.0
    top_p: float = 0.95
    max_tokens: int = 16384
    seed: int = 42
    system: str | None = None


HELP = """Usage:
  ai [flags] <question>

Model:
  --model=<fast|medium|deep>
  -m <fast|medium|deep>
      Select the AI model.

  --fast
      Use the fast model.

  --medium
      Use the medium model.

  --deep
      Use the deep model.

Thinking:
  --thinking=True|False
  -thinking=True|False
      Enable or disable thinking.

  --thinking
      Enable thinking.

  --no-thinking
      Disable thinking.

Streaming:
  --stream=True|False
  -stream=True|False
      Enable or disable streaming.

  --stream
      Enable streaming.

  --no-stream
      Disable streaming.

Sampling:
  --temperature=<value>
  -t <value>
      Set temperature.

  --top-p=<value>
  -p <value>
      Set top-p.

  --max-tokens=<value>
  -n <value>
      Set maximum output tokens.

  --seed=<value>
      Set random seed.

System:
  --system=<prompt>
      Set system prompt.

Other:
  --help
  -h
      Show this help.

  --
      Stop parsing flags.

Examples:
  ai "hello"
  ai --fast "what is 2 + 2?"
  ai -m medium "explain this error"
  ai --deep "design an operating system"
  ai --deep --thinking=True "solve this algorithm"
  ai --fast --stream "tell me a story"

Pipeline:
  cat error.log | ai "explain this error"
  cat main.py | ai --medium "review this code"
  git diff | ai --deep "review these changes"
  cat file.txt | ai "summarize this" | grep Python
"""


def _parse_bool(value: str) -> bool:
    value = value.strip().lower()

    if value in {"true", "1", "yes", "on"}:
        return True

    if value in {"false", "0", "no", "off"}:
        return False

    raise ValueError(
        f"invalid boolean value '{value}' "
        "(expected True or False)"
    )


def _require_value(
    args: list[str],
    index: int,
    flag: str,
) -> tuple[str, int]:
    index += 1

    if index >= len(args):
        raise ValueError(
            f"{flag}: missing value"
        )

    return args[index], index


def _set_model(
    options: AIOptions,
    value: str,
) -> None:
    value = value.strip().lower()

    if value not in MODELS:
        raise ValueError(
            f"invalid model '{value}' "
            "(expected fast, medium or deep)"
        )

    options.model = value


def parse_args(
    args: list[str],
) -> tuple[AIOptions, list[str]]:
    options = AIOptions()
    question: list[str] = []

    index = 0

    while index < len(args):
        arg = args[index]

        # ---------------------------------------------------------
        # Stop parsing
        # ---------------------------------------------------------

        if arg == "--":
            question.extend(args[index + 1:])
            break

        # ---------------------------------------------------------
        # Model
        # ---------------------------------------------------------

        if arg.startswith("--model="):
            _set_model(
                options,
                arg.split("=", 1)[1],
            )

        elif arg.startswith("-model="):
            _set_model(
                options,
                arg.split("=", 1)[1],
            )

        elif arg in {"--model", "-model", "-m"}:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            _set_model(
                options,
                value,
            )

        elif arg == "--fast":
            options.model = "fast"

        elif arg == "--medium":
            options.model = "medium"

        elif arg == "--deep":
            options.model = "deep"

        # ---------------------------------------------------------
        # Thinking
        # ---------------------------------------------------------

        elif arg.startswith("--thinking="):
            options.thinking = _parse_bool(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-thinking="):
            options.thinking = _parse_bool(
                arg.split("=", 1)[1]
            )

        elif arg in {"--thinking", "-thinking"}:
            options.thinking = True

        elif arg in {
            "--no-thinking",
            "-no-thinking",
        }:
            options.thinking = False

        # ---------------------------------------------------------
        # Stream
        # ---------------------------------------------------------

        elif arg.startswith("--stream="):
            options.stream = _parse_bool(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-stream="):
            options.stream = _parse_bool(
                arg.split("=", 1)[1]
            )

        elif arg in {"--stream", "-stream"}:
            options.stream = True

        elif arg in {
            "--no-stream",
            "-no-stream",
        }:
            options.stream = False

        # ---------------------------------------------------------
        # Temperature
        # ---------------------------------------------------------

        elif arg.startswith("--temperature="):
            options.temperature = float(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-temperature="):
            options.temperature = float(
                arg.split("=", 1)[1]
            )

        elif arg in {
            "--temperature",
            "-temperature",
            "-t",
        }:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            options.temperature = float(value)

        # ---------------------------------------------------------
        # Top P
        # ---------------------------------------------------------

        elif arg.startswith("--top-p="):
            options.top_p = float(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-top-p="):
            options.top_p = float(
                arg.split("=", 1)[1]
            )

        elif arg in {
            "--top-p",
            "-top-p",
            "-p",
        }:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            options.top_p = float(value)

        # ---------------------------------------------------------
        # Max tokens
        # ---------------------------------------------------------

        elif arg.startswith("--max-tokens="):
            options.max_tokens = int(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-max-tokens="):
            options.max_tokens = int(
                arg.split("=", 1)[1]
            )

        elif arg in {
            "--max-tokens",
            "-max-tokens",
            "-n",
        }:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            options.max_tokens = int(value)

        # ---------------------------------------------------------
        # Seed
        # ---------------------------------------------------------

        elif arg.startswith("--seed="):
            options.seed = int(
                arg.split("=", 1)[1]
            )

        elif arg.startswith("-seed="):
            options.seed = int(
                arg.split("=", 1)[1]
            )

        elif arg in {
            "--seed",
            "-seed",
        }:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            options.seed = int(value)

        # ---------------------------------------------------------
        # System
        # ---------------------------------------------------------

        elif arg.startswith("--system="):
            options.system = arg.split(
                "=",
                1,
            )[1]

        elif arg.startswith("-system="):
            options.system = arg.split(
                "=",
                1,
            )[1]

        elif arg in {
            "--system",
            "-system",
        }:
            value, index = _require_value(
                args,
                index,
                arg,
            )

            options.system = value

        # ---------------------------------------------------------
        # Help
        # ---------------------------------------------------------

        elif arg in {"--help", "-h"}:
            raise ValueError(HELP)

        # ---------------------------------------------------------
        # Unknown flag
        # ---------------------------------------------------------

        elif arg.startswith("-"):
            raise ValueError(
                f"unknown option '{arg}'"
            )

        # ---------------------------------------------------------
        # Question
        # ---------------------------------------------------------

        else:
            question.append(arg)

        index += 1

    return options, question
