from __future__ import annotations

import ctypes
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import psutil

try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None

# ============================================================================
# Ctypes Struct Definitions (Strict 1:1 Match with ram.hpp)
# ============================================================================

MAX_MEMORY_DEVICES = 64
MAX_STRING = 128
MAX_TYPE = 32

class MemoryDeviceCTypes(ctypes.Structure):
    _fields_ = [
        ("capacity_bytes", ctypes.c_uint64),
        ("speed_mt", ctypes.c_uint32),
        ("configured_speed_mt", ctypes.c_uint32),
        ("manufacturer", ctypes.c_char * MAX_STRING),
        ("part_number", ctypes.c_char * MAX_STRING),
        ("locator", ctypes.c_char * MAX_STRING),
        ("form_factor", ctypes.c_char * MAX_TYPE),
        ("type", ctypes.c_char * MAX_TYPE),
    ]

class RamInfoCTypes(ctypes.Structure):
    _fields_ = [
        ("total_bytes", ctypes.c_uint64),
        ("slots_used", ctypes.c_uint32),
        ("slots_total", ctypes.c_uint32),
        ("speed_mt", ctypes.c_uint32),
        ("type", ctypes.c_char * MAX_TYPE),
        ("device_count", ctypes.c_uint32),
        ("devices", MemoryDeviceCTypes * MAX_MEMORY_DEVICES),
    ]

# ============================================================================
# Helpers
# ============================================================================

def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None: return default
        return int(value)
    except (TypeError, ValueError):
        return default

def _bytes_to_gib(value: int) -> float:
    return round(value / (1024 ** 3), 2)

def _text(value: Any) -> str:
    if value is None: return "Unknown"
    result = str(value).strip()
    return result if result else "Unknown"

# ============================================================================
# Native C++ Library Interop (ctypes)
# ============================================================================

def _find_native_library() -> Path | None:
    base_dir = Path(__file__).resolve().parent
    if os.name == "nt":
        candidates = [
            base_dir / "ram" / "build-win" / "midnight_ram_windows.dll",
            base_dir / "ram" / "build" / "midnight_ram_windows.dll",
            base_dir / "ram" / "midnight_ram_windows.dll",
            base_dir / "midnight_ram_windows.dll",
        ]
    else:
        candidates = [
            base_dir / "ram" / "build" / "libmidnight_ram_linux.so",
            base_dir / "ram" / "libmidnight_ram_linux.so",
            base_dir / "libmidnight_ram_linux.so",
        ]
    for path in candidates:
        if path.is_file(): return path
    return None

def _collect_native_ram() -> dict | None:
    lib_path = _find_native_library()
    if not lib_path: return None
    try:
        lib = ctypes.CDLL(str(lib_path))
        lib.midnight_ram_collect.argtypes = [ctypes.POINTER(RamInfoCTypes)]
        lib.midnight_ram_collect.restype = ctypes.c_int

        ram_info = RamInfoCTypes()
        result = lib.midnight_ram_collect(ctypes.byref(ram_info))

        if result != 1 or ram_info.device_count == 0:
            return None

        sticks: list[dict] = []
        for i in range(ram_info.device_count):
            dev = ram_info.devices[i]
            effective_speed = dev.configured_speed_mt if dev.configured_speed_mt > 0 else dev.speed_mt
            
            sticks.append({
                "manufacturer": _text(dev.manufacturer.decode("utf-8", errors="ignore")),
                "capacity_gib": _bytes_to_gib(dev.capacity_bytes),
                "part_number": _text(dev.part_number.decode("utf-8", errors="ignore")),
                "form_factor": _text(dev.form_factor.decode("utf-8", errors="ignore")),
                "type": _text(dev.type.decode("utf-8", errors="ignore")),
                "speed": effective_speed if effective_speed > 0 else "Unknown",
                "locator": _text(dev.locator.decode("utf-8", errors="ignore")),
            })

        total_gib = _bytes_to_gib(ram_info.total_bytes)
        if total_gib <= 0:
            try: total_gib = _bytes_to_gib(psutil.virtual_memory().total)
            except Exception: pass

        ram_type = _text(ram_info.type.decode("utf-8", errors="ignore"))

        return {
            "total_gib": total_gib,
            "slots_used": ram_info.slots_used,
            "slots_total": ram_info.slots_total if ram_info.slots_total > 0 else "Unknown",
            "speed": ram_info.speed_mt if ram_info.speed_mt > 0 else "Unknown",
            "type": ram_type,
            "sticks": sticks,
        }
    except Exception:
        return None

# ============================================================================
# Linux dmidecode (Fallback)
# ============================================================================

def _run_dmidecode(as_root: bool = False) -> str:
    if shutil.which("dmidecode") is None:
        return ""
    try:
        cmd = ["dmidecode", "--type", "memory"]
        if as_root:
            cmd.insert(0, "sudo")
            
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    if result.returncode != 0: return ""
    return result.stdout

def _parse_capacity(value: str) -> float:
    match = re.search(r"([\d.]+)\s*(KB|MB|GB|TB|KiB|MiB|GiB|TiB)", value, flags=re.IGNORECASE)
    if not match: return 0.0
    number, unit = float(match.group(1)), match.group(2).lower()
    multipliers = {"kb": 1/(1024**2), "mb": 1/1024, "gb": 1, "tb": 1024, "kib": 1/(1024**2), "mib": 1/1024, "gib": 1, "tib": 1024}
    return round(number * multipliers[unit], 2)

def _parse_speed(value: str) -> int:
    match = re.search(r"([\d.]+)\s*(?:MT/s|MHz)", value, flags=re.IGNORECASE)
    if not match: return 0
    try: return int(float(match.group(1)))
    except ValueError: return 0

def _extract_field(block: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}:\s*(.+)$", block, flags=re.MULTILINE)
    if not match: return "Unknown"
    return match.group(1).strip()

def _parse_dmidecode_memory(output: str) -> tuple[int | str, list[dict]]:
    if not output: return "Unknown", []
    
    slots_total: int | str = "Unknown"
    array_match = re.search(r"Physical Memory Array.*?Number Of Devices:\s*(\d+)", output, flags=re.DOTALL)
    if array_match:
        slots = _safe_int(array_match.group(1), 0)
        if slots > 0: slots_total = slots

    blocks = re.split(r"\n(?=Handle\s+0x[0-9A-Fa-f]+,\s+DMI type 17\b)", output)
    sticks: list[dict] = []

    for block in blocks:
        if not re.search(r"^\s*Memory Device\s*$", block, flags=re.MULTILINE): continue
        size_text = _extract_field(block, "Size")
        if size_text.lower() in {"no module installed", "no module", "not installed", "unknown"}: continue
        
        capacity_gib = _parse_capacity(size_text)
        if capacity_gib <= 0: continue

        speed = _parse_speed(_extract_field(block, "Configured Memory Speed"))
        if speed <= 0: speed = _parse_speed(_extract_field(block, "Speed"))

        sticks.append({
            "manufacturer": _text(_extract_field(block, "Manufacturer")),
            "capacity_gib": capacity_gib,
            "part_number": _text(_extract_field(block, "Part Number")),
            "form_factor": _text(_extract_field(block, "Form Factor")),
            "type": _text(_extract_field(block, "Type")),
            "speed": speed if speed > 0 else "Unknown",
            "locator": _text(_extract_field(block, "Locator")),
        })

    return slots_total, sticks

# ============================================================================
# Windows WMI (Fallback)
# ============================================================================

def _collect_windows_ram() -> dict:
    info = {"slots_used": 0, "slots_total": "Unknown", "speed": "Unknown", "type": "Unknown", "sticks": []}
    try:
        wmi = get_system_wmi()
        if not wmi: return info

        arrays = wmi.query("Win32_PhysicalMemoryArray")
        if arrays:
            slots_total = _safe_int(getattr(arrays[0], "MemoryDevices", 0), 0)
            if slots_total > 0: info["slots_total"] = slots_total

        physical_memory = wmi.query("Win32_PhysicalMemory")
        if not physical_memory: return info
        info["slots_used"] = len(physical_memory)

        speeds, types = [], []
        for stick in physical_memory:
            speed = _safe_int(getattr(stick, "ConfiguredClockSpeed", 0), 0)
            if speed <= 0: speed = _safe_int(getattr(stick, "Speed", 0), 0)
            if speed > 0: speeds.append(speed)

            type_code = _safe_int(getattr(stick, "SMBIOSMemoryType", 0), 0)
            memory_types = {20: "DDR", 21: "DDR2", 22: "DDR2 FB-DIMM", 24: "DDR3", 26: "DDR4", 27: "LPDDR", 28: "LPDDR2", 29: "LPDDR3", 30: "LPDDR4", 34: "DDR5", 35: "LPDDR5"}
            memory_type = memory_types.get(type_code, "Unknown")
            if memory_type != "Unknown": types.append(memory_type)

            form_factors = {8: "DIMM", 10: "Chip", 12: "SO-DIMM", 14: "FB-DIMM"}
            form_factor = form_factors.get(_safe_int(getattr(stick, "FormFactor", 0), 0), "Unknown")

            info["sticks"].append({
                "manufacturer": _text(getattr(stick, "Manufacturer", None)),
                "capacity_gib": _bytes_to_gib(_safe_int(getattr(stick, "Capacity", 0), 0)),
                "part_number": _text(getattr(stick, "PartNumber", None)),
                "form_factor": form_factor,
                "type": memory_type,
                "speed": speed if speed > 0 else "Unknown",
                "locator": _text(getattr(stick, "DeviceLocator", None)),
            })

        if speeds: info["speed"] = max(speeds)
        if types: info["type"] = types[0]
    except Exception: pass
    return info

# ============================================================================
# Public collector
# ============================================================================

def collect_ram(as_root: bool = False) -> dict:
    native_info = _collect_native_ram()
    # If the native library fails due to permissions (Linux user), fallback to dmidecode
    # which can use the `as_root` flag to execute `sudo dmidecode`.
    if native_info is not None and native_info.get('speed') != "Unknown":
        return native_info

    info = {
        "total_gib": 0.0,
        "slots_used": 0,
        "slots_total": "Unknown",
        "speed": "Unknown",
        "type": "Unknown",
        "sticks": [],
    }

    try: info["total_gib"] = _bytes_to_gib(psutil.virtual_memory().total)
    except Exception: pass

    if os.name == "nt":
        windows_info = _collect_windows_ram()
        info.update(windows_info)
        return info

    try:
        dmidecode_output = _run_dmidecode(as_root=as_root)
        if dmidecode_output:
            slots_total, sticks = _parse_dmidecode_memory(dmidecode_output)
            info["slots_total"] = slots_total
            info["sticks"] = sticks
            info["slots_used"] = len(sticks)

            if sticks:
                speeds = [stick["speed"] for stick in sticks if stick.get("speed") != "Unknown"]
                if speeds: info["speed"] = max(speeds)

                types = [stick["type"] for stick in sticks if stick.get("type") and stick["type"] != "Unknown"]
                if types: info["type"] = types[0]
    except Exception: pass

    return info