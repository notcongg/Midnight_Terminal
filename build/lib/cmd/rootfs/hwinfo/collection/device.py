from __future__ import annotations

from ..platform.wmi import get_system_wmi


def collect_device_type() -> str:
    try:
        enclosure_list = get_system_wmi().query("Win32_SystemEnclosure")
        if not enclosure_list:
            return "Unknown"

        enclosure = enclosure_list[0]
        chassis = enclosure.ChassisTypes or []
        # 8=Portable, 9=Laptop, 10=Notebook, 11=Hand Held,
        # 12=Docking Station, 14=Sub Notebook, 30=Tablet
        if any(t in chassis for t in [8, 9, 10, 11, 12, 14, 30]):
            return "Laptop / Portable"
        return "Desktop"
    except Exception:
        return "Unknown"


def collect_battery() -> dict[str, str]:
    info = {"status": "No Battery (Desktop)", "level": "N/A"}
    try:
        battery = get_system_wmi().query("Win32_Battery")
        if not battery:
            return info

        b = battery[0]
        status_map = {
            1: "Discharging",
            2: "Plugged In (AC)",
            3: "Charging",
            4: "Fully Charged",
        }
        info["status"] = status_map.get(b.BatteryStatus, "On Battery")
        charge = getattr(b, "EstimatedChargeRemaining", None)
        info["level"] = f"{charge}%" if charge is not None else "Unknown"
    except Exception:
        pass
    return info
