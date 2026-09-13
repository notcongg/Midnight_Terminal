import os
import platform
import subprocess

from .collection.board import collect_mainboard
from .collection.cpu import collect_cpu
from .collection.device import collect_battery, collect_device_type
from .collection.gpu import collect_gpu
from .collection.monitor import collect_monitors
from .collection.network import collect_network
from .collection.os import collect_os
from .collection.ram import collect_ram
from .collection.storage import collect_storage

# Enable ANSI escape code support on Windows 10/11
os.system("")

def man_hwinfo() -> str:
    return """HWINFO(1)                Midnight Terminal Manual               HWINFO(1)

NAME
    hwinfo - display hardware information

SYNOPSIS
    hwinfo [OPTIONS]

DESCRIPTION
    Shows detailed information about the system hardware including
    CPU, RAM, storage, GPU, network, motherboard and more.

OPTIONS
    --type=<type>    Filter by category (e.g. ram, cpu, gpu, storage, os).
    --root           Run commands with sudo to unlock full hardware specs
                     (such as RAM speed, Disk topologies on Linux).

EXAMPLES
    hwinfo
    hwinfo --type=ram
    hwinfo --root

SEE ALSO
    task(1), ps(1), date(1)
"""

class SystemAnalyzer:
    def __init__(self, as_root: bool = False):
        self.as_root = as_root

    def get_os_info(self) -> dict: return collect_os()
    def get_device_type(self) -> str: return collect_device_type()
    def get_battery_info(self) -> dict: return collect_battery()
    def get_mainboard_info(self) -> dict: return collect_mainboard()
    def get_cpu_info(self) -> dict: return collect_cpu()
    def get_ram_info(self) -> dict: 
        # Pass the as_root flag down so it can invoke 'sudo dmidecode' if needed
        try:
            return collect_ram(as_root=self.as_root)
        except TypeError:
            # Fallback if old collect_ram is somehow loaded
            return collect_ram()
    def get_monitor_info(self) -> list: return collect_monitors()
    def get_storage_info(self) -> list: return collect_storage()
    def get_gpu_info(self) -> dict: return collect_gpu()
    def get_network_info(self) -> list: return collect_network()

    def _generate_category_lines(self, cat_name, cat_data, child_prefix):
        lines = []

        if cat_name == "Operating System":
            lines.append(f"{child_prefix}├─ Name         : {cat_data.get('name', 'Unknown')}")
            lines.append(f"{child_prefix}├─ Build        : {cat_data.get('build', 'Unknown')}")
            lines.append(f"{child_prefix}└─ Architecture : {cat_data.get('arch', 'Unknown')}")

        elif cat_name == "Device Type":
            lines.append(f"{child_prefix}└─ Type         : {cat_data}")

        elif cat_name == "Power / Battery":
            lines.append(f"{child_prefix}├─ Status       : {cat_data.get('status', 'Unknown')}")
            lines.append(f"{child_prefix}└─ Level        : {cat_data.get('level', 'Unknown')}")

        elif cat_name == "Motherboard":
            lines.append(f"{child_prefix}├─ Model        : {cat_data.get('model', 'Unknown')}")
            lines.append(f"{child_prefix}├─ Manufacturer : {cat_data.get('manufacturer', 'Unknown')}")
            lines.append(f"{child_prefix}├─ BIOS         : {cat_data.get('bios', 'Unknown')}")
            lines.append(f"{child_prefix}├─ UEFI         : {cat_data.get('uefi', 'Unknown')}")
            lines.append(f"{child_prefix}└─ Serial       : {cat_data.get('serial', 'Unknown')}")

        elif cat_name == "Processor (CPU)":
            lines.append(f"{child_prefix}├─ Model        : {cat_data.get('name', 'Unknown')}")
            lines.append(f"{child_prefix}├─ Cores/Threads: {cat_data.get('cores', 'Unknown')} / {cat_data.get('threads', 'Unknown')}")
            lines.append(f"{child_prefix}└─ Clock Speed  : {cat_data.get('clock', 'Unknown')}")

        elif cat_name == "Memory (RAM)":
            total = cat_data.get('total_gib', 'Unknown')
            speed = cat_data.get('speed', 'Unknown')
            ram_type = cat_data.get('type', 'Unknown')
            slots_used = cat_data.get('slots_used', 0)
            slots_total = cat_data.get('slots_total', 'Unknown')

            # Clean UI Formatting
            speed_str = f"{speed} MT/s" if speed != "Unknown" else "Unknown"
            slots_str = f"{slots_used} / {slots_total}" if (slots_used != 0 or slots_total != "Unknown") else "Unknown"

            lines.append(f"{child_prefix}├─ Total        : {total} GiB")
            lines.append(f"{child_prefix}├─ Type/Speed   : {ram_type} / {speed_str}")
            lines.append(f"{child_prefix}└─ Slots        : {slots_str}")

        elif cat_name == "Monitor":
            for j, mon in enumerate(cat_data):
                is_last_mon = (j == len(cat_data) - 1)
                p = f"{child_prefix}└─" if is_last_mon else f"{child_prefix}├─"
                mon_child = f"{child_prefix}   " if is_last_mon else f"{child_prefix}│  "
                lines.append(f"{p} {mon.get('name', 'Unknown')}")
                lines.append(f"{mon_child}├─ Resolution   : {mon.get('width', '?')}x{mon.get('height', '?')}")
                hz = mon.get('hz', 'Unknown')
                hz_fmt = f"{hz} Hz" if str(hz).replace(".", "").isdigit() else str(hz)
                lines.append(f"{mon_child}└─ Refresh Rate : {hz_fmt}")

        elif cat_name == "Storage":
            for j, drv in enumerate(cat_data):
                p = f"{child_prefix}└─" if j == len(cat_data) - 1 else f"{child_prefix}├─"
                size = drv.get('size_gib', 'Unknown')
                size_str = f"{size} GiB" if size != "Unknown" and size > 0 else "Unknown Capacity"
                lines.append(f"{p} {drv.get('model', 'Unknown Drive')} ({drv.get('type', 'Unknown')}) - {size_str}")

        elif cat_name == "Graphics (GPU)":
            gpus = cat_data.get("gpus", [])
            if not gpus:
                lines.append(f"{child_prefix}└─ None / Unknown")
            else:
                for j, gpu in enumerate(gpus):
                    is_last_gpu = (j == len(gpus) - 1)
                    p = f"{child_prefix}└─" if is_last_gpu else f"{child_prefix}├─"
                    gpu_child = f"{child_prefix}   " if is_last_gpu else f"{child_prefix}│  "

                    name = gpu.get("name", "Unknown GPU")
                    primary_val = gpu.get("primary", None)
                    primary_text = "Yes" if primary_val is True else "No" if primary_val is False else "Unknown"

                    lines.append(f"{p} {name}")
                    lines.append(f"{gpu_child}├─ Type         : {gpu.get('type', 'Unknown')}")
                    lines.append(f"{gpu_child}├─ PCI          : {gpu.get('pci_address', 'Unknown')}")
                    lines.append(f"{gpu_child}├─ Vendor ID    : {gpu.get('vendor_id', 'Unknown')}")
                    lines.append(f"{gpu_child}├─ Device ID    : {gpu.get('device_id', 'Unknown')}")
                    lines.append(f"{gpu_child}├─ Class        : {gpu.get('class', 'Unknown')}")
                    lines.append(f"{gpu_child}├─ Driver       : {gpu.get('driver', 'Unknown')}")
                    lines.append(f"{gpu_child}└─ Primary      : {primary_text}")

        elif cat_name == "Network (Internet)":
            for j, net in enumerate(cat_data):
                last = (j == len(cat_data) - 1)
                p = f"{child_prefix}└─" if last else f"{child_prefix}├─"
                sub = f"{child_prefix}   " if last else f"{child_prefix}│  "
                lines.append(f"{p} {net.get('type', 'Unknown')} : {net.get('name', 'Unknown')}")
                lines.append(f"{sub}├─ Adapter      : {net.get('adapter', 'Unknown')}")
                lines.append(f"{sub}├─ Standard     : {net.get('standard', 'Unknown')}")
                lines.append(f"{sub}├─ Speed        : {net.get('speed', 'Unknown')}")
                lines.append(f"{sub}├─ IPv4         : {net.get('ip', 'Unknown')}")
                lines.append(f"{sub}├─ MAC          : {net.get('mac', 'Unknown')}")
                lines.append(f"{sub}└─ VPN          : {net.get('vpn', 'Unknown')}")

        return lines

    def print_report(self, filter_type: str = None):
        hostname = platform.node()

        print(f"\nHWINFO ({hostname})")

        collectors = {
            "operating system": (
                "Operating System",
                self.get_os_info,
            ),
            "device type": (
                "Device Type",
                self.get_device_type,
            ),
            "power / battery": (
                "Power / Battery",
                self.get_battery_info,
            ),
            "motherboard": (
                "Motherboard",
                self.get_mainboard_info,
            ),
            "processor (cpu)": (
                "Processor (CPU)",
                self.get_cpu_info,
            ),
            "memory (ram)": (
                "Memory (RAM)",
                self.get_ram_info,
            ),
            "monitor": (
                "Monitor",
                self.get_monitor_info,
            ),
            "storage": (
                "Storage",
                self.get_storage_info,
            ),
            "graphics (gpu)": (
                "Graphics (GPU)",
                self.get_gpu_info,
            ),
            "network (internet)": (
                "Network (Internet)",
                self.get_network_info,
            ),
        }

        aliases = {
            "os": "operating system",
            "board": "motherboard",
            "cpu": "processor (cpu)",
            "ram": "memory (ram)",
            "memory": "memory (ram)",
            "vga": "graphics (gpu)",
            "gpu": "graphics (gpu)",
            "net": "network (internet)",
            "network": "network (internet)",
            "disk": "storage",
            "storage": "storage",
            "display": "monitor",
        }

        # ---------------------------------------------------------------
        # Determine which collectors should actually run.
        # ---------------------------------------------------------------
        if filter_type:
            target = filter_type.lower()
            target = aliases.get(target, target)

            selected = [
                collectors[key]
                for key in collectors
                if target in key
            ]

            if not selected:
                print(
                    f"Error: Unknown hardware category "
                    f"'{filter_type}'."
                )
                return
        else:
            selected = list(collectors.values())

        # ---------------------------------------------------------------
        # Collect only what is needed.
        # ---------------------------------------------------------------
        categories = []

        for name, collector in selected:
            categories.append(
                (name, collector())
            )

        # ---------------------------------------------------------------
        # Print report.
        # ---------------------------------------------------------------
        for i, (cat_name, cat_data) in enumerate(categories):
            is_last_cat = i == len(categories) - 1

            cat_prefix = (
                "└─"
                if is_last_cat
                else "├─"
            )

            child_prefix = (
                "   "
                if is_last_cat
                else "│  "
            )

            print(
                f"{cat_prefix} {cat_name}"
            )

            lines = self._generate_category_lines(
                cat_name,
                cat_data,
                child_prefix,
            )

            for line in lines:
                print(line)

        if not self.as_root and os.name != "nt":
            print("\n  \033[90m* Note: Run 'hwinfo --root' to unlock full hardware topology specs.\033[0m")

def cmd_hwinfo(args, context=None):
    if "--help" in args or "-h" in args:
        print(man_hwinfo())
        return

    as_root = False
    filter_type = None

    # Parse arguments
    for arg in args:
        if arg.startswith("--type="):
            filter_type = arg.split("=", 1)[1].strip()

    if "--root" in args:
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            print("\033[93m[System] Requesting sudo privileges to read low-level hardware tables...\033[0m")
            # Cache sudo credentials upfront so subprocesses don't hang waiting for password
            auth = subprocess.run(["sudo", "-v"])
            if auth.returncode == 0:
                as_root = True
            else:
                print("\033[91m[Error] Authentication failed. Continuing with standard permissions.\033[0m")
        else:
            as_root = True # Already running as root

    analyzer = SystemAnalyzer(as_root=as_root)
    analyzer.print_report(filter_type=filter_type)