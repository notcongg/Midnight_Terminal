import os
import platform

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


class SystemAnalyzer:
    def get_os_info(self) -> dict:
        return collect_os()

    def get_device_type(self) -> str:
        return collect_device_type()

    def get_battery_info(self) -> dict:
        return collect_battery()

    def get_mainboard_info(self) -> dict:
        return collect_mainboard()

    def get_cpu_info(self) -> dict:
        return collect_cpu()

    def get_ram_info(self) -> dict:
        return collect_ram()

    def get_monitor_info(self) -> list:
        return collect_monitors()

    def get_storage_info(self) -> list:
        return collect_storage()

    def get_gpu_info(self) -> dict:
        return collect_gpu()

    def get_network_info(self) -> list:
        return collect_network()

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


def cmd_hwinfo(args, context=None):
    analyzer = SystemAnalyzer()
    analyzer.print_report()
