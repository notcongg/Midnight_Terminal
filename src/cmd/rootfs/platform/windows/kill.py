
"""
Midnight Terminal - kill command.

Usage:

    kill 4216
    kill -p=4216
    kill --pid=4216

Terminates a Windows process by PID.

Windows-only.
"""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

ERROR_STILL_ACTIVE = 259  # STILL_ACTIVE exit code


# ============================================================
# Windows DLL
# ============================================================

kernel32 = ctypes.WinDLL(
    "kernel32",
    use_last_error=True,
)


# ============================================================
# Constants
# ============================================================

TH32CS_SNAPPROCESS = 0x00000002

PROCESS_TERMINATE = 0x0001

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

ERROR_ACCESS_DENIED = 5

ERROR_INVALID_PARAMETER = 87


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


kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]

kernel32.OpenProcess.restype = wintypes.HANDLE


kernel32.TerminateProcess.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
]

kernel32.TerminateProcess.restype = wintypes.BOOL


kernel32.CloseHandle.argtypes = [
    wintypes.HANDLE,
]

kernel32.CloseHandle.restype = wintypes.BOOL


kernel32.GetExitCodeProcess.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.DWORD),
]

kernel32.GetExitCodeProcess.restype = wintypes.BOOL


# ------------------------------------------------------------
# Window API (graceful close support)
# ------------------------------------------------------------

user32 = ctypes.WinDLL(
    "user32",
    use_last_error=True,
)

WM_CLOSE = 0x0010

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

user32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.PostMessageW.restype = wintypes.BOOL

GRACEFUL_CLOSE_TIMEOUT = 2.0  # seconds to wait after WM_CLOSE


# ============================================================
# Helpers
# ============================================================

def parse_pid(
    args: list[str],
) -> int | None:
    """
    Parse PID from command arguments.

    Supported:

        kill 208
        kill -p=208
        kill --pid=208
    """

    if not args:
        print(
            "[ERROR] Missing process ID."
        )
        print(
            "Usage: kill <pid>"
        )
        return None

    if len(args) > 1:
        print(
            "[ERROR] Too many arguments."
        )
        print(
            "Usage: kill <pid>"
        )
        return None

    value = args[0].strip()

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

    if pid <= 0:
        print(
            f"[ERROR] Invalid PID: {pid}"
        )
        return None

    return pid


def find_process(
    pid: int,
) -> str | None:
    """
    Find process name by PID.

    Returns:
        Process executable name or None.
    """

    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPPROCESS,
        0,
    )

    invalid_handle = ctypes.c_void_p(
        -1
    ).value

    if snapshot == invalid_handle:
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
                return entry.szExeFile

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
# Graceful close helpers
# ============================================================

def get_window_handles(
    pid: int,
) -> list:
    """
    Collect the visible top-level window handles owned by a PID
    (empty list for console/background processes).
    """

    handles: list = []

    process_id = wintypes.DWORD()

    def _on_window(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id),
            )

            if process_id.value == pid:
                handles.append(hwnd)

        return True

    user32.EnumWindows(WNDENUMPROC(_on_window), 0)
    return handles


def is_process_alive(pid: int) -> bool:
    """True while the process exists and has not exited."""

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )

    if not handle:
        return False

    try:
        exit_code = wintypes.DWORD()

        if not kernel32.GetExitCodeProcess(
            handle,
            ctypes.byref(exit_code),
        ):
            return False

        return exit_code.value == ERROR_STILL_ACTIVE

    finally:
        kernel32.CloseHandle(handle)


def graceful_close(
    pid: int,
) -> bool:
    """
    Ask the process to close politely: post WM_CLOSE to its visible
    windows, then wait briefly for it to exit.

    Returns True when the process exited gracefully.
    """

    handles = get_window_handles(pid)

    if not handles:
        return False

    for handle in handles:
        user32.PostMessageW(handle, WM_CLOSE, 0, 0)

    deadline = time.monotonic() + GRACEFUL_CLOSE_TIMEOUT

    while time.monotonic() < deadline:
        if not is_process_alive(pid):
            return True

        time.sleep(0.1)

    return False

def cmd_kill(
    args: list[str],
) -> None:
    """
    Execute kill command.

    Executor contract:

        handler(args)

    Options:

        kill <pid>      graceful close (WM_CLOSE), then force
        kill -f <pid>   force termination immediately
    """

    force = False
    pid_args: list[str] = []

    for arg in args:
        if arg in ("-f", "--force"):
            force = True
        else:
            pid_args.append(arg)

    pid = parse_pid(
        pid_args
    )

    if pid is None:
        return

    # --------------------------------------------------------
    # Check that PID exists
    # --------------------------------------------------------

    process_name = find_process(
        pid
    )

    if process_name is None:
        print(
            f"[ERROR] Process {pid} not found."
        )
        return

    # --------------------------------------------------------
    # Graceful close first (unless forced)
    # --------------------------------------------------------

    if not force and graceful_close(pid):
        print(
            f"[OK] Closed "
            f"{process_name} "
            f"(PID {pid})."
        )
        return

    # --------------------------------------------------------
    # Open with BOTH terminate + query permissions
    # --------------------------------------------------------

    access = (
        PROCESS_TERMINATE
        | PROCESS_QUERY_LIMITED_INFORMATION
    )

    handle = kernel32.OpenProcess(
        access,
        False,
        pid,
    )

    if not handle:

        error = ctypes.get_last_error()

        if error == ERROR_ACCESS_DENIED:
            print(
                f"[ERROR] Access denied for "
                f"process {pid}."
            )
        else:
            print(
                f"[ERROR] Cannot open process "
                f"{pid} "
                f"(Windows error {error})."
            )

        return

    try:

        # ----------------------------------------------------
        # Terminate directly.
        #
        # Do NOT call GetExitCodeProcess first.
        # ----------------------------------------------------

        success = kernel32.TerminateProcess(
            handle,
            1,
        )

        if not success:

            error = ctypes.get_last_error()

            if error == ERROR_ACCESS_DENIED:
                print(
                    f"[ERROR] Access denied while "
                    f"terminating process {pid}."
                )

            elif error == ERROR_INVALID_PARAMETER:
                print(
                    f"[ERROR] Process {pid} "
                    f"no longer exists."
                )

            else:
                print(
                    f"[ERROR] Failed to terminate "
                    f"process {pid} "
                    f"(Windows error {error})."
                )

            return

        print(
            f"[OK] Terminated "
            f"{process_name} "
            f"(PID {pid})."
        )

    finally:

        kernel32.CloseHandle(
            handle
        )
