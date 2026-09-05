"""
executor.py

Walks a Sequence AST and executes each Pipeline (left-to-right,
respecting '&&', '||' and ';' and the exit status of the previous
pipeline) by dispatching Commands through the existing command registry.

Commands not present in the registry are executed as external
processes through the native Midnight Extensions bridge.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import time
from typing import Any, Callable

from src.cmd.utils.registry import COMMANDS
from src.extensions.extensions import Extensions
from src.shell.ast.ast import Command, Pipeline, Sequence
from src.shell.context.context import ShellContext
from src.shell.errors.errors import ExecutionError, ShellError
from src.shell.syntax.suggestions import format_suggestions


# ============================================================
# EXTERNAL PROCESS EXTENSIONS
# ============================================================

_extensions = Extensions()


# ============================================================
# COMMAND RESOLUTION
# ============================================================

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


def _is_builtin(name: str) -> bool:
    return name in COMMANDS


# ============================================================
# BUILTIN INVOCATION
# ============================================================

def _invoke_command(
    handler: Callable[..., Any],
    name: str,
    args: list[str],
    context: ShellContext,
) -> str | None:
    try:
        try:
            param_count = len(
                inspect.signature(handler).parameters
            )
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


# ============================================================
# REDIRECTION
# ============================================================

def _open_redirect_path(
    context: ShellContext,
    target: str,
    mode: str,
):
    path = context.resolve_path(target)

    return open(
        path,
        mode,
        encoding="utf-8",
    )


# ============================================================
# EXTERNAL COMMAND
# ============================================================

def _execute_external(
    command: Command,
    *,
    context: ShellContext,
    working_directory: str | None,
    stdin_data: str | None,
) -> tuple[str | None, int]:
    """
    Execute an external process through the native Extensions DLL.

    Returns:
        (stdout, exit_code)

    stderr is written directly to the shell stderr stream.

    stdin_data is passed to Extensions.call_text() when supported.
    """

    if not command.name:
        raise ExecutionError(
            "Cannot execute an empty external command"
        )

    # --------------------------------------------------------
    # BUILD COMMAND LINE
    # --------------------------------------------------------

    command_line = command.name

    if command.args:
        command_line += " " + " ".join(
            _quote_external_argument(arg)
            for arg in command.args
        )

    # --------------------------------------------------------
    # PREPARE EXTENSIONS CALL
    # --------------------------------------------------------

    call_text = _extensions.call_text

    kwargs: dict[str, Any] = {}

    if working_directory is not None:
        kwargs["working_directory"] = working_directory

    # --------------------------------------------------------
    # CHECK stdin_data SUPPORT
    # --------------------------------------------------------

    try:
        signature = inspect.signature(call_text)
        parameters = signature.parameters

        accepts_stdin = (
            "stdin_data" in parameters
            or any(
                parameter.kind
                == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )
        )

    except (TypeError, ValueError):
        accepts_stdin = False

    if accepts_stdin:
        kwargs["stdin_data"] = stdin_data or ""

    elif stdin_data is not None:
        raise ExecutionError(
            f"{command.name}: external extensions backend "
            "does not support stdin input",
            command_name=command.name,
        )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    try:
        result = call_text(
            command_line,
            **kwargs,
        )

    except FileNotFoundError as exc:
        raise ExecutionError(
            f"{command.name}: external execution backend "
            f"not available: {exc}",
            command_name=command.name,
        ) from exc

    except OSError as exc:
        raise ExecutionError(
            f"{command.name}: {exc}",
            command_name=command.name,
        ) from exc

    except TypeError as exc:
        raise ExecutionError(
            f"{command.name}: invalid extensions API call: {exc}",
            command_name=command.name,
        ) from exc

    # --------------------------------------------------------
    # NATIVE API FAILURE
    # --------------------------------------------------------

    if not result["success"]:
        error_code = result["error_code"]

        raise ExecutionError(
            f"{command.name}: failed to execute "
            f"(error {error_code})",
            command_name=command.name,
        )

    # --------------------------------------------------------
    # STDERR
    # --------------------------------------------------------

    stderr = result["stderr"]

    if stderr:
        context.stderr.write(stderr)

        if not stderr.endswith("\n"):
            context.stderr.write("\n")

        context.stderr.flush()

    # --------------------------------------------------------
    # STDOUT
    # --------------------------------------------------------

    stdout = result["stdout"]

    if stdout == "":
        stdout = None

    return stdout, result["exit_code"]


def _quote_external_argument(
    argument: str,
) -> str:
    """
    Quote one argument for the Windows command line.

    This intentionally keeps command construction simple and
    compatible with CreateProcessW. Empty arguments and arguments
    containing whitespace/quotes are handled.
    """

    if argument == "":
        return '""'

    if not any(
        character in argument
        for character in (" ", "\t", '"')
    ):
        return argument

    escaped = (
        argument
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    return f'"{escaped}"'


# ============================================================
# SEQUENCE
# ============================================================

def execute(
    sequence: Sequence,
    context: ShellContext,
) -> int:
    """
    Execute a Sequence AST.

    Supports:
        &&
        ||
        ;

    Returns the final exit status.

    The status is also stored in:
        context.last_exit_code
    """

    if not sequence.pipelines:
        raise ExecutionError(
            "Cannot execute an empty pipeline"
        )

    status = 0

    for index, pipeline in enumerate(
        sequence.pipelines
    ):
        if index > 0:
            connector = sequence.connectors[index - 1]

            # ------------------------------------------------
            # SHORT CIRCUIT
            # ------------------------------------------------

            if connector == "&&" and status != 0:
                continue

            if connector == "||" and status == 0:
                continue

        try:
            status = _execute_pipeline(
                pipeline,
                context,
            )

        except ShellError as exc:
            context.stderr.write(
                f"{exc}\n"
            )
            context.stderr.flush()

            status = 1

        context.last_exit_code = status

    return status


# ============================================================
# PIPELINE
# ============================================================

def _execute_pipeline(
    pipeline: Pipeline,
    context: ShellContext,
) -> int:
    """
    Execute one pipeline.

    Example:
        echo hello | grep hello

    Commands are executed left-to-right.
    """

    if not pipeline.commands:
        raise ExecutionError(
            "Cannot execute an empty pipeline"
        )

    commands = pipeline.commands

    # --------------------------------------------------------
    # TIME WRAPPER
    # --------------------------------------------------------

    if commands[0].name == "time":
        time_command = commands[0]

        if not time_command.args:
            raise ExecutionError(
                "time: missing command",
                command_name="time",
            )

        first_command = Command(
            name=time_command.args[0],
            args=time_command.args[1:],
            redirections=time_command.redirections,
        )

        wrapped_commands = [
            first_command,
            *commands[1:],
        ]

        wrapped_pipeline = Pipeline(
            commands=wrapped_commands,
        )

        started = time.perf_counter()

        try:
            return _execute_pipeline(
                wrapped_pipeline,
                context,
            )

        finally:
            elapsed = (
                time.perf_counter() - started
            )

            context.stderr.write(
                f"[time] {elapsed:.6f}s\n"
            )
            context.stderr.flush()

    # --------------------------------------------------------
    # PIPELINE EXECUTION
    # --------------------------------------------------------

    piped_input: str | None = None
    status = 0

    for index, command in enumerate(commands):
        is_last = (
            index == len(commands) - 1
        )

        piped_input, status = _execute_single_command(
            command,
            context=context,
            piped_input=piped_input,
            is_last=is_last,
        )

    return status


# ============================================================
# SINGLE COMMAND
# ============================================================

def _execute_single_command(
    command: Command,
    *,
    context: ShellContext,
    piped_input: str | None,
    is_last: bool,
) -> tuple[str | None, int]:

    # --------------------------------------------------------
    # TIME INSIDE PIPELINE
    # --------------------------------------------------------

    if command.name == "time":
        if not command.args:
            raise ExecutionError(
                "time: missing command",
                command_name="time",
            )

        nested_command = Command(
            name=command.args[0],
            args=command.args[1:],
            redirections=command.redirections,
        )

        started = time.perf_counter()

        try:
            return _execute_single_command(
                nested_command,
                context=context,
                piped_input=piped_input,
                is_last=is_last,
            )

        finally:
            elapsed = (
                time.perf_counter() - started
            )

            context.stderr.write(
                f"[time] {elapsed:.6f}s\n"
            )
            context.stderr.flush()

    # --------------------------------------------------------
    # COMMAND TYPE
    # --------------------------------------------------------

    builtin = _is_builtin(
        command.name
    )

    # --------------------------------------------------------
    # INPUT REDIRECTION
    # --------------------------------------------------------

    effective_input = piped_input

    input_redirections = [
        redirection
        for redirection in command.redirections
        if redirection.type == "<"
    ]

    if input_redirections:
        source_path = (
            input_redirections[-1].target
        )

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

    # --------------------------------------------------------
    # EXTERNAL COMMAND
    # --------------------------------------------------------

    if not builtin:
        working_directory = (
            str(context.cwd)
            if context.cwd is not None
            else None
        )

        output, status = _execute_external(
            command,
            context=context,
            working_directory=working_directory,
            stdin_data=effective_input,
        )

        # ----------------------------------------------------
        # OUTPUT REDIRECTION
        # ----------------------------------------------------

        output_redirections = [
            redirection
            for redirection in command.redirections
            if redirection.type in (">", ">>")
        ]

        if output_redirections:
            redirection = (
                output_redirections[-1]
            )

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
                        file_handle.write(
                            output
                        )

                        if not output.endswith(
                            "\n"
                        ):
                            file_handle.write(
                                "\n"
                            )

            except OSError as exc:
                raise ExecutionError(
                    f"{command.name}: cannot write "
                    f"'{redirection.target}': {exc}",
                    command_name=command.name,
                ) from exc

            return None, status

        # ----------------------------------------------------
        # FINAL EXTERNAL COMMAND
        # ----------------------------------------------------

        if is_last:
            if output is not None:
                context.stdout.write(
                    output
                )

                if not output.endswith(
                    "\n"
                ):
                    context.stdout.write(
                        "\n"
                    )

                context.stdout.flush()

            return None, status

        # ----------------------------------------------------
        # EXTERNAL PIPELINE OUTPUT
        # ----------------------------------------------------

        return output, status

    # --------------------------------------------------------
    # BUILTIN RESOLUTION
    # --------------------------------------------------------

    handler = _resolve_command(
        command.name
    )

    # --------------------------------------------------------
    # EXECUTION CONTEXT
    # --------------------------------------------------------

    exec_context = (
        context.clone_streams_reset()
    )

    exec_context.has_pipeline_input = (
        effective_input is not None
    )

    if effective_input is not None:
        exec_context.stdin = io.StringIO(
            effective_input
        )

    # --------------------------------------------------------
    # OUTPUT CAPTURE
    # --------------------------------------------------------

    output_redirections = [
        redirection
        for redirection in command.redirections
        if redirection.type in (">", ">>")
    ]

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

    # --------------------------------------------------------
    # EXECUTE BUILTIN
    # --------------------------------------------------------

    try:
        with contextlib.redirect_stdout(
            stdout_target
        ):
            output = _invoke_command(
                handler,
                command.name,
                command.args,
                exec_context,
            )

    finally:
        context.cwd = exec_context.cwd

        context.exit_requested = (
            exec_context.exit_requested
        )

    # --------------------------------------------------------
    # COLLECT OUTPUT
    # --------------------------------------------------------

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
        output = (
            captured + output
        )

    # --------------------------------------------------------
    # OUTPUT REDIRECTION
    # --------------------------------------------------------

    if output_redirections:
        redirection = (
            output_redirections[-1]
        )

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
                    file_handle.write(
                        output
                    )

                    if not output.endswith(
                        "\n"
                    ):
                        file_handle.write(
                            "\n"
                        )

        except OSError as exc:
            raise ExecutionError(
                f"{command.name}: cannot write "
                f"'{redirection.target}': {exc}",
                command_name=command.name,
            ) from exc

        return None, 0

    # --------------------------------------------------------
    # FINAL BUILTIN
    # --------------------------------------------------------

    if is_last:
        if output is not None:
            context.stdout.write(
                output
            )

            if not output.endswith(
                "\n"
            ):
                context.stdout.write(
                    "\n"
                )

            context.stdout.flush()

        return None, 0

    # --------------------------------------------------------
    # BUILTIN PIPELINE OUTPUT
    # --------------------------------------------------------

    return output, 0
