from __future__ import annotations

import os
import signal


def man_task() -> str:
    return """TASK(1)                  Midnight Terminal Manual                 TASK(1)

NAME

    task - show process details

SYNOPSIS

    task <pid>
    task -p=<pid>
    task --pid=<pid>

DESCRIPTION

    Displays process information for a single PID.

EXAMPLES

    task 208
    task -p=208

SEE ALSO

    kill(1), ps(1), top(1)

"""


def man_kill() -> str:
    return """KILL(1)                  Midnight Terminal Manual                 KILL(1)

NAME

    kill - terminate a running process

SYNOPSIS

    kill [-f|--force] <pid>

DESCRIPTION

    Asks a process to exit. Use -f/--force to terminate immediately.

EXAMPLES

    kill 208
    kill -f 208

SEE ALSO

    task(1), ps(1), top(1)

"""


def _parse_pid(
    args: list[str],
    command: str,
    usage: str,
) -> int | None:
    if not args:
        print("[ERROR] Missing process ID.")
        print(f"Usage: {usage}")
        return None

    if len(args) > 1:
        print("[ERROR] Too many arguments.")
        print(f"Usage: {usage}")
        return None

    value = args[0].strip()

    if value.startswith("--pid="):
        value = value[len("--pid="):]
    elif value.startswith("-p="):
        value = value[len("-p="):]
    elif value.startswith("-"):
        print(f"[ERROR] Unknown option: {value}")
        return None

    if not value:
        print("[ERROR] Missing process ID.")
        return None

    try:
        pid = int(value)
    except ValueError:
        print(f"[ERROR] Invalid PID: {value}")
        return None

    if pid < 0:
        print(f"[ERROR] Invalid PID: {pid}")
        return None

    return pid


def _process_name(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/comm", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return None


def cmd_task(
    args: list[str],
) -> None:
    pid = _parse_pid(args, "task", "task <pid>")

    if pid is None:
        return

    name = _process_name(pid)

    if name is None:
        print(f"[ERROR] Process {pid} not found.")
        return

    print("Process Information")
    print("─" * 40)
    print(f"{'PID':<12}: {pid}")
    print(f"{'Name':<12}: {name}")

    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            fields = handle.read().split()
            parent_pid = fields[3] if len(fields) > 3 else "?"
            threads = fields[19] if len(fields) > 19 else "?"
    except OSError:
        parent_pid = "?"
        threads = "?"

    print(f"{'Parent PID':<12}: {parent_pid}")
    print(f"{'Threads':<12}: {threads}")

    try:
        with open(f"/proc/{pid}/statm", encoding="utf-8") as handle:
            pages = int(handle.read().split()[1])
            memory = pages * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError):
        memory = None

    print(f"{'Memory':<12}: {memory if memory is not None else 'Unavailable'}")
    print(f"{'Status':<12}: Running")


def cmd_kill(
    args: list[str],
) -> None:
    force = False
    pid_args: list[str] = []

    for arg in args:
        if arg in ("-f", "--force"):
            force = True
        else:
            pid_args.append(arg)

    pid = _parse_pid(pid_args, "kill", "kill <pid>")

    if pid is None:
        return

    name = _process_name(pid)

    if name is None:
        print(f"[ERROR] Process {pid} not found.")
        return

    death_signal = signal.SIGKILL if force else signal.SIGTERM

    try:
        os.kill(pid, death_signal)
    except ProcessLookupError:
        print(f"[ERROR] Process {pid} no longer exists.")
        return
    except PermissionError:
        print(f"[ERROR] Access denied for process {pid}.")
        return
    except OSError as exc:
        print(f"[ERROR] Failed to terminate process {pid} ({exc}).")
        return

    verb = "Terminated" if force else "Closed"
    print(f"[OK] {verb} {name} (PID {pid}).")
