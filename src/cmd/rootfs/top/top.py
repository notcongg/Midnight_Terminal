from __future__ import annotations

import ctypes
import sys
import time

from src.cmd.rootfs.ps.ps import (
    CPU_SAMPLE_INTERVAL,
    MEMORYSTATUSEX,
    ProcessMetrics,
    _enable_ansi_console,
    _live_max_rows,
    _live_sort_key,
    _SORT_KEYS,
    classify_process,
    enumerate_processes,
    format_table,
    get_total_memory,
    get_window_pids,
    kernel32,
    parse_ps_options,
    run_realtime,
)
from src.shell.context.context import ShellContext


def man_top() -> str:
    return """TOP(1)                   Midnight Terminal Manual                  TOP(1)

NAME
    top - realtime view of the busiest processes

SYNOPSIS
    top
    top -n=<count>
    top -rt=false

DESCRIPTION
    Live dashboard of the most CPU-hungry processes, redrawn in place
    every second until interrupted with Ctrl+C. Shows a summary line
    (process count, total CPU usage, memory load) followed by the
    same table layout as `ps` (PID, PPID, THREADS, CPU%, MEM%, TYPE,
    NAME), sorted busiest-first.

    Reuses the process enumeration and metrics of `ps`; no separate
    process enumeration logic.

OPTIONS

    -n=<count>   limit the table to <count> rows
    -rt=false    one-shot snapshot instead of the live view
    -a           include system processes as well
    -sort=<key>  sort rows by cpu|mem|pid|ppid|threads|name

SEE ALSO
    ps(1), task(1), kill(1)
"""


def _memory_load() -> int | None:
    """Total memory load in percent (None when unavailable)."""

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None

    return int(status.dwMemoryLoad)


def _build_summary(processes, use_colors: bool) -> str:
    """One top-style summary line above the process table."""

    total_cpu = sum(
        process.cpu_percent or 0.0
        for process in processes
    )

    mem_load = _memory_load()
    mem_text = f"{mem_load}%" if mem_load is not None else "-"

    timestamp = time.strftime("%H:%M:%S")

    summary = (
        f"top - {timestamp} | "
        f"{len(processes)} processes | "
        f"CPU {total_cpu:.1f}% | "
        f"memory {mem_text}"
    )

    if use_colors:
        return f"\033[1m{summary}\033[0m"

    return summary


def cmd_top(args: list[str], context: ShellContext) -> str:
    """
    Execute `top`.

    Realtime, always-sorted view of the busiest processes, built on
    the `ps` process-management infrastructure.
    """

    options = parse_ps_options(args)

    use_colors = sys.stdout.isatty()

    metrics = ProcessMetrics()

    def collect():
        """One sampling pass: enumerate, measure, classify."""
        processes = enumerate_processes()
        app_pids, hung_pids = get_window_pids()
        total_memory = get_total_memory()

        metrics.update(processes, total_memory)

        for process in processes:
            process.category = classify_process(
                process,
                app_pids,
            )
            process.hung = process.pid in hung_pids

        return processes

    def sort_key(process):
        if options.sort_key is not None:
            return _SORT_KEYS[options.sort_key](process)
        return _live_sort_key(process)

    max_rows = _live_max_rows(options.limit)

    if not sys.stdout.isatty():
        # Snapshot mode (piped/redirected output): same two-pass CPU
        # sampling as the one-shot `ps` table.
        if use_colors:
            _enable_ansi_console()

        collect()
        time.sleep(CPU_SAMPLE_INTERVAL)
        processes = collect()
        processes.sort(key=sort_key)

        return (
            f"{_build_summary(processes, use_colors)}\n"
            f"{format_table(processes[:max_rows], colors=use_colors)}"
        )

    def build_table() -> str:
        processes = collect()
        processes.sort(key=sort_key)
        return (
            f"{_build_summary(processes, use_colors)}\n"
            f"{format_table(processes[:max_rows], colors=use_colors)}"
        )

    return run_realtime(build_table)
