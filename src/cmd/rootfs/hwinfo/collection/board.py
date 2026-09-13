from __future__ import annotations

import os

try:
    from ..platform.win32 import is_uefi
except ImportError:
    def is_uefi():
        return None


try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None


try:
    from ..platform.posix import sys, sys_exists
except ImportError:
    def sys(path: str, default: str = "Unknown") -> str:
        return default

    def sys_exists(path: str) -> bool:
        return False


def collect_mainboard() -> dict[str, str]:
    info = {
        "manufacturer": "Unknown",
        "model": "Unknown",
        "serial": "Unknown",
        "bios": "Unknown",
        "uefi": "Unknown",
    }

    # Windows
    if os.name == "nt":
        try:
            wmi = get_system_wmi()

            if wmi:
                boards = wmi.query("Win32_BaseBoard")
                if boards:
                    board = boards[0]

                    info["manufacturer"] = (
                        str(board.Manufacturer).strip()
                        if board.Manufacturer
                        else "Unknown"
                    )

                    info["model"] = (
                        str(board.Product).strip()
                        if board.Product
                        else "Unknown"
                    )

                    info["serial"] = (
                        str(board.SerialNumber).strip()
                        if board.SerialNumber
                        else "Unknown"
                    )

                bios_list = wmi.query("Win32_BIOS")
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

    # POSIX / Linux
    try:
        info["manufacturer"] = sys(
            "class/dmi/id/board_vendor"
        )

        info["model"] = sys(
            "class/dmi/id/board_name"
        )

        info["serial"] = sys(
            "class/dmi/id/board_serial"
        )

        bios_vendor = sys(
            "class/dmi/id/bios_vendor"
        )

        bios_version = sys(
            "class/dmi/id/bios_version"
        )

        if bios_vendor != "Unknown" and bios_version != "Unknown":
            info["bios"] = f"{bios_vendor} {bios_version}"
        elif bios_version != "Unknown":
            info["bios"] = bios_version
        elif bios_vendor != "Unknown":
            info["bios"] = bios_vendor

        if sys_exists("firmware/efi"):
            info["uefi"] = "UEFI Enabled"
        else:
            info["uefi"] = "Legacy / CSM"

    except Exception:
        pass

    return info