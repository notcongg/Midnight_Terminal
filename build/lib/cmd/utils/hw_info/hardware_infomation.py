import platform
import subprocess
import json
import re
import psutil
import socket
import ctypes

try:
    import wmi
except ImportError:
    wmi = None

_wmi_client = None

def get_wmi():
    global _wmi_client
    if _wmi_client is None and wmi is not None:
        if platform.system() == "Windows":
            try:
                _wmi_client = wmi.WMI()
            except Exception:
                _wmi_client = None
    return _wmi_client

class DotDict(dict):
    def __getattr__(self, item):
        val = self.get(item)
        if isinstance(val, dict):
            return DotDict(val)
        if isinstance(val, list):
            return [DotDict(i) if isinstance(i, dict) else i for i in val]
        return val

def get_os_info() -> dict:
    c = get_wmi()
    info = {"name": "Unknown", "build": "Unknown", "arch": "Unknown"}
    if c:
        try:
            os_wmi = c.Win32_OperatingSystem()[0]
            info["name"] = os_wmi.Caption.strip()
            info["build"] = os_wmi.BuildNumber
            info["arch"] = os_wmi.OSArchitecture
        except Exception:
            pass
    return info

def get_device_type() -> str:
    c = get_wmi()
    if c:
        try:
            enclosure = c.Win32_SystemEnclosure()[0]
            if any(t in enclosure.ChassisTypes for t in [8, 9, 10, 11, 14]):
                return "Laptop"
            return "Desktop"
        except Exception:
            pass
    return "Unknown"

def get_battery_info() -> dict:
    c = get_wmi()
    info = {"status": "No Battery (Desktop)", "level": "N/A"}
    if c:
        try:
            battery = c.Win32_Battery()
            if battery:
                b = battery[0]
                status_map = {1: "Discharging", 2: "AC Connected", 3: "Charging", 4: "Full"}
                info["status"] = status_map.get(b.BatteryStatus, "On Battery")
                info["level"] = f"{b.EstimatedChargeRemaining}%"
        except Exception:
            pass
    return info

def get_mainboard_info() -> dict:
    c = get_wmi()
    info = {
        "manufacturer": "Unknown",
        "model": "Unknown",
        "serial": "Unknown",
        "bios": "Unknown",
        "uefi": "Unknown"
    }
    if c:
        try:
            board = c.Win32_BaseBoard()[0]
            info["manufacturer"] = board.Manufacturer.strip() if board.Manufacturer else "Unknown"
            info["model"] = board.Product.strip() if board.Product else "Unknown"
            info["serial"] = board.SerialNumber.strip() if board.SerialNumber else "Unknown"
            bios = c.Win32_BIOS()[0]
            info["bios"] = bios.SMBIOSBIOSVersion.strip() if bios.SMBIOSBIOSVersion else "Unknown"
            
            ps_script = 'if (Test-Path "HKLM:\\System\\CurrentControlSet\\Control\\SecureBoot\\State") { "Yes" } else { "No / Legacy" }'
            ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if ps_res.returncode == 0:
                info["uefi"] = ps_res.stdout.strip()
        except Exception:
            pass
    return info

def get_cpu_info() -> dict:
    c = get_wmi()
    info = {"name": "Unknown", "cores": 0, "threads": 0, "clock": "Unknown", "socket": "Unknown"}
    if c:
        try:
            cpu = c.Win32_Processor()[0]
            if cpu.Name:
                name = cpu.Name.strip()
                info["name"] = re.sub(r'(?i)\s*(with|w/)\s*radeon.*graphics', '', name)
            info["cores"] = cpu.NumberOfCores
            info["threads"] = cpu.NumberOfLogicalProcessors
            if cpu.CurrentClockSpeed:
                info["clock"] = f"{cpu.CurrentClockSpeed} MHz"
            info["socket"] = cpu.SocketDesignation.strip() if cpu.SocketDesignation else "Unknown"
        except Exception:
            pass
    return info

def get_ram_info() -> dict:
    c = get_wmi()
    info = {"total_gib": 0, "slots_used": 0, "slots_total": "?", "speed": 0, "type": "Unknown", "sticks": []}
    mem_types = {24: "DDR3", 26: "DDR4", 34: "DDR5", 35: "LPDDR5"}
    form_factors = {8: "DIMM", 12: "SO-DIMM"}
    if c:
        try:
            mem_array = c.Win32_PhysicalMemoryArray()
            if mem_array:
                info["slots_total"] = mem_array[0].MemoryDevices
            physical_memory = c.Win32_PhysicalMemory()
            info["slots_used"] = len(physical_memory)
            total_capacity = 0
            speeds = []
            for stick in physical_memory:
                capacity_bytes = int(stick.Capacity)
                total_capacity += capacity_bytes
                speed = int(stick.Speed) if stick.Speed else 0
                speeds.append(speed)
                stick_type_code = getattr(stick, "SMBIOSMemoryType", 0)
                stick_type = mem_types.get(stick_type_code, "Unknown")
                info["type"] = stick_type if stick_type != "Unknown" else info["type"]
                ff_code = getattr(stick, "FormFactor", 0)
                ff_str = form_factors.get(ff_code, "DIMM")
                info["sticks"].append({
                    "manufacturer": stick.Manufacturer.strip() if stick.Manufacturer else "Unknown",
                    "capacity_gib": round(capacity_bytes / (1024**3), 2),
                    "part_number": stick.PartNumber.strip() if stick.PartNumber else "Unknown",
                    "form_factor": ff_str
                })
            info["total_gib"] = round(total_capacity / (1024**3), 2)
            if speeds:
                info["speed"] = max(speeds)
        except Exception:
            pass
    return info

def get_monitor_info() -> list:
    c = get_wmi()
    monitors = []
    try:
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32), ("dmSpecVersion", ctypes.c_ushort),
                ("dmDriverVersion", ctypes.c_ushort), ("dmSize", ctypes.c_ushort),
                ("dmDriverExtra", ctypes.c_ushort), ("dmFields", ctypes.c_ulong),
                ("dmPositionX", ctypes.c_long), ("dmPositionY", ctypes.c_long),
                ("dmDisplayOrientation", ctypes.c_ulong), ("dmDisplayFixedOutput", ctypes.c_ulong),
                ("dmColor", ctypes.c_short), ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short), ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short), ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_ushort), ("dmBitsPerPel", ctypes.c_ulong),
                ("dmPelsWidth", ctypes.c_ulong), ("dmPelsHeight", ctypes.c_ulong),
                ("dmDisplayFlags", ctypes.c_ulong), ("dmDisplayFrequency", ctypes.c_ulong),
            ]

        dev = DEVMODE()
        dev.dmSize = ctypes.sizeof(DEVMODE)
        ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dev))

        names = [mon.Name.strip() for mon in c.Win32_DesktopMonitor() if mon.Name] if c else []
        name = names[0] if names else "Generic PnP Monitor"

        monitors.append({
            "name": name,
            "width": dev.dmPelsWidth,
            "height": dev.dmPelsHeight,
            "hz": dev.dmDisplayFrequency
        })
    except Exception:
        monitors.append({"name": "Unknown", "width": "?", "height": "?", "hz": "?"})
    return monitors

def get_storage_info() -> list:
    drives = []
    ps_script = 'Get-PhysicalDisk | Select-Object Model, Size, MediaType, BusType | ConvertTo-Json'
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            for disk in data:
                drives.append({
                    "type": f"{disk.get('BusType')} {disk.get('MediaType')}",
                    "model": disk.get("Model", "Unknown").strip(),
                    "size_gib": round(disk.get("Size", 0) / (1024**3), 2)
                })
    except Exception:
        pass
    return drives

def get_gpu_info() -> dict:
    c = get_wmi()
    gpus = {"igpu": [], "dgpu": []}
    seen = set()
    if c:
        try:
            for gpu in c.Win32_VideoController():
                name = gpu.Name.strip()
                if name in seen or "virtual" in name.lower() or "remote" in name.lower():
                    continue
                seen.add(name)
                is_igpu = any(kw in name.lower() for kw in ["intel", "uhd", "iris"]) or ("radeon" in name.lower() and not any(kw in name.lower() for kw in ["rx ", "pro ", "xt "]))
                if any(kw in name.lower() for kw in ["nvidia", "geforce", "rtx", "gtx", "quadro"]):
                    is_igpu = False
                if is_igpu:
                    gpus["igpu"].append(name)
                else:
                    gpus["dgpu"].append(name)
        except Exception:
            pass
    return gpus

def get_network_info() -> list:
    networks = []
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        wifi_name, wifi_type = "Unknown", "Unknown"

        try:
            wifi = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8", errors="ignore")
            ssid = re.search(r"^\s*SSID\s*:\s*(.+)$", wifi, re.MULTILINE)
            radio = re.search(r"^\s*Radio type\s*:\s*(.+)$", wifi, re.MULTILINE)
            if ssid:
                wifi_name = ssid.group(1).strip()
            if radio:
                wifi_type = radio.group(1).strip()
        except Exception:
            pass

        vpn_detected = False

        for nic, stat in stats.items():
            if not stat.isup:
                continue
            lower = nic.lower()
            ip, mac = "-", "-"
            
            if nic in addrs:
                for addr in addrs[nic]:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                    elif addr.family == psutil.AF_LINK:
                        mac = addr.address

            if "wi-fi" in lower or "wifi" in lower or "wireless" in lower:
                networks.append({
                    "adapter": nic,
                    "type": "Wi-Fi",
                    "name": wifi_name,
                    "standard": wifi_type,
                    "speed": f"{stat.speed} Mbps",
                    "ip": ip,
                    "mac": mac,
                    "vpn": "OFF"
                })
            elif "ethernet" in lower:
                networks.append({
                    "adapter": nic,
                    "type": "Ethernet",
                    "name": "LAN",
                    "standard": "Wired",
                    "speed": f"{stat.speed} Mbps",
                    "ip": ip,
                    "mac": mac,
                    "vpn": "OFF"
                })
            elif ("vpn" in lower or "tap" in lower or "tun" in lower or "wireguard" in lower) and "teredo" not in lower:
                vpn_detected = True
                networks.append({
                    "adapter": nic,
                    "type": "VPN",
                    "name": nic,
                    "standard": "Tunnel",
                    "speed": f"{stat.speed} Mbps",
                    "ip": ip,
                    "mac": mac,
                    "vpn": "ON"
                })

        for net in networks:
            if net["type"] != "VPN":
                net["vpn"] = "ON" if vpn_detected else "OFF"
    except Exception:
        pass
    return networks

def get_system_info() -> DotDict:
    return DotDict({
        "hostname": platform.node(),
        "os": get_os_info(),
        "device_type": get_device_type(),
        "battery": get_battery_info(),
        "mainboard": get_mainboard_info(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "monitors": get_monitor_info(),
        "storage": get_storage_info(),
        "gpu": get_gpu_info(),
        "network": get_network_info()
    })