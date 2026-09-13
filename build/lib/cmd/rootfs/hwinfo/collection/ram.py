from __future__ import annotations

import psutil

from ..platform.wmi import get_system_wmi


def collect_ram() -> dict:
    info = {
        "total_gib": 0,
        "slots_used": 0,
        "slots_total": "?",
        "speed": 0,
        "type": "Unknown",
        "sticks": [],
    }
    mem_types = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5", 35: "LPDDR5"}
    form_factors = {8: "DIMM", 12: "SO-DIMM", 0: "Unknown"}

    try:
        total_bytes = psutil.virtual_memory().total
        info["total_gib"] = round(total_bytes / (1024**3), 2)
    except Exception:
        pass

    try:
        mem_array = get_system_wmi().query("Win32_PhysicalMemoryArray")
        if mem_array:
            info["slots_total"] = mem_array[0].MemoryDevices

        physical_memory = get_system_wmi().query("Win32_PhysicalMemory")
        info["slots_used"] = len(physical_memory)

        speeds = []
        for stick in physical_memory:
            speed = int(stick.Speed) if stick.Speed else 0
            speeds.append(speed)

            type_code = getattr(stick, "SMBIOSMemoryType", 0)
            stick_type = mem_types.get(type_code, "Unknown")
            if stick_type != "Unknown":
                info["type"] = stick_type

            ff_code = getattr(stick, "FormFactor", 0)
            ff_str = form_factors.get(ff_code, "DIMM/Unknown")

            cap_bytes = int(stick.Capacity) if stick.Capacity else 0
            info["sticks"].append(
                {
                    "manufacturer": (
                        str(stick.Manufacturer).strip()
                        if stick.Manufacturer
                        else "Unknown"
                    ),
                    "capacity_gib": round(cap_bytes / (1024**3), 2),
                    "part_number": (
                        str(stick.PartNumber).strip()
                        if stick.PartNumber
                        else "Unknown"
                    ),
                    "form_factor": ff_str,
                }
            )

        if speeds:
            info["speed"] = max(speeds)
    except Exception:
        pass
    return info
