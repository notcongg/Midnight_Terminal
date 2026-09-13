
from __future__ import annotations

import os

try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None


try:
    from ..platform.posix import sys, list_dir
except ImportError:
    def sys(path: str, default: str = "Unknown") -> str:
        return default

    def list_dir(path: str) -> list[str]:
        return []


def collect_device_type() -> str:
    # Windows
    if os.name == "nt":
        try:
            wmi = get_system_wmi()

            if not wmi:
                return "Unknown"

            enclosure_list = wmi.query(
                "Win32_SystemEnclosure"
            )

            if not enclosure_list:
                return "Unknown"

            enclosure = enclosure_list[0]
            chassis = enclosure.ChassisTypes or []

            # 8  = Portable
            # 9  = Laptop
            # 10 = Notebook
            # 11 = Hand Held
            # 12 = Docking Station
            # 14 = Sub Notebook
            # 30 = Tablet
            if any(
                t in chassis
                for t in [8, 9, 10, 11, 12, 14, 30]
            ):
                return "Laptop / Portable"

            return "Desktop"

        except Exception:
            return "Unknown"

    # POSIX / Linux
    try:
        chassis = sys(
            "class/dmi/id/chassis_type"
        )

        if chassis == "Unknown":
            return "Unknown"

        try:
            chassis_type = int(chassis)
        except ValueError:
            return "Unknown"

        if chassis_type in [8, 9, 10, 11, 12, 14, 30]:
            return "Laptop / Portable"

        if chassis_type in [
            3,   # Desktop
            4,   # Low Profile Desktop
            5,   # Pizza Box
            6,   # Mini Tower
            7,   # Tower
            13,  # All In One
            15,  # Space-saving
            16,  # Lunch Box
            17,  # Main Server Chassis
        ]:
            return "Desktop"

        return "Unknown"

    except Exception:
        return "Unknown"


def collect_battery() -> dict[str, str]:
    info = {
        "status": "No Battery (Desktop)",
        "level": "N/A",
    }

    # Windows
    if os.name == "nt":
        try:
            wmi = get_system_wmi()

            if not wmi:
                return info

            battery = wmi.query("Win32_Battery")

            if not battery:
                return info

            b = battery[0]

            status_map = {
                1: "Discharging",
                2: "Plugged In (AC)",
                3: "Charging",
                4: "Fully Charged",
            }

            info["status"] = status_map.get(
                b.BatteryStatus,
                "On Battery",
            )

            charge = getattr(
                b,
                "EstimatedChargeRemaining",
                None,
            )

            info["level"] = (
                f"{charge}%"
                if charge is not None
                else "Unknown"
            )

        except Exception:
            pass

        return info

    # POSIX / Linux
    try:
        power_supplies = list_dir(
            "/sys/class/power_supply"
        )

        batteries = [
            name
            for name in power_supplies
            if name.startswith("BAT")
        ]

        if not batteries:
            return info

        # Prefer the first detected battery.
        # This works with BAT0, BAT1, etc.
        battery = batteries[0]

        status = sys(
            f"class/power_supply/{battery}/status"
        )

        capacity = sys(
            f"class/power_supply/{battery}/capacity"
        )

        if status != "Unknown":
            status_map = {
                "Charging": "Charging",
                "Discharging": "Discharging",
                "Full": "Fully Charged",
                "Not charging": "Plugged In (AC)",
                "Unknown": "Unknown",
            }

            info["status"] = status_map.get(
                status,
                status,
            )

        if capacity != "Unknown":
            info["level"] = f"{capacity}%"

    except Exception:
        pass

    return info