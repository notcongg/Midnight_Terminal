"""
Midnight Terminal - ps command.

Usage:

    ps
    ps -a
    ps -rt=true
    ps -rt=false
    ps -n=20
    ps -a -rt=false
    ps -a -n=20
    ps -n=20 -rt=true

Lists the running Windows processes as a table, grouped into
apps, background processes and system processes:

    PID      PPID     THREADS     CPU%    MEM% TYPE         NAME
    -------- -------- -------- ------- ------- ------------ ----------------------------
    ...

Options:

    -a           include system processes as well
    -n=<count>   limit the table to <count> rows
    -rt=true     realtime mode: live dashboard of the busiest
                 processes, redrawn in place every second
                 until interrupted with Ctrl+C
    -rt=false    one-shot mode (default)
    -sort=<key>  sort rows by cpu|mem|pid|ppid|threads|name
    -name=<pat>  only show processes whose name contains <pat>

Behavior notes:

- By default `ps` lists app and background processes. System
  processes (kernel, services host, session manager, ...) are
  only shown with `-a`.
- An "App" is a process that owns a visible top-level window;
  well-known system processes are recognized by name.
- The one-shot table is grouped: apps first, then background,
  then system, each group sorted by PID.
- THREADS, CPU% and MEM% are re-measured on every realtime
  refresh, so the live view is fully real time.
- CPU% is the share of total CPU. Realtime mode measures it
  between refreshes; one-shot mode measures it over a short
  CPU_SAMPLE_INTERVAL window. '-' means unavailable (access
  denied or already exited).
- MEM% is the process working set relative to total physical RAM.
- Colors (bold header, cyan PID, green/gray TYPE, yellow/red CPU%
  and MEM%, full red rows for hung processes) are applied only
  when the output goes straight to the terminal. Piped or
  redirected output stays plain, so tools like `grep` keep
  working.
- A process is shown in red when Windows reports it as not
  responding (IsHungAppWindow) -- an app that has problems and is
  a candidate for `kill`.
- Output is pipeline-friendly: `ps | grep python` keeps the table
  header and separator (the `grep` command detects them).
- Realtime mode shows a compact top-consumers dashboard, sized to
  always fit on screen. It redraws in place: nothing ever scrolls
  into scrollback, so the mouse-wheel position and the history
  above stay untouched. When stdout is captured (pipeline or
  redirection), a single snapshot is rendered instead.

Windows-only. Uses the Toolhelp32 snapshot API plus a window
enumeration pass (same approach as the `task` and `kill`
commands). On non-Windows platforms the command registry simply
skips loading this module.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import Callable

from src.shell.errors.errors import ShellError


# ============================================================
# Windows DLL
# ============================================================

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True,
)

user32 = ctypes.WinDLL(
    "user32",
    use_last_error=True,
)


# ============================================================
# Constants
# ============================================================

TH32CS_SNAPPROCESS = 0x00000002

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

REFRESH_INTERVAL = 1.0

CPU_SAMPLE_INTERVAL = 0.25  # one-shot CPU measurement window

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Console mode flag enabling ANSI escape sequences.
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

STD_OUTPUT_HANDLE = -11  # standard output device

_NAME_WIDTH = 28

_TYPE_WIDTH = 12

_PERCENT_WIDTH = 7  # e.g. ' 100.0%'

_CPU_COUNT = os.cpu_count() or 1

# Color thresholds (share of total CPU / share of total RAM).
_CPU_HIGH_THRESHOLD = 25.0      # CPU% shown in yellow
_MEM_WARN_THRESHOLD = 10.0      # MEM% shown in yellow
_MEM_CRITICAL_THRESHOLD = 25.0  # MEM% shown in red

# Live dashboard caps: the frame must always fit on screen so the
# in-place redraw never scrolls the terminal.
_LIVE_MAX_ROWS = 25

_LIVE_ROW_RESERVE = 5  # header + separator + prompt + margins

# Well-known system processes (matched case-insensitively).
_SYSTEM_PROCESS_NAMES = {
    "system",
    "registry",
    "secure system",
    "memory compression",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "lsaiso.exe",
    "svchost.exe",
    "dwm.exe",
    "fontdrvhost.exe",
    "audiodg.exe",
    "wudfhost.exe",
}

# Grouping order of the TYPE column (Apps first).
_CATEGORY_ORDER = {
    "App": 0,
    "Background": 1,
    "System": 2,
}


# ============================================================
# Structures
# ============================================================

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


# ============================================================
# API definitions
# ============================================================

kernel32.CreateToolhelp32Snapshot.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
]

kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE


kernel32.Process32FirstW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESSENTRY32W),
]

kernel32.Process32FirstW.restype = wintypes.BOOL


kernel32.Process32NextW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESSENTRY32W),
]

kernel32.Process32NextW.restype = wintypes.BOOL


kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE,
]

kernel32.CloseHandle.restype = wintypes.BOOL


# ============================================================
# Window API definitions (App vs Background detection)
# ============================================================

WNDENUMPROC = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.LPARAM,
)


user32.EnumWindows.argtypes = [
    WNDENUMPROC,
    wintypes.LPARAM,
]

user32.EnumWindows.restype = wintypes.BOOL


user32.IsWindowVisible.argtypes = [
    wintypes.HWND,
]

user32.IsWindowVisible.restype = wintypes.BOOL


user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]

user32.GetWindowThreadProcessId.restype = wintypes.DWORD


user32.IsHungAppWindow.argtypes = [
    wintypes.HWND,
]

user32.IsHungAppWindow.restype = wintypes.BOOL


# ============================================================
# Console API definitions (ANSI live view support)
# ============================================================

kernel32.GetStdHandle.argtypes = [
    wintypes.DWORD,
]

kernel32.GetStdHandle.restype = wintypes.HANDLE


kernel32.GetConsoleMode.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.DWORD),
]

kernel32.GetConsoleMode.restype = wintypes.BOOL


kernel32.SetConsoleMode.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
]

kernel32.SetConsoleMode.restype = wintypes.BOOL


# ============================================================
# Process metrics API definitions (CPU / memory)
# ============================================================

psapi = ctypes.WinDLL(
    "psapi",
    use_last_error=True,
)


kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]

kernel32.OpenProcess.restype = wintypes.HANDLE


kernel32.GetProcessTimes.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
]

kernel32.GetProcessTimes.restype = wintypes.BOOL


kernel32.GlobalMemoryStatusEx.argtypes = [
    ctypes.POINTER(MEMORYSTATUSEX),
]

kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL


psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]

psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


# ============================================================
# Configuration
# ============================================================

@dataclass
class PsOptions:
    """Parsed `ps` command configuration."""

    show_all: bool = False
    realtime: bool = False
    limit: int | None = None  # None = no explicit -n= limit
    sort_key: str | None = None  # None = default grouped/one-shot order
    filter_name: str | None = None  # None = no name filter


@dataclass
class ProcessInfo:
    """One row of the process table."""

    pid: int
    ppid: int
    threads: int
    name: str
    category: str = ""  # 'App', 'Background' or 'System'
    cpu_percent: float | None = None  # share of total CPU
    mem_percent: float | None = None  # working set / total RAM
    hung: bool = False  # reported not responding by Windows



# ============================================================
# Argument parsing
# ============================================================

def _parse_count(value: str) -> int:
    """Parse the value of '-n=<count>'."""

    try:
        count = int(value)
    except ValueError:
        raise ShellError(
            f"invalid value for '-n': '{value}' "
            f"(expected a positive integer)"
        ) from None

    if count < 1:
        raise ShellError(
            f"'-n' must be a positive integer (got {count})"
        )

    return count


def _parse_boolean(value: str) -> bool:
    """Parse the value of '-rt=<true|false>'."""

    result = _BOOLEAN_VALUES.get(value.lower())

    if result is None:
        raise ShellError(
            f"invalid value for '-rt': '{value}' "
            f"(expected 'true' or 'false')"
        )

    return result


def parse_ps_options(args: list[str]) -> PsOptions:
    """
    Parse command arguments into PsOptions.

    Options are matched by exact key (never by prefix):

        -a          boolean flag
        -n=<count>  row limit
        -rt=<bool>  realtime toggle
    """

    options = PsOptions()

    for arg in args:
        if not arg or arg[0] != "-":
            raise ShellError(f"unexpected argument '{arg}'")

        if arg == "-a":
            options.show_all = True
            continue

        key, sep, value = arg.partition("=")

        if key == "-n":
            if not sep:
                raise ShellError(
                    "option '-n' requires a value (use -n=<count>)"
                )
            options.limit = _parse_count(value)

        elif key == "-rt":
            if not sep:
                raise ShellError(
                    "option '-rt' requires a value (use -rt=<true|false>)"
                )
            options.realtime = _parse_boolean(value)

        elif key == "-sort":
            if not sep:
                raise ShellError(
                    "option '-sort' requires a value "
                    "(use -sort=<cpu|mem|pid|ppid|threads|name>)"
                )
            options.sort_key = _parse_sort_key(value)

        elif key == "-name":
            if not sep:
                raise ShellError(
                    "option '-name' requires a value (use -name=<pattern>)"
                )
            options.filter_name = value

        else:
            raise ShellError(f"unknown option '{arg}'")

    return options


def classify_process(
    process: ProcessInfo,
    app_pids: set[int],
) -> str:
    """
    Classify one process as 'App', 'Background' or 'System'.

    - System: kernel/idle pseudo-processes and well-known system
      process names (services host, session manager, ...).
    - App: owns at least one visible top-level window.
    - Background: everything else.
    """

    if process.pid <= 4 or process.name.lower() in _SYSTEM_PROCESS_NAMES:
        return "System"

    if process.pid in app_pids:
        return "App"

    return "Background"


_BOOLEAN_VALUES = {
    "true": True,
    "false": False,
}

_SORT_KEYS = {
    "cpu": lambda p: -(p.cpu_percent or 0.0),
    "mem": lambda p: -(p.mem_percent or 0.0),
    "pid": lambda p: p.pid,
    "ppid": lambda p: p.ppid,
    "threads": lambda p: p.threads,
    "name": lambda p: p.name.lower(),
}


def _parse_sort_key(value: str) -> str:
    """Parse the value of '-sort=<key>'."""

    key = value.lower()

    if key not in _SORT_KEYS:
        raise ShellError(
            f"invalid value for '-sort': '{value}' "
            f"(expected one of: {', '.join(_SORT_KEYS)})"
        )

    return key

# ============================================================
# Process enumeration (Windows)
# ============================================================

def get_window_pids() -> tuple[set[int], set[int]]:
    """
    Collect window-owner PIDs in one single EnumWindows pass.

    Returns (app_pids, hung_pids):

    app_pids  : PIDs owning a visible top-level window
                (tells regular apps from background processes)
    hung_pids : PIDs Windows reports as not responding
                (IsHungAppWindow)
    """

    app_pids: set[int] = set()
    hung_pids: set[int] = set()

    process_id = wintypes.DWORD()

    def _on_window(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id),
            )

            pid = process_id.value

            if pid:
                app_pids.add(pid)

                if user32.IsHungAppWindow(hwnd):
                    hung_pids.add(pid)

        return True

    user32.EnumWindows(WNDENUMPROC(_on_window), 0)
    return app_pids, hung_pids


def enumerate_processes() -> list[ProcessInfo]:
    """Snapshot the running processes."""

    processes: list[ProcessInfo] = []

    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPPROCESS,
        0,
    )

    if snapshot == INVALID_HANDLE_VALUE:
        raise ShellError(
            "cannot snapshot the process list "
            f"(Windows error {ctypes.get_last_error()})"
        )

    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

        success = kernel32.Process32FirstW(
            snapshot,
            ctypes.byref(entry),
        )

        while success:
            processes.append(
                ProcessInfo(
                    pid=entry.th32ProcessID,
                    ppid=entry.th32ParentProcessID,
                    threads=entry.cntThreads,
                    name=entry.szExeFile,
                )
            )

            success = kernel32.Process32NextW(
                snapshot,
                ctypes.byref(entry),
            )

    finally:
        kernel32.CloseHandle(snapshot)

    return processes


def apply_limit(
    processes: list[ProcessInfo],
    limit: int | None,
) -> list[ProcessInfo]:
    """Keep at most `limit` rows (all rows when limit is None)."""

    if limit is None:
        return processes

    return processes[:limit]


# ============================================================
# Process metrics (CPU / memory)
# ============================================================

def get_total_memory() -> int:
    """Total physical RAM in bytes (0 when unavailable)."""

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0

    return int(status.ullTotalPhys)


def get_process_stats(
    pid: int,
) -> tuple[tuple[float, float] | None, int | None]:
    """
    Read (cpu_times, working_set) for one process.

    cpu_times   : (kernel_time, user_time) in seconds, or None
    working_set : bytes, or None

    Both are None when the process cannot be opened (access denied
    or already exited).
    """

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )

    if not handle:
        return None, None

    try:
        creation = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()

        cpu_times = None

        if kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exited),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            def to_seconds(ft: wintypes.FILETIME) -> float:
                value = (ft.dwHighDateTime << 32) | ft.dwLowDateTime
                return value / 10_000_000

            cpu_times = (
                to_seconds(kernel_time),
                to_seconds(user_time),
            )

        working_set = None

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

        if psapi.GetProcessMemoryInfo(
            handle,
            ctypes.byref(counters),
            ctypes.sizeof(PROCESS_MEMORY_COUNTERS),
        ):
            working_set = int(counters.WorkingSetSize)

        return cpu_times, working_set

    finally:
        kernel32.CloseHandle(handle)


class ProcessMetrics:
    """
    Tracks per-process CPU-time samples between two passes and
    converts the deltas into CPU percentages (share of total CPU).

    The first pass establishes the baseline (CPU% = 0.0); every
    following pass measures since the previous one.
    """

    def __init__(self) -> None:
        # pid -> (kernel_time, user_time, monotonic_time)
        self._previous: dict[int, tuple[float, float, float]] = {}

    def update(
        self,
        processes: list[ProcessInfo],
        total_memory: int,
    ) -> None:
        """Fill MEM% now and CPU% since the previous pass."""

        now = time.monotonic()

        current: dict[int, tuple[float, float]] = {}

        for process in processes:
            cpu_times, working_set = get_process_stats(process.pid)

            if working_set is not None and total_memory > 0:
                process.mem_percent = (
                    working_set / total_memory * 100
                )

            if cpu_times is None:
                continue

            current[process.pid] = cpu_times

            previous = self._previous.get(process.pid)

            if previous is None or now <= previous[2]:
                process.cpu_percent = 0.0
                continue

            elapsed = now - previous[2]

            delta = (
                (cpu_times[0] - previous[0])
                + (cpu_times[1] - previous[1])
            )

            process.cpu_percent = max(
                0.0,
                min(100.0, delta / (elapsed * _CPU_COUNT) * 100),
            )

        self._previous = {
            pid: (kernel, user, now)
            for pid, (kernel, user) in current.items()
        }




# ============================================================
# Formatting
# ============================================================

# ANSI attributes (applied only on a real terminal).
_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_CYAN = "\033[36m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RED = "\033[31m"
_ANSI_GREEN = "\033[32m"
_ANSI_GRAY = "\033[90m"

_TYPE_COLORS = {
    "App": _ANSI_GREEN,
    "Background": _ANSI_GRAY,
    "System": _ANSI_GRAY,
}


def _paint(text: str, color: str | None) -> str:
    """Wrap an already-padded cell in a color code (zero-width)."""

    if not color:
        return text

    return f"{color}{text}{_ANSI_RESET}"


def _format_name(name: str) -> str:
    if len(name) > _NAME_WIDTH:
        return name[:_NAME_WIDTH - 3] + "..."

    return name


def _format_percent(value: float | None, color: str | None = None) -> str:
    if value is None:
        return "-".rjust(_PERCENT_WIDTH)

    text = f"{value:>{_PERCENT_WIDTH - 1}.1f}%"

    return _paint(text, color) if color else text


def _build_row(process: ProcessInfo, colors: bool) -> str:
    """One table row; colors wrap already-padded cells."""

    pid_cell = f"{process.pid:<8}"
    if colors:
        pid_cell = _paint(pid_cell, _ANSI_CYAN)

    cpu_color = None
    if (
        colors
        and process.cpu_percent is not None
        and process.cpu_percent >= _CPU_HIGH_THRESHOLD
    ):
        cpu_color = _ANSI_YELLOW

    mem_color = None
    if colors and process.mem_percent is not None:
        if process.mem_percent >= _MEM_CRITICAL_THRESHOLD:
            mem_color = _ANSI_RED
        elif process.mem_percent >= _MEM_WARN_THRESHOLD:
            mem_color = _ANSI_YELLOW

    type_color = _TYPE_COLORS.get(process.category) if colors else None

    return (
        f"{pid_cell} "
        f"{process.ppid:<8} "
        f"{process.threads:<8} "
        f"{_format_percent(process.cpu_percent, cpu_color)} "
        f"{_format_percent(process.mem_percent, mem_color)} "
        f"{_paint(process.category.ljust(_TYPE_WIDTH), type_color)} "
        f"{_format_name(process.name)}"
    )


def format_table(
    processes: list[ProcessInfo],
    colors: bool = False,
) -> str:
    """
    Render the process table.

    The header/separator layout is the one `grep` recognizes for
    `ps | grep <pattern>` (header starts with 'PID' and contains
    'NAME'; the separator is dashes only). Colors wrap already
    padded cells, so they never break the column alignment, and
    they are only enabled on a real terminal.
    """

    header = (
        f"{'PID':<8} "
        f"{'PPID':<8} "
        f"{'THREADS':<8} "
        f"{'CPU%':>{_PERCENT_WIDTH}} "
        f"{'MEM%':>{_PERCENT_WIDTH}} "
        f"{'TYPE'.ljust(_TYPE_WIDTH)} "
        f"{'NAME'}"
    )

    if colors:
        header = f"{_ANSI_BOLD}{header}{_ANSI_RESET}"

    separator = "-" * (
        8 + 1 + 8 + 1 + 8 + 1
        + _PERCENT_WIDTH + 1 + _PERCENT_WIDTH + 1
        + _TYPE_WIDTH + 1 + _NAME_WIDTH
    )

    rows: list[str] = []

    for process in processes:
        if colors and process.hung:
            # A process with problems / candidate for `kill`:
            # the whole row goes red.
            rows.append(
                _paint(_build_row(process, colors=False), _ANSI_RED)
            )
        else:
            rows.append(_build_row(process, colors))

    return "\n".join([header, separator, *rows])


# ============================================================
# Realtime mode
# ============================================================

def _live_sort_key(process: ProcessInfo):
    """Live dashboard order: busiest processes first."""

    return (
        -(process.cpu_percent or 0.0),
        -(process.mem_percent or 0.0),
        process.pid,
    )


def _live_max_rows(limit: int | None) -> int:
    """
    Rows the live dashboard may show.

    The whole frame must fit inside the terminal window, so the
    in-place redraw never adds a single line: the terminal never
    scrolls, the mouse-wheel position and the scrollback history
    stay untouched.
    """

    try:
        lines = shutil.get_terminal_size().lines
    except Exception:
        lines = 24

    max_rows = max(
        1,
        min(_LIVE_MAX_ROWS, lines - _LIVE_ROW_RESERVE),
    )

    if limit is not None:
        max_rows = min(max_rows, limit)

    return max_rows


def _enable_ansi_console() -> None:
    """
    Best-effort enablement of ANSI escape sequences on the Windows
    console. Never raises (older consoles simply stay as they are).
    """

    try:
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        mode = wintypes.DWORD()

        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(
                handle,
                mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
            )

    except Exception:
        pass


def run_realtime(build_table: Callable[[], str]) -> str:
    """
    Live view: redraw the table in place every REFRESH_INTERVAL
    seconds until interrupted with Ctrl+C.

    The cursor is rewound over the previous table and the screen is
    cleared downwards before each refresh, so nothing accumulates
    and nothing scrolls -- it just stays real time.

    When stdout is captured (pipeline or redirection) a live view
    is impossible, so a single snapshot is rendered instead.
    """

    if not sys.stdout.isatty():
        return build_table()

    _enable_ansi_console()

    try:
        while True:
            table = build_table()

            print(table, flush=True)
            time.sleep(REFRESH_INTERVAL)

            # Rewind the cursor to the top of the table and clear
            # downwards, so the next refresh redraws in place.
            lines = table.count("\n") + 1

            print(
                f"\033[{lines}F\033[J",
                end="",
                flush=True,
            )

    except KeyboardInterrupt:
        pass

    return ""


# ============================================================
# Command
# ============================================================

def cmd_ps(args: list[str]) -> str:
    """
    Execute `ps`.

    Executor contract:

        handler(args)

    Flow: parse options -> enumerate -> measure metrics ->
    classify -> filter -> format -> return the table string
    (pipeline-safe).
    """

    options = parse_ps_options(args)
    metrics = ProcessMetrics()

    def collect() -> list[ProcessInfo]:
        """One sampling pass: enumerate, measure, classify, filter."""

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

        # Default view: apps + background processes only.
        # `-a` includes system processes as well.
        if not options.show_all:
            processes = [
                p for p in processes if p.category != "System"
            ]

        # `-name=<pattern>`: substring filter on the process name.
        if options.filter_name:
            pattern = options.filter_name.lower()
            processes = [
                p for p in processes
                if pattern in p.name.lower()
            ]

        return processes

    # Colors only when output goes straight to the terminal;
    # piped/redirected output stays plain (grep-friendly).
    use_colors = sys.stdout.isatty()

    if options.realtime:
        # Live dashboard: busiest processes first (or `-sort=` order),
        # capped to what fits on screen so the redraw never scrolls
        # the terminal.
        max_rows = _live_max_rows(options.limit)

        def build_table() -> str:
            processes = collect()

            if options.sort_key is not None:
                processes.sort(key=_SORT_KEYS[options.sort_key])
            else:
                processes.sort(key=_live_sort_key)

            return format_table(
                processes[:max_rows],
                colors=use_colors,
            )

        return run_realtime(build_table)

    # One-shot: full grouped table. Take a baseline pass, wait a
    # short interval, then measure, so CPU% reflects real activity
    # instead of 0.00.
    if use_colors:
        _enable_ansi_console()

    collect()
    time.sleep(CPU_SAMPLE_INTERVAL)
    processes = collect()

    if options.sort_key is not None:
        processes.sort(key=_SORT_KEYS[options.sort_key])
    else:
        processes.sort(
            key=lambda p: (_CATEGORY_ORDER.get(p.category, 9), p.pid)
        )

    return format_table(
        apply_limit(processes, options.limit),
        colors=use_colors,
    )


def man_ps() -> str:
    return """PS(1)                    Midnight Terminal Manual                   PS(1)

NAME
    ps - list the running Windows processes

SYNOPSIS
    ps
    ps -a
    ps -n=<count>
    ps -rt=true
    ps -sort=<key>
    ps -name=<pattern>

DESCRIPTION
    Lists the running Windows processes as a table, grouped into
    apps, background processes and system processes:

        PID      PPID     THREADS     CPU%    MEM% TYPE         NAME

    By default only apps and background processes are shown; `-a`
    includes system processes as well.

OPTIONS

    -a           include system processes as well
    -n=<count>   limit the table to <count> rows
    -rt=true     realtime mode: live dashboard of the busiest
                 processes, redrawn in place every second until
                 interrupted with Ctrl+C
    -rt=false    one-shot mode (default)
    -sort=<key>  sort rows by cpu|mem|pid|ppid|threads|name
    -name=<pat>  only show processes whose name contains <pat>

BEHAVIOR NOTES

    - CPU% is the share of total CPU; MEM% is the process working
      set relative to total physical RAM. '-' means unavailable.
    - Processes reported as not responding are shown in red -- they
      are candidates for `kill`.
    - Output is pipeline-friendly (`ps | grep python` keeps the
      table header); colors are only used on a real terminal.

SEE ALSO
    top(1), task(1), kill(1)
"""