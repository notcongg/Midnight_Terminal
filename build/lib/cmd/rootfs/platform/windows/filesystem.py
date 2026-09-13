# ============================================================
# platform/windows/filesystem.py
# ============================================================

import ctypes
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

ULONG_PTR = ctypes.c_size_t
LARGE_INTEGER = ctypes.c_longlong
ULARGE_INTEGER = ctypes.c_ulonglong


# ------------------------------------------------------------
# GetFileAttributesW / GetFileAttributesExW
# ------------------------------------------------------------

INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

GetFileExInfoStandard = 0


class WIN32_FILE_ATTRIBUTE_DATA(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
    ]


GetFileAttributesW = kernel32.GetFileAttributesW
GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
GetFileAttributesW.restype = wintypes.DWORD

GetFileAttributesExW = kernel32.GetFileAttributesExW
GetFileAttributesExW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.c_int,
    wintypes.LPVOID,
]
GetFileAttributesExW.restype = wintypes.BOOL


# ------------------------------------------------------------
# GetFullPathNameW / GetLongPathNameW / GetShortPathNameW
# ------------------------------------------------------------

GetFullPathNameW = kernel32.GetFullPathNameW
GetFullPathNameW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.LPWSTR),
]
GetFullPathNameW.restype = wintypes.DWORD


GetLongPathNameW = kernel32.GetLongPathNameW
GetLongPathNameW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetLongPathNameW.restype = wintypes.DWORD


GetShortPathNameW = kernel32.GetShortPathNameW
GetShortPathNameW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetShortPathNameW.restype = wintypes.DWORD


# ------------------------------------------------------------
# GetFinalPathNameByHandleW
# ------------------------------------------------------------

FILE_NAME_NORMALIZED = 0x0
FILE_NAME_OPENED = 0x8

VOLUME_NAME_DOS = 0x0
VOLUME_NAME_GUID = 0x1
VOLUME_NAME_NT = 0x2
VOLUME_NAME_NONE = 0x4

GetFinalPathNameByHandleW = kernel32.GetFinalPathNameByHandleW
GetFinalPathNameByHandleW.argtypes = [
    wintypes.HANDLE,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
]
GetFinalPathNameByHandleW.restype = wintypes.DWORD


# ------------------------------------------------------------
# GetFileInformationByHandle
# ------------------------------------------------------------

class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


GetFileInformationByHandle = kernel32.GetFileInformationByHandle
GetFileInformationByHandle.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(BY_HANDLE_FILE_INFORMATION),
]
GetFileInformationByHandle.restype = wintypes.BOOL


# ------------------------------------------------------------
# GetFileInformationByHandleEx + FILE_ID_INFO
# ------------------------------------------------------------

class FILE_INFO_BY_HANDLE_CLASS:
    FileBasicInfo = 0
    FileStandardInfo = 1
    FileNameInfo = 2
    FileRenameInfo = 3
    FileDispositionInfo = 4
    FileAllocationInfo = 5
    FileEndOfFileInfo = 6
    FileStreamInfo = 7
    FileCompressionInfo = 8
    FileAttributeTagInfo = 9
    FileIdBothDirectoryInfo = 10
    FileIdBothDirectoryRestartInfo = 11
    FileIoPriorityHintInfo = 12
    FileRemoteProtocolInfo = 13
    FileFullDirectoryInfo = 14
    FileFullDirectoryRestartInfo = 15
    FileStorageInfo = 16
    FileAlignmentInfo = 17
    FileIdInfo = 18
    FileIdExtdDirectoryInfo = 19
    FileIdExtdDirectoryRestartInfo = 20


class FILE_ID_128(ctypes.Structure):
    _fields_ = [
        ("Identifier", ctypes.c_byte * 16),
    ]


class FILE_ID_INFO(ctypes.Structure):
    _fields_ = [
        ("VolumeSerialNumber", ULARGE_INTEGER),
        ("FileId", FILE_ID_128),
    ]


class FILE_STANDARD_INFO(ctypes.Structure):
    _fields_ = [
        ("AllocationSize", LARGE_INTEGER),
        ("EndOfFile", LARGE_INTEGER),
        ("NumberOfLinks", wintypes.DWORD),
        ("DeletePending", wintypes.BOOLEAN),
        ("Directory", wintypes.BOOLEAN),
    ]


class FILE_BASIC_INFO(ctypes.Structure):
    _fields_ = [
        ("CreationTime", LARGE_INTEGER),
        ("LastAccessTime", LARGE_INTEGER),
        ("LastWriteTime", LARGE_INTEGER),
        ("ChangeTime", LARGE_INTEGER),
        ("FileAttributes", wintypes.DWORD),
    ]


GetFileInformationByHandleEx = kernel32.GetFileInformationByHandleEx
GetFileInformationByHandleEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    wintypes.LPVOID,
    wintypes.DWORD,
]
GetFileInformationByHandleEx.restype = wintypes.BOOL


# ------------------------------------------------------------
# Volume operations
# ------------------------------------------------------------

DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6

GetVolumeInformationW = kernel32.GetVolumeInformationW
GetVolumeInformationW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetVolumeInformationW.restype = wintypes.BOOL


GetVolumePathNameW = kernel32.GetVolumePathNameW
GetVolumePathNameW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
]
GetVolumePathNameW.restype = wintypes.BOOL


GetDriveTypeW = kernel32.GetDriveTypeW
GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
GetDriveTypeW.restype = wintypes.UINT


GetDiskFreeSpaceW = kernel32.GetDiskFreeSpaceW
GetDiskFreeSpaceW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
]
GetDiskFreeSpaceW.restype = wintypes.BOOL


GetDiskFreeSpaceExW = kernel32.GetDiskFreeSpaceExW
GetDiskFreeSpaceExW.argtypes = [
    wintypes.LPCWSTR,
    ctypes.POINTER(ULARGE_INTEGER),
    ctypes.POINTER(ULARGE_INTEGER),
    ctypes.POINTER(ULARGE_INTEGER),
]
GetDiskFreeSpaceExW.restype = wintypes.BOOL


# ------------------------------------------------------------
# Core operations: MoveFileExW / CopyFileExW
# ------------------------------------------------------------

MOVEFILE_REPLACE_EXISTING = 0x00000001
MOVEFILE_COPY_ALLOWED = 0x00000002
MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
MOVEFILE_WRITE_THROUGH = 0x00000008
MOVEFILE_CREATE_HARDLINK = 0x00000010
MOVEFILE_FAIL_IF_NOT_TRACKABLE = 0x00000020

MoveFileExW = kernel32.MoveFileExW
MoveFileExW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
]
MoveFileExW.restype = wintypes.BOOL


COPY_FILE_FAIL_IF_EXISTS = 0x00000001
COPY_FILE_RESTARTABLE = 0x00000002
COPY_FILE_OPEN_SOURCE_FOR_WRITE = 0x00000004
COPY_FILE_ALLOW_DECRYPTED_DESTINATION = 0x00000008
COPY_FILE_COPY_SYMLINK = 0x00000800
COPY_FILE_NO_BUFFERING = 0x00001000

LPPROGRESS_ROUTINE = ctypes.c_void_p

CopyFileExW = kernel32.CopyFileExW
CopyFileExW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    LPPROGRESS_ROUTINE,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.BOOL),
    wintypes.DWORD,
]
CopyFileExW.restype = wintypes.BOOL


DeleteFileW = kernel32.DeleteFileW
DeleteFileW.argtypes = [wintypes.LPCWSTR]
DeleteFileW.restype = wintypes.BOOL


# ------------------------------------------------------------
# Security: GetFileSecurityW / AccessCheck
# ------------------------------------------------------------

OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION = 0x00000004
SACL_SECURITY_INFORMATION = 0x00000008

PSID = wintypes.LPVOID
PACL = wintypes.LPVOID
PSECURITY_DESCRIPTOR = wintypes.LPVOID


class GENERIC_MAPPING(ctypes.Structure):
    _fields_ = [
        ("GenericRead", wintypes.DWORD),
        ("GenericWrite", wintypes.DWORD),
        ("GenericExecute", wintypes.DWORD),
        ("GenericAll", wintypes.DWORD),
    ]


class PRIVILEGE_SET(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Control", wintypes.DWORD),
        ("Privilege", wintypes.LARGE_INTEGER * 1),
    ]


GetFileSecurityW = advapi32.GetFileSecurityW
GetFileSecurityW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    PSECURITY_DESCRIPTOR,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
GetFileSecurityW.restype = wintypes.BOOL


AccessCheck = advapi32.AccessCheck
AccessCheck.argtypes = [
    PSECURITY_DESCRIPTOR,
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(GENERIC_MAPPING),
    ctypes.POINTER(PRIVILEGE_SET),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.BOOL),
]
AccessCheck.restype = wintypes.BOOL
