from __future__ import annotations

import ctypes
from ctypes import wintypes


# ============================================================
# Win32 Constants
# ============================================================

DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
DISPLAY_DEVICE_MIRRORING_DRIVER = 0x00000008

ENUM_CURRENT_SETTINGS = 0xFFFFFFFF

ERROR_INVALID_FUNCTION = 1

# GUID used by GetFirmwareEnvironmentVariableW to test UEFI.
EFI_GLOBAL_VARIABLE_GUID = "{00000000-0000-0000-0000-000000000000}"


# ============================================================
# Win32 Structures
# ============================================================

class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),

        ("dmPositionX", wintypes.LONG),
        ("dmPositionY", wintypes.LONG),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),

        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),

        ("dmFormName", wintypes.WCHAR * 32),

        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),

        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),

        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


# ============================================================
# Win32 API Setup
# ============================================================

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


_user32.EnumDisplayDevicesW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.POINTER(DISPLAY_DEVICEW),
    wintypes.DWORD,
]

_user32.EnumDisplayDevicesW.restype = wintypes.BOOL


_user32.EnumDisplaySettingsW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.POINTER(DEVMODEW),
]

_user32.EnumDisplaySettingsW.restype = wintypes.BOOL


_kernel32.GetFirmwareEnvironmentVariableW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.LPVOID,
    wintypes.DWORD,
]

_kernel32.GetFirmwareEnvironmentVariableW.restype = wintypes.DWORD


# ============================================================
# Display Enumeration
# ============================================================

def enum_display_devices(
    device_name: str | None = None,
    max_devices: int = 64,
) -> list[DISPLAY_DEVICEW]:
    """
    Enumerate Windows display devices.

    Args:
        device_name:
            None to enumerate display adapters.
            A device name such as '\\\\.\\DISPLAY1'
            to enumerate monitors attached to that adapter.

        max_devices:
            Defensive upper bound for enumeration.

    Returns:
        A list of DISPLAY_DEVICEW structures.
    """

    devices: list[DISPLAY_DEVICEW] = []

    for index in range(max_devices):
        device = DISPLAY_DEVICEW()
        device.cb = ctypes.sizeof(DISPLAY_DEVICEW)

        success = _user32.EnumDisplayDevicesW(
            device_name,
            index,
            ctypes.byref(device),
            0,
        )

        if not success:
            break

        devices.append(device)

    return devices


def enum_active_display_adapters() -> list[DISPLAY_DEVICEW]:
    """
    Return display adapters currently attached to the desktop.

    Mirroring drivers are excluded.
    """

    adapters: list[DISPLAY_DEVICEW] = []

    for device in enum_display_devices():
        if not (
            device.StateFlags
            & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
        ):
            continue

        if device.StateFlags & DISPLAY_DEVICE_MIRRORING_DRIVER:
            continue

        adapters.append(device)

    return adapters


def enum_active_monitors(
    adapter_name: str,
) -> list[DISPLAY_DEVICEW]:
    """
    Return active physical monitors attached to a display adapter.
    """

    monitors: list[DISPLAY_DEVICEW] = []

    for device in enum_display_devices(
        adapter_name,
        max_devices=16,
    ):
        if not (
            device.StateFlags
            & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
        ):
            continue

        if device.StateFlags & DISPLAY_DEVICE_MIRRORING_DRIVER:
            continue

        monitors.append(device)

    return monitors


# ============================================================
# Current Display Settings
# ============================================================

def get_current_display_settings(
    device_name: str,
) -> DEVMODEW | None:
    """
    Get the current display mode for a Windows display device.
    """

    mode = DEVMODEW()
    mode.dmSize = ctypes.sizeof(DEVMODEW)

    success = _user32.EnumDisplaySettingsW(
        device_name,
        ENUM_CURRENT_SETTINGS,
        ctypes.byref(mode),
    )

    if not success:
        return None

    return mode


# ============================================================
# UEFI Detection
# ============================================================

def is_uefi() -> bool | None:
    """
    Detect whether Windows was booted using UEFI.

    Returns:
        True:
            UEFI boot.

        False:
            Legacy BIOS / CSM.

        None:
            Detection failed.
    """

    ctypes.set_last_error(0)

    _kernel32.GetFirmwareEnvironmentVariableW(
        "",
        EFI_GLOBAL_VARIABLE_GUID,
        None,
        0,
    )

    error = ctypes.get_last_error()

    if error == ERROR_INVALID_FUNCTION:
        return False

    if error == 0:
        return True

    return None


# ============================================================
# Helper Functions
# ============================================================

def get_device_id_key(device_id: str) -> str | None:
    """
    Extract the hardware identifier key used to match
    a Win32 display device against WMI WmiMonitorID data.

    Example:

        DISPLAY\\DELA1234\\...
                    ^^^^^^^^

    Returns:
        The identifier portion or None if unavailable.
    """

    if not device_id:
        return None

    parts = device_id.upper().split("\\")

    if len(parts) < 2:
        return None

    return parts[1]


def get_display_resolution(
    device_name: str,
) -> tuple[int, int] | None:
    """
    Return the current display resolution.
    """

    mode = get_current_display_settings(device_name)

    if mode is None:
        return None

    return (
        int(mode.dmPelsWidth),
        int(mode.dmPelsHeight),
    )


def get_display_refresh_rate(
    device_name: str,
) -> int | None:
    """
    Return the current display refresh rate in Hz.
    """

    mode = get_current_display_settings(device_name)

    if mode is None:
        return None

    refresh_rate = int(mode.dmDisplayFrequency)

    if refresh_rate <= 1:
        return None

    return refresh_rate
