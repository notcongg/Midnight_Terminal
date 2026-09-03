from __future__ import annotations

from ..platform.win32 import is_uefi
from ..platform.wmi import get_system_wmi


def collect_mainboard() -> dict[str, str]:
    info = {
        "manufacturer": "Unknown",
        "model": "Unknown",
        "serial": "Unknown",
        "bios": "Unknown",
        "uefi": "Unknown",
    }
    try:
        boards = get_system_wmi().query("Win32_BaseBoard")
        if boards:
            board = boards[0]
            info["manufacturer"] = (
                str(board.Manufacturer).strip() if board.Manufacturer else "Unknown"
            )
            info["model"] = (
                str(board.Product).strip() if board.Product else "Unknown"
            )
            info["serial"] = (
                str(board.SerialNumber).strip() if board.SerialNumber else "Unknown"
            )

        bios_list = get_system_wmi().query("Win32_BIOS")
        if bios_list:
            bios = bios_list[0]
            info["bios"] = (
                str(bios.SMBIOSBIOSVersion).strip()
                if bios.SMBIOSBIOSVersion
                else "Unknown"
            )

        uefi = is_uefi()
        if uefi is True:
            info["uefi"] = "UEFI Enabled"
        elif uefi is False:
            info["uefi"] = "Legacy / CSM"
        else:
            info["uefi"] = "Unknown"
    except Exception:
        info["uefi"] = "Unknown"
    return info
