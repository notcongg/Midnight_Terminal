from __future__ import annotations

import re

from ..platform.wmi import get_system_wmi


def collect_cpu() -> dict:
    info = {
        "name": "Unknown",
        "cores": 0,
        "threads": 0,
        "clock": "Unknown",
        "socket": "Unknown",
    }
    try:
        cpus = get_system_wmi().query("Win32_Processor")
        if not cpus:
            return info

        cpu = cpus[0]
        if cpu.Name:
            name = str(cpu.Name).strip()
            info["name"] = re.sub(
                r"(?i)\s*(with|w/)\s*radeon.*graphics",
                "",
                name,
            ).strip()

        info["cores"] = cpu.NumberOfCores or 0
        info["threads"] = cpu.NumberOfLogicalProcessors or 0

        clock = getattr(cpu, "CurrentClockSpeed", None)
        if clock:
            info["clock"] = f"{round(clock / 1000, 2)} GHz"

        info["socket"] = (
            str(cpu.SocketDesignation).strip()
            if cpu.SocketDesignation
            else "Unknown"
        )
    except Exception:
        pass
    return info
