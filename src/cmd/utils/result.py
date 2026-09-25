from dataclasses import dataclass


@dataclass
class CommandResult:
    output: str = ""
    status: int = 0