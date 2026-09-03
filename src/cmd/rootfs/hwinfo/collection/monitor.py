from __future__ import annotations

from ..platform import win32
from ..platform.wmi import get_monitor_wmi


def _friendly_monitor_names() -> dict[str, str]:
    friendly_names: dict[str, str] = {}
    try:
        for mon in get_monitor_wmi().query("WmiMonitorID"):
            inst = getattr(mon, "InstanceName", "") or ""
            user_name_raw = getattr(mon, "UserFriendlyName", None)
            if inst and user_name_raw:
                name_str = "".join(chr(c) for c in user_name_raw if c > 0).strip()
                if name_str:
                    key = win32.get_device_id_key(inst)
                    if key:
                        friendly_names[key] = name_str
    except Exception:
        pass
    return friendly_names


def collect_monitors() -> list[dict]:
    monitors: list[dict] = []
    friendly_names = _friendly_monitor_names()

    try:
        for adapter in win32.enum_active_display_adapters():
            monitor_name = ""
            monitor_found = False

            for mon_device in win32.enum_active_monitors(adapter.DeviceName):
                key = win32.get_device_id_key(mon_device.DeviceID or "")
                if key and key in friendly_names:
                    monitor_name = friendly_names[key]

                if (
                    not monitor_name
                    and mon_device.DeviceString
                    and mon_device.DeviceString.strip()
                ):
                    monitor_name = mon_device.DeviceString.strip()

                monitor_found = True
                break

            if not monitor_found:
                continue

            if not monitor_name:
                monitor_name = "Generic PnP Monitor"

            mode = win32.get_current_display_settings(adapter.DeviceName)
            if mode is None:
                continue

            hz_val = mode.dmDisplayFrequency
            monitors.append(
                {
                    "name": monitor_name,
                    "width": mode.dmPelsWidth,
                    "height": mode.dmPelsHeight,
                    "hz": hz_val if hz_val > 1 else "Default",
                }
            )
    except Exception:
        pass

    if not monitors:
        monitors.append(
            {"name": "Unknown Monitor", "width": "?", "height": "?", "hz": "?"}
        )

    return monitors
