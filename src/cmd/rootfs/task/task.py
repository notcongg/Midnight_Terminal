
"""
Midnight Terminal - task command.

Usage:

    task 4216
    task -p=4216
    task --pid=4216

Displays detailed information about a Windows process.

Windows-only.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes


# ============================================================
# Windows DLLs
# ============================================================

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True,
)

psapi = ctypes.WinDLL(
    "psapi",
    use_last_error=True,
)


# ============================================================
# Constants
# ============================================================

TH32CS_SNAPPROCESS = 0x00000002

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010

MAX_PATH = 260
STILL_ACTIVE = 259


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
        ("szExeFile", wintypes.WCHAR * MAX_PATH),
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
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


# ============================================================
# Process API definitions
# ============================================================

kernel32.CreateToolhelp32Snapshot.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
]

kernel32.CreateToolhelp32Snapshot.restype = (
    wintypes.HANDLE
)


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


kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]

kernel32.OpenProcess.restype = wintypes.HANDLE


kernel32.GetExitCodeProcess.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.DWORD),
]

kernel32.GetExitCodeProcess.restype = wintypes.BOOL


kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE,
]

kernel32.CloseHandle.restype = wintypes.BOOL


# ============================================================
# Memory API definitions
# ============================================================

psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]

psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


# ============================================================
# Helpers
# ============================================================

def format_memory(
    value: int | None,
) -> str:
    """
    Convert bytes into human-readable memory.

    Returns:
        N/A when memory cannot be queried.
    """

    if value is None:
        return "N/A"

    if value < 1024:
        return f"{value} B"

    if value < 1024 ** 2:
        return f"{value / 1024:.1f} KB"

    if value < 1024 ** 3:
        return f"{value / (1024 ** 2):.1f} MB"

    return f"{value / (1024 ** 3):.2f} GB"


def parse_pid(
    args: list[str],
) -> int | None:
    """
    Parse PID from command arguments.

    Supported:

        task 208
        task -p=208
        task --pid=208
    """

    if not args:
        print(
            "[ERROR] Missing process ID."
        )
        print(
            "Usage: task <pid>"
        )
        return None

    if len(args) > 1:
        print(
            "[ERROR] Too many arguments."
        )
        print(
            "Usage: task <pid>"
        )
        return None

    value = args[0]

    if value.startswith("--pid="):
        value = value[len("--pid="):]

    elif value.startswith("-p="):
        value = value[len("-p="):]

    elif value.startswith("-"):
        print(
            f"[ERROR] Unknown option: {value}"
        )
        return None

    if not value:
        print(
            "[ERROR] Missing process ID."
        )
        return None

    try:
        pid = int(value)

    except ValueError:
        print(
            f"[ERROR] Invalid PID: {value}"
        )
        return None

    if pid < 0:
        print(
            f"[ERROR] Invalid PID: {pid}"
        )
        return None

    return pid


# ============================================================
# Process lookup
# ============================================================

def find_process(
    pid: int,
) -> dict | None:
    """
    Find a process using Tool Help API.
    """

    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPPROCESS,
        0,
    )

    if snapshot == INVALID_HANDLE_VALUE:
        return None

    try:

        entry = PROCESSENTRY32W()

        entry.dwSize = ctypes.sizeof(
            PROCESSENTRY32W
        )

        success = kernel32.Process32FirstW(
            snapshot,
            ctypes.byref(entry),
        )

        if not success:
            return None

        while success:

            if entry.th32ProcessID == pid:

                return {
                    "pid": entry.th32ProcessID,
                    "name": entry.szExeFile,
                    "parent_pid": entry.th32ParentProcessID,
                    "threads": entry.cntThreads,
                }

            success = kernel32.Process32NextW(
                snapshot,
                ctypes.byref(entry),
            )

    finally:

        kernel32.CloseHandle(
            snapshot
        )

    return None


# ============================================================
# Process access
# ============================================================

def open_process(pid: int):
    """
    Open process with query permissions.
    """

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
        False,
        pid,
    )

    if handle:
        return handle

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )

    if handle:
        return handle

    return None


# ============================================================
# Process status
# ============================================================

def get_process_status(
    handle,
) -> str:
    """
    Get process status.
    """

    exit_code = wintypes.DWORD()

    success = kernel32.GetExitCodeProcess(
        handle,
        ctypes.byref(exit_code),
    )

    if not success:
        return "Unknown"

    if exit_code.value == STILL_ACTIVE:
        return "Running"

    return f"Exited ({exit_code.value})"


# ============================================================
# Memory
# ============================================================

def get_memory(
    handle,
) -> int | None:
    """
    Get working-set memory.

    Returns:
        bytes or None when unavailable.
    """

    counters = PROCESS_MEMORY_COUNTERS()

    counters.cb = ctypes.sizeof(
        PROCESS_MEMORY_COUNTERS
    )

    success = psapi.GetProcessMemoryInfo(
        handle,
        ctypes.byref(counters),
        ctypes.sizeof(counters),
    )

    if not success:
        return None

    return counters.WorkingSetSize


# ============================================================
# Command
# ============================================================

def cmd_task(
    args: list[str],
) -> None:
    """
    Execute `task`.

    IMPORTANT:

    Midnight executor calls commands like:

        handler(args)

    therefore `args` is always a list[str].
    """

    # --------------------------------------------------------
    # Parse arguments
    # --------------------------------------------------------

    pid = parse_pid(
        args
    )

    if pid is None:
        return

    # --------------------------------------------------------
    # Find process
    # --------------------------------------------------------

    process = find_process(
        pid
    )

    if process is None:
        print(
            f"[ERROR] Process {pid} not found."
        )
        return

    # --------------------------------------------------------
    # Open process
    # --------------------------------------------------------

    handle = open_process(
        pid
    )

    if not handle:

        error = ctypes.get_last_error()

        print(
            f"[ERROR] Cannot access process {pid} "
            f"(Windows error {error})."
        )

        return

    try:

        # ----------------------------------------------------
        # Collect information
        # ----------------------------------------------------

        memory = get_memory(
            handle
        )

        status = get_process_status(
            handle
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print(
            "Process Information"
        )

        print(
            "─" * 40
        )

        print(
            f"{'PID':<12}: "
            f"{process['pid']}"
        )

        print(
            f"{'Name':<12}: "
            f"{process['name']}"
        )

        print(
            f"{'Parent PID':<12}: "
            f"{process['parent_pid']}"
        )

        print(
            f"{'Threads':<12}: "
            f"{process['threads']}"
        )

        print(
            f"{'Memory':<12}: "
            f"{format_memory(memory)}"
        )

        print(
            f"{'Status':<12}: "
            f"{status}"
        )

    finally:

        kernel32.CloseHandle(
            handle
        )
