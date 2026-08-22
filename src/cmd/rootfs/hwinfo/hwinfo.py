import platform
import sys
import subprocess
import json
import os
import re
import socket
import msvcrt
import ctypes

try:
    import wmi
    import psutil
except ImportError:
    print("Please install the required libraries: pip install wmi pypiwin32 psutil")
    sys.exit(1)

# Enable ANSI escape code support on Windows 10/11
os.system('')
# ---------------------------------------------------------
# Win32 API Structures for Display Enumeration
# ---------------------------------------------------------
class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.c_ulong),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]

class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmPositionX", ctypes.c_long),
        ("dmPositionY", ctypes.c_long),
        ("dmDisplayOrientation", ctypes.c_ulong),
        ("dmDisplayFixedOutput", ctypes.c_ulong),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_ulong),
        ("dmPelsHeight", ctypes.c_ulong),
        ("dmDisplayFlags", ctypes.c_ulong),
        ("dmDisplayFrequency", ctypes.c_ulong),
        ("dmICMMethod", ctypes.c_ulong),
        ("dmICMIntent", ctypes.c_ulong),
        ("dmMediaType", ctypes.c_ulong),
        ("dmDitherType", ctypes.c_ulong),
        ("dmReserved1", ctypes.c_ulong),
        ("dmReserved2", ctypes.c_ulong),
        ("dmPanningWidth", ctypes.c_ulong),
        ("dmPanningHeight", ctypes.c_ulong),
    ]

class SystemAnalyzer:
    def __init__(self):
        if platform.system() != "Windows":
            print("Error: This script only supports Windows.")
            sys.exit(1)
        
        try:
            self.c = wmi.WMI()
        except Exception as e:
            print(f"Failed to initialize WMI. Error: {e}")
            sys.exit(1)

    def get_os_info(self) -> dict:
        info = {"name": "Unknown", "build": "Unknown", "arch": "Unknown"}
        try:
            os_wmi = self.c.Win32_OperatingSystem()[0]
            info["name"] = str(os_wmi.Caption).strip()
            info["build"] = str(os_wmi.BuildNumber).strip()
            info["arch"] = str(os_wmi.OSArchitecture).strip()
        except Exception:
            pass
        return info

    def get_device_type(self) -> str:
        try:
            enclosure = self.c.Win32_SystemEnclosure()[0]
            chassis = enclosure.ChassisTypes
            # 8=Portable, 9=Laptop, 10=Notebook, 11=Hand Held, 12=Docking Station, 14=Sub Notebook, 30=Tablet
            if any(t in chassis for t in [8, 9, 10, 11, 12, 14, 30]):
                return "Laptop / Portable"
            return "Desktop"
        except Exception:
            return "Unknown"

    def get_battery_info(self) -> dict:
        info = {"status": "No Battery (Desktop)", "level": "N/A"}
        try:
            battery = self.c.Win32_Battery()
            if battery:
                b = battery[0]
                status_map = {1: "Discharging", 2: "Plugged In (AC)", 3: "Charging", 4: "Fully Charged"}
                info["status"] = status_map.get(b.BatteryStatus, "On Battery")
                charge = getattr(b, "EstimatedChargeRemaining", None)
                info["level"] = f"{charge}%" if charge is not None else "Unknown"
        except Exception:
            pass
        return info

    def get_mainboard_info(self) -> dict:
        info = {"manufacturer": "Unknown", "model": "Unknown", "serial": "Unknown", "bios": "Unknown", "uefi": "Unknown"}
        try:
            board = self.c.Win32_BaseBoard()[0]
            info["manufacturer"] = str(board.Manufacturer).strip() if board.Manufacturer else "Unknown"
            info["model"] = str(board.Product).strip() if board.Product else "Unknown"
            info["serial"] = str(board.SerialNumber).strip() if board.SerialNumber else "Unknown"
            
            bios = self.c.Win32_BIOS()[0]
            info["bios"] = str(bios.SMBIOSBIOSVersion).strip() if bios.SMBIOSBIOSVersion else "Unknown"
            
            # Robust native UEFI check via Kernel32
            kernel32 = ctypes.windll.kernel32
            kernel32.GetFirmwareEnvironmentVariableW.restype = ctypes.c_ulong
            kernel32.GetFirmwareEnvironmentVariableW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p, ctypes.c_ulong]
            kernel32.GetFirmwareEnvironmentVariableW("", "{00000000-0000-0000-0000-000000000000}", None, 0)
            
            if ctypes.GetLastError() == 1:  # ERROR_INVALID_FUNCTION
                info["uefi"] = "Legacy / CSM"
            else:
                info["uefi"] = "UEFI Enabled"
        except Exception:
            info["uefi"] = "Unknown"
        return info

    def get_cpu_info(self) -> dict:
        info = {"name": "Unknown", "cores": 0, "threads": 0, "clock": "Unknown", "socket": "Unknown"}
        try:
            cpu = self.c.Win32_Processor()[0]
            if cpu.Name:
                name = str(cpu.Name).strip()
                # Safely clean redundant APU strings
                info["name"] = re.sub(r'(?i)\s*(with|w/)\s*radeon.*graphics', '', name).strip()
            
            info["cores"] = cpu.NumberOfCores
            info["threads"] = cpu.NumberOfLogicalProcessors
            
            clock = getattr(cpu, "CurrentClockSpeed", None)
            if clock:
                info["clock"] = f"{round(clock / 1000, 2)} GHz"
                
            info["socket"] = str(cpu.SocketDesignation).strip() if cpu.SocketDesignation else "Unknown"
        except Exception:
            pass
        return info

    def get_ram_info(self) -> dict:
        info = {"total_gib": 0, "slots_used": 0, "slots_total": "?", "speed": 0, "type": "Unknown", "sticks": []}
        mem_types = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5", 35: "LPDDR5"}
        form_factors = {8: "DIMM", 12: "SO-DIMM", 0: "Unknown"}
        
        try:
            # Use psutil for exact total usable capacity
            total_bytes = psutil.virtual_memory().total
            info["total_gib"] = round(total_bytes / (1024**3), 2)

            mem_array = self.c.Win32_PhysicalMemoryArray()
            if mem_array:
                info["slots_total"] = mem_array[0].MemoryDevices

            physical_memory = self.c.Win32_PhysicalMemory()
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
                info["sticks"].append({
                    "manufacturer": str(stick.Manufacturer).strip() if stick.Manufacturer else "Unknown",
                    "capacity_gib": round(cap_bytes / (1024**3), 2),
                    "part_number": str(stick.PartNumber).strip() if stick.PartNumber else "Unknown",
                    "form_factor": ff_str
                })

            if speeds:
                info["speed"] = max(speeds)
        except Exception:
            pass
        return info

    def _get_friendly_monitor_names(self) -> dict:
        """Query WMI root\\wmi (WmiMonitorID) to extract real EDID monitor model names."""
        friendly_names = {}
        try:
            wmi_wmi = wmi.WMI(namespace="root\\wmi")
            for mon in wmi_wmi.WmiMonitorID():
                inst = getattr(mon, "InstanceName", "")
                user_name_raw = getattr(mon, "UserFriendlyName", None)
                if inst and user_name_raw:
                    name_str = "".join(chr(c) for c in user_name_raw if c > 0).strip()
                    if name_str:
                        parts = inst.upper().split('\\')
                        if len(parts) >= 2:
                            friendly_names[parts[1]] = name_str
        except Exception:
            pass
        return friendly_names

    def get_monitor_info(self) -> list:
        monitors = []
        DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
        DISPLAY_DEVICE_MIRRORING_DRIVER = 0x00000008
        ENUM_CURRENT_SETTINGS = 0xFFFFFFFF

        friendly_names = self._get_friendly_monitor_names()

        try:
            dev_idx = 0
            while dev_idx < 64:  # Defensive upper bound
                display_device = DISPLAY_DEVICEW()
                display_device.cb = ctypes.sizeof(DISPLAY_DEVICEW)

                if not ctypes.windll.user32.EnumDisplayDevicesW(None, dev_idx, ctypes.byref(display_device), 0):
                    break
                dev_idx += 1

                if not (display_device.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP):
                    continue
                if display_device.StateFlags & DISPLAY_DEVICE_MIRRORING_DRIVER:
                    continue

                monitor_name = ""
                mon_idx = 0
                monitor_found = False

                while mon_idx < 16:
                    mon_device = DISPLAY_DEVICEW()
                    mon_device.cb = ctypes.sizeof(DISPLAY_DEVICEW)

                    if not ctypes.windll.user32.EnumDisplayDevicesW(display_device.DeviceName, mon_idx, ctypes.byref(mon_device), 0):
                        break
                    mon_idx += 1

                    # Ensure the sub-device is actually the active, physically connected monitor
                    if mon_device.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
                        dev_id = mon_device.DeviceID.upper() if mon_device.DeviceID else ""
                        parts = dev_id.split('\\')
                        
                        if len(parts) >= 2 and parts[1] in friendly_names:
                            monitor_name = friendly_names[parts[1]]

                        if not monitor_name and mon_device.DeviceString and mon_device.DeviceString.strip():
                            monitor_name = mon_device.DeviceString.strip()
                            
                        monitor_found = True
                        break 

                if not monitor_found:
                    continue

                if not monitor_name:
                    monitor_name = "Generic PnP Monitor"

                dev_mode = DEVMODEW()
                dev_mode.dmSize = ctypes.sizeof(DEVMODEW)

                if ctypes.windll.user32.EnumDisplaySettingsW(display_device.DeviceName, ENUM_CURRENT_SETTINGS, ctypes.byref(dev_mode)):
                    hz_val = dev_mode.dmDisplayFrequency
                    monitors.append({
                        "name": monitor_name,
                        "width": dev_mode.dmPelsWidth,
                        "height": dev_mode.dmPelsHeight,
                        "hz": hz_val if hz_val > 1 else "Default"
                    })

        except Exception:
            pass

        if not monitors:
            monitors.append({"name": "Unknown Monitor", "width": "?", "height": "?", "hz": "?"})
            
        return monitors

    def get_storage_info(self) -> list:
        drives = []
        ps_script = 'Get-PhysicalDisk | Select-Object Model, Size, MediaType, BusType | ConvertTo-Json -Compress'
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                    
                for disk in data:
                    model = str(disk.get("Model", "Unknown")).strip() if disk.get("Model") else "Unknown Storage"
                    bus = str(disk.get("BusType", "")).strip() if disk.get("BusType") else "Unknown"
                    media = str(disk.get("MediaType", "")).strip() if disk.get("MediaType") else "Disk"
                    size_bytes = disk.get("Size")
                    size_gib = round(size_bytes / (1024**3), 2) if isinstance(size_bytes, (int, float)) else 0
                    
                    drives.append({
                        "type": f"{bus} {media}".strip(),
                        "model": model,
                        "size_gib": size_gib
                    })
        except Exception:
            pass
        return drives if drives else [{"type": "Unknown", "model": "Unknown Drive", "size_gib": 0}]

    def get_gpu_info(self) -> dict:
        gpus = {"igpu": [], "dgpu": []}
        seen = set()
        try:
            for gpu in self.c.Win32_VideoController():
                name = str(gpu.Name).strip() if gpu.Name else "Unknown GPU"
                if name in seen or any(kw in name.lower() for kw in ["virtual", "remote", "citrix"]):
                    continue
                seen.add(name)
                
                name_lower = name.lower()
                is_igpu = False
                
                # Heuristics for iGPU vs dGPU
                if "intel" in name_lower:
                    is_igpu = "arc" not in name_lower
                elif "radeon" in name_lower or "amd" in name_lower:
                    is_igpu = not any(kw in name_lower for kw in ["rx ", "pro ", "xt ", "discrete"])
                elif any(kw in name_lower for kw in ["nvidia", "geforce", "rtx", "gtx", "quadro"]):
                    is_igpu = False
                else:
                    is_igpu = True # Fallback generic display adapters
                    
                if is_igpu:
                    gpus["igpu"].append(name)
                else:
                    gpus["dgpu"].append(name)
        except Exception:
            pass
        return gpus

    def get_network_info(self) -> list:
        networks = []
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            wifi_name, wifi_type = "Unknown", "Unknown"

            try:
                wifi = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], encoding="utf-8", errors="ignore")
                ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", wifi, re.MULTILINE)
                radio_match = re.search(r"^\s*Radio type\s*:\s*(.+)$", wifi, re.MULTILINE)
                if ssid_match: wifi_name = ssid_match.group(1).strip()
                if radio_match: wifi_type = radio_match.group(1).strip()
            except Exception:
                pass

            vpn_detected = False
            vpn_keywords = ["wireguard", "tailscale", "zerotier", "openvpn", "tap-", "tun", "sstp", "ike"]

            for nic, stat in stats.items():
                if not stat.isup:
                    continue

                lower_nic = nic.lower()
                ip, mac = "-", "-"

                if nic in addrs:
                    for addr in addrs[nic]:
                        if addr.family == socket.AF_INET: ip = addr.address
                        elif addr.family == psutil.AF_LINK: mac = addr.address.replace('-', ':').upper()

                if any(kw in lower_nic for kw in ["wi-fi", "wifi", "wireless"]):
                    networks.append({
                        "adapter": nic, "type": "Wireless (Wi-Fi)", "name": wifi_name,
                        "standard": wifi_type, "speed": f"{stat.speed} Mbps",
                        "ip": ip, "mac": mac, "vpn": "OFF"
                    })
                elif any(kw in lower_nic for kw in vpn_keywords) and "teredo" not in lower_nic:
                    vpn_detected = True
                    networks.append({
                        "adapter": nic, "type": "VPN Tunnel", "name": nic,
                        "standard": "Secure Tunnel", "speed": f"{stat.speed} Mbps",
                        "ip": ip, "mac": mac, "vpn": "ON"
                    })
                elif "ethernet" in lower_nic:
                    networks.append({
                        "adapter": nic, "type": "Wired (Ethernet)", "name": "LAN",
                        "standard": "Wired Connection", "speed": f"{stat.speed} Mbps",
                        "ip": ip, "mac": mac, "vpn": "OFF"
                    })

            for net in networks:
                if not net["type"].startswith("VPN"):
                    net["vpn"] = "ON" if vpn_detected else "OFF"

            networks.append({
                "adapter": "System Wide", "type": "Global Status", "name": "VPN Protection",
                "standard": "Active" if vpn_detected else "Inactive", "speed": "-",
                "ip": "-", "mac": "-", "vpn": "SYSTEM"
            })
            
        except Exception:
            pass

        return networks if networks else [{"adapter": "None", "type": "Unknown", "name": "No Connection", "standard": "-", "speed": "-", "ip": "-", "mac": "-", "vpn": "-"}]

    def _format_dict(self, data: dict, child_prefix: str) -> list:
        """Helper to format dictionaries into the tree output."""
        lines = []
        keys = list(data.keys())
        for j, k in enumerate(keys):
            p = f"{child_prefix}└─" if j == len(keys)-1 else f"{child_prefix}├─"
            lines.append(f"{p} {k.capitalize():<12}: {data[k]}")
        return lines

    def _generate_category_lines(self, cat_name, cat_data, child_prefix):
        """Generates tree-formatted string lists for any category, used by CLI & Viewer."""
        lines = []
        
        if cat_name == "Operating System":
            lines.append(f"{child_prefix}├─ Name         : {cat_data['name']}")
            lines.append(f"{child_prefix}├─ Build        : {cat_data['build']}")
            lines.append(f"{child_prefix}└─ Architecture : {cat_data['arch']}")
        elif cat_name == "Device Type":
            lines.append(f"{child_prefix}└─ Type         : {cat_data}")
        elif cat_name == "Power / Battery":
            lines.append(f"{child_prefix}├─ Status       : {cat_data['status']}")
            lines.append(f"{child_prefix}└─ Level        : {cat_data['level']}")
        elif cat_name == "Motherboard":
            lines.append(f"{child_prefix}├─ Model        : {cat_data['model']}")
            lines.append(f"{child_prefix}├─ Manufacturer : {cat_data['manufacturer']}")
            lines.append(f"{child_prefix}├─ BIOS         : {cat_data['bios']}")
            lines.append(f"{child_prefix}├─ UEFI         : {cat_data['uefi']}")
            lines.append(f"{child_prefix}└─ Serial       : {cat_data['serial']}")
        elif cat_name == "Processor (CPU)":
            lines.append(f"{child_prefix}├─ Model        : {cat_data['name']}")
            lines.append(f"{child_prefix}├─ Cores/Threads: {cat_data['cores']} / {cat_data['threads']}")
            lines.append(f"{child_prefix}└─ Clock Speed  : {cat_data['clock']}")
        elif cat_name == "Memory (RAM)":
            lines.append(f"{child_prefix}├─ Total        : {cat_data['total_gib']} GiB")
            lines.append(f"{child_prefix}├─ Type/Speed   : {cat_data['type']} / {cat_data['speed']} MT/s")
            lines.append(f"{child_prefix}└─ Slots        : {cat_data['slots_used']} / {cat_data['slots_total']}")
        elif cat_name == "Monitor":
            for j, mon in enumerate(cat_data):
                is_last_mon = (j == len(cat_data) - 1)
                p = f"{child_prefix}└─" if is_last_mon else f"{child_prefix}├─"
                mon_child = f"{child_prefix}   " if is_last_mon else f"{child_prefix}│  "
                lines.append(f"{p} {mon['name']}")
                lines.append(f"{mon_child}├─ Resolution   : {mon['width']}x{mon['height']}")
                
                hz_fmt = f"{mon['hz']} Hz" if str(mon['hz']).isdigit() else str(mon['hz'])
                lines.append(f"{mon_child}└─ Refresh Rate : {hz_fmt}")
        elif cat_name == "Storage":     
            for j, drv in enumerate(cat_data):
                p = f"{child_prefix}└─" if j == len(cat_data)-1 else f"{child_prefix}├─"
                lines.append(f"{p} {drv['model']} ({drv['type']}) - {drv['size_gib']} GiB")
        elif cat_name == "Graphics (GPU)":
            gpus = [("Integrated", g) for g in cat_data["igpu"]] + [("Dedicated", g) for g in cat_data["dgpu"]]
            if not gpus:
                lines.append(f"{child_prefix}└─ None")
            else:
                for j, (g_type, g_name) in enumerate(gpus):
                    p = f"{child_prefix}└─" if j == len(gpus)-1 else f"{child_prefix}├─"
                    lines.append(f"{p} {g_type:<10}: {g_name}")
        elif cat_name == "Network (Internet)":
            for j, net in enumerate(cat_data):
                last = (j == len(cat_data) - 1)
                p = f"{child_prefix}└─" if last else f"{child_prefix}├─"
                sub = f"{child_prefix}   " if last else f"{child_prefix}│  "
                lines.append(f"{p} {net['type']} : {net['name']}")
                lines.append(f"{sub}├─ Adapter      : {net['adapter']}")
                lines.append(f"{sub}├─ Standard     : {net['standard']}")
                lines.append(f"{sub}├─ Speed        : {net['speed']}")
                lines.append(f"{sub}├─ IPv4         : {net['ip']}")
                lines.append(f"{sub}├─ MAC          : {net['mac']}")
                lines.append(f"{sub}└─ VPN          : {net['vpn']}")
        return lines

    def print_report(self):
        hostname = platform.node()
        print(f"\nHWINFO ({hostname})")
        
        categories = [
            ("Operating System", self.get_os_info()),
            ("Device Type", self.get_device_type()),
            ("Power / Battery", self.get_battery_info()),
            ("Motherboard", self.get_mainboard_info()),
            ("Processor (CPU)", self.get_cpu_info()),
            ("Memory (RAM)", self.get_ram_info()),
            ("Monitor", self.get_monitor_info()),
            ("Storage", self.get_storage_info()),
            ("Graphics (GPU)", self.get_gpu_info()),
            ("Network (Internet)", self.get_network_info())
        ]

        for i, (cat_name, cat_data) in enumerate(categories):
            is_last_cat = (i == len(categories) - 1)
            cat_prefix = "└─" if is_last_cat else "├─"
            child_prefix = "   " if is_last_cat else "│  "
            
            print(f"{cat_prefix} {cat_name}")
            lines = self._generate_category_lines(cat_name, cat_data, child_prefix)
            for line in lines:
                print(line)

class InteractiveViewer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.sections = [
            ("Operating System", analyzer.get_os_info),
            ("Device Type", analyzer.get_device_type),
            ("Power / Battery", analyzer.get_battery_info),
            ("Motherboard", analyzer.get_mainboard_info),
            ("Processor (CPU)", analyzer.get_cpu_info),
            ("Memory (RAM)", analyzer.get_ram_info),
            ("Monitor", analyzer.get_monitor_info),
            ("Storage", analyzer.get_storage_info),
            ("Graphics (GPU)", analyzer.get_gpu_info),
            ("Network (Internet)", analyzer.get_network_info)
        ]
        self.opened = [False] * len(self.sections)
        self.cursor = 0

    def clear(self):
        # Flicker-free clear using ANSI VT100 escape sequence
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()

    def render(self):
        self.clear()
        print(f"System // ({platform.node()})\n")

        for i, (name, func) in enumerate(self.sections):
            pointer = ">" if i == self.cursor else " "
            icon = "▼" if self.opened[i] else "▶"

            print(f"{pointer} {icon} {name}")

            if self.opened[i]:
                data = func()
                # Utilize the same aesthetic tree formatter from SystemAnalyzer
                lines = self.analyzer._generate_category_lines(name, data, "    ")
                for line in lines:
                    print(line)

        print("\n↑↓ Move | ENTER Open/Close | ESC Exit")

    def run(self):
        while True:
            self.render()
            key = msvcrt.getch()

            if key == b'\x1b':  # ESC
                break
            elif key == b'\r':  # ENTER
                self.opened[self.cursor] = not self.opened[self.cursor]
            elif key == b'\xe0':  # Arrow keys
                key2 = msvcrt.getch()
                if key2 == b'H':  # UP
                    self.cursor -= 1
                elif key2 == b'P':  # DOWN
                    self.cursor += 1
                self.cursor %= len(self.sections)

def cmd_hwinfo(args):
    analyzer = SystemAnalyzer()
    # By default, use the static report. If an arg like '--interactive' is provided, load viewer.
    if len(args) > 1 and args[1] == "--interactive":
        viewer = InteractiveViewer(analyzer)
        viewer.run()
    else:
        analyzer.print_report()