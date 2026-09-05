from __future__ import annotations

from src.cmd.rootfs.env.env import reload_envconfig
from src.shell.context.context import ShellContext


def man_source() -> str:
    return """SOURCE(1)                Midnight Terminal Manual             SOURCE(1)

NAME

    source - reload environment configuration

SYNOPSIS

    source

DESCRIPTION

    Reloads envconfig.dream into the current Midnight Terminal
    environment without restarting the shell.

EXAMPLES

    source

SEE ALSO

    env(1), set(1), unset(1), enfix(1)

"""


def cmd_source(
    args: list[str],
    context: ShellContext,
) -> None:
    if args:
        raise ValueError("source: unexpected arguments")

    try:
        reload_envconfig(context)
    except Exception as exc:
        raise ValueError(
            f"source: failed to reload environment: {exc}"
        ) from exc
