from __future__ import annotations

from dataclasses import dataclass

from src.shell.errors.errors import ShellError
from src.shell.lexer.lexer import tokenize
from src.shell.parser.parser import parse


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    error: str | None = None


def validate(source: str) -> ValidationResult:
    if not source.strip():
        return ValidationResult(valid=True)

    try:
        tokens = tokenize(source)

        if not tokens:
            return ValidationResult(valid=True)

        parse(tokens)

    except ShellError as exc:
        return ValidationResult(
            valid=False,
            error=str(exc),
        )

    except (ValueError, TypeError, IndexError) as exc:
        return ValidationResult(
            valid=False,
            error=str(exc),
        )

    return ValidationResult(valid=True)
