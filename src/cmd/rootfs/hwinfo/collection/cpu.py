
from __future__ import annotations

import os
import re

try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None


try:
    from ..platform.posix import proc
except ImportError:
    def proc(path: str, default: str = "Unknown") -> str:
        return default


def _clean_cpu_name(name: str) -> str:
    """Normalize CPU names for display."""
    name = str(name).strip()

    # Remove integrated Radeon graphics suffix.
    name = re.sub(
        r"(?i)\s*(with|w/)\s*radeon.*$",
        "",
        name,
    ).strip()

    return name or "Unknown"


def collect_cpu() -> dict:
    info = {
        "name": "Unknown",
        "cores": 0,
        "threads": 0,
        "clock": "Unknown",
        "socket": "Unknown",
    }

    # Windows
    if os.name == "nt":
        try:
            wmi = get_system_wmi()

            if not wmi:
                return info

            cpus = wmi.query("Win32_Processor")

            if not cpus:
                return info

            cpu = cpus[0]

            if cpu.Name:
                info["name"] = _clean_cpu_name(cpu.Name)

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

    # POSIX / Linux
    try:
        cpuinfo = proc("cpuinfo", "")

        if not cpuinfo:
            return info

        # CPU model
        model_match = re.search(
            r"^model name\s*:\s*(.+)$",
            cpuinfo,
            re.MULTILINE,
        )

        if model_match:
            info["name"] = _clean_cpu_name(
                model_match.group(1)
            )

        # Logical processors / threads
        processor_entries = re.findall(
            r"^processor\s*:",
            cpuinfo,
            re.MULTILINE,
        )

        if processor_entries:
            info["threads"] = len(processor_entries)

        # Physical cores
        core_match = re.search(
            r"^cpu cores\s*:\s*(\d+)$",
            cpuinfo,
            re.MULTILINE,
        )

        if core_match:
            info["cores"] = int(core_match.group(1))

        # Current clock
        clock_match = re.search(
            r"^cpu MHz\s*:\s*([\d.]+)$",
            cpuinfo,
            re.MULTILINE,
        )

        if clock_match:
            clock_mhz = float(clock_match.group(1))
            info["clock"] = f"{round(clock_mhz / 1000, 2)} GHz"

        # Physical socket ID
        socket_match = re.search(
            r"^physical id\s*:\s*(\S+)$",
            cpuinfo,
            re.MULTILINE,
        )

        if socket_match:
            info["socket"] = socket_match.group(1)

    except Exception:
        pass

    return info