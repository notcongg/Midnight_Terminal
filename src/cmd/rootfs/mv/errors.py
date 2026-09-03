# ============================================================
# platform/windows/errors.py
# ============================================================

import ctypes
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


# ------------------------------------------------------------
# Error codes
# ------------------------------------------------------------

ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_ALREADY_EXISTS = 183
ERROR_SHARING_VIOLATION = 32
ERROR_NOT_SAME_DEVICE = 17
ERROR_WRITE_PROTECT = 19
ERROR_DISK_FULL = 112
ERROR_INVALID_NAME = 123
ERROR_DIRECTORY = 267


# ------------------------------------------------------------
# FormatMessageW flags
# ------------------------------------------------------------

FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

LANG_NEUTRAL = 0x00
SUBLANG_DEFAULT = 0x01


def MAKELANGID(primary, sub):
    return (sub << 10) | primary


# ------------------------------------------------------------
# GetLastError
# ------------------------------------------------------------

GetLastError = kernel32.GetLastError
GetLastError.argtypes = []
GetLastError.restype = wintypes.DWORD


SetLastError = kernel32.SetLastError
SetLastError.argtypes = [wintypes.DWORD]
SetLastError.restype = None


# ------------------------------------------------------------
# FormatMessageW
# ------------------------------------------------------------

FormatMessageW = kernel32.FormatMessageW
FormatMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.LPWSTR),
    wintypes.DWORD,
    wintypes.LPVOID,
]
FormatMessageW.restype = wintypes.DWORD


LocalFree = ctypes.windll.kernel32.LocalFree
LocalFree.argtypes = [wintypes.HLOCAL]
LocalFree.restype = wintypes.HLOCAL
