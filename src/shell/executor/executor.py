"""
executor.py

Walks a Pipeline AST and executes each Command by dispatching
through the existing command registry.
"""

from __future__ import annotations

import contextlib
import inspect
import io
from typing import Any, Callable

from src.cmd.utils.registry import COMMANDS
from src.shell.ast.ast import Command, Pipeline
from src.shell.context.context import ShellContext
from src.shell.errors.errors import ExecutionError
from src.shell.syntax.suggestions import format_suggestions


def _resolve_command(name: str) -> Callable[..., Any]:
    try:
        return COMMANDS[name]
    except KeyError as exc:
        message = f"{name}: command not found"

        suggestion = format_suggestions(name)

        if suggestion:
            message += f"\n{suggestion}"

        raise ExecutionError(
            message,
            command_name=name,
        ) from exc


def _invoke_command(
    handler: Callable[..., Any],
    name: str,
    args: list[str],
    context: ShellContext,
) -> str | None:
    try:
        try:
            param_count = len(inspect.signature(handler).parameters)
        except (TypeError, ValueError):
            param_count = 1

        if param_count >= 2:
            return handler(args, context)

        return handler(args)

    except ExecutionError:
        raise

    except Exception as exc:
        raise ExecutionError(
            f"{name}: {exc}",
            command_name=name,
        ) from exc


def _open_redirect_path(
    context: ShellContext,
    target: str,
    mode: str,
):
    path = context.resolve_path(target)
    return open(path, mode, encoding="utf-8")


def execute(
    pipeline: Pipeline,
    context: ShellContext,
) -> None:
    if not pipeline.commands:
        raise ExecutionError("Cannot execute an empty pipeline")

    piped_input: str | None = None

    for index, command in enumerate(pipeline.commands):
        is_last = index == len(pipeline.commands) - 1

        piped_input = _execute_single_command(
            command,
            context=context,
            piped_input=piped_input,
            is_last=is_last,
        )


def _execute_single_command(
    command: Command,
    *,
    context: ShellContext,
    piped_input: str | None,
    is_last: bool,
) -> str | None:
    handler = _resolve_command(command.name)

    effective_input = piped_input

    output_redirections = [
        redirection
        for redirection in command.redirections
        if redirection.type in (">", ">>")
    ]

    input_redirections = [
        redirection
        for redirection in command.redirections
        if redirection.type == "<"
    ]

    if input_redirections:
        source_path = input_redirections[-1].target

        try:
            with _open_redirect_path(
                context,
                source_path,
                "r",
            ) as file_handle:
                effective_input = file_handle.read()

        except OSError as exc:
            raise ExecutionError(
                f"{command.name}: cannot read "
                f"'{source_path}': {exc}",
                command_name=command.name,
            ) from exc

    exec_context = context.clone_streams_reset()

    if effective_input is not None:
        exec_context.stdin = io.StringIO(effective_input)

    capture = (
        not is_last
        or bool(output_redirections)
    )

    buffer = io.StringIO()

    if capture:
        exec_context.stdout = buffer

    stdout_target = (
        buffer
        if capture
        else context.stdout
    )

    try:
        with contextlib.redirect_stdout(stdout_target):
            output = _invoke_command(
                handler,
                command.name,
                command.args,
                exec_context,
            )

    finally:
        context.cwd = exec_context.cwd
        context.exit_requested = exec_context.exit_requested

    captured = (
        buffer.getvalue()
        if capture
        else ""
    )

    if output is None:
        output = (
            captured
            if captured
            else None
        )

    elif captured:
        output = captured + output

    if output_redirections:
        redirection = output_redirections[-1]

        mode = (
            "a"
            if redirection.type == ">>"
            else "w"
        )

        try:
            with _open_redirect_path(
                context,
                redirection.target,
                mode,
            ) as file_handle:

                if output is not None:
                    file_handle.write(output)

                    if not output.endswith("\n"):
                        file_handle.write("\n")

        except OSError as exc:
            raise ExecutionError(
                f"{command.name}: cannot write "
                f"'{redirection.target}': {exc}",
                command_name=command.name,
            ) from exc

        return None

    if is_last:
        if output is not None:
            context.stdout.write(output)

            if not output.endswith("\n"):
                context.stdout.write("\n")

        return None

    return output
