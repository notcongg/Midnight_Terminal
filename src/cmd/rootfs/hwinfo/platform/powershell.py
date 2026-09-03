from __future__ import annotations

import json
import subprocess
from typing import Any


class PowerShellError(RuntimeError):
    """Raised when a PowerShell command cannot be executed."""


def run(
    script: str,
    *,
    timeout: float | None = 10.0,
) -> str:
    """
    Execute a PowerShell script and return stdout.

    Args:
        script:
            PowerShell script to execute.

        timeout:
            Maximum execution time in seconds.
            None disables the timeout.

    Returns:
        Stripped stdout.

    Raises:
        PowerShellError:
            If PowerShell cannot be started or exits with an error.
    """

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise PowerShellError(
            "PowerShell executable was not found."
        ) from exc

    except subprocess.TimeoutExpired as exc:
        raise PowerShellError(
            "PowerShell command timed out."
        ) from exc

    except OSError as exc:
        raise PowerShellError(
            f"Failed to execute PowerShell: {exc}"
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()

        if stderr:
            raise PowerShellError(
                f"PowerShell exited with code "
                f"{result.returncode}: {stderr}"
            )

        raise PowerShellError(
            f"PowerShell exited with code "
            f"{result.returncode}."
        )

    return result.stdout.strip()


def run_json(
    script: str,
    *,
    timeout: float | None = 10.0,
) -> Any:
    """
    Execute a PowerShell script and parse its stdout as JSON.

    Returns:
        Parsed JSON value.

    Raises:
        PowerShellError:
            If execution fails or output is invalid JSON.
    """

    output = run(
        script,
        timeout=timeout,
    )

    if not output:
        raise PowerShellError(
            "PowerShell returned empty output."
        )

    try:
        return json.loads(output)

    except json.JSONDecodeError as exc:
        raise PowerShellError(
            "PowerShell returned invalid JSON."
        ) from exc


def run_json_or_none(
    script: str,
    *,
    timeout: float | None = 10.0,
) -> Any | None:
    """
    Execute a PowerShell script and return parsed JSON.

    Any PowerShell or JSON parsing error is converted to None.

    Useful for hardware collectors where a missing optional
    data source should not crash the entire HWINFO command.
    """

    try:
        return run_json(
            script,
            timeout=timeout,
        )
    except PowerShellError:
        return None
