
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


try:
    from ..platform import win32
except ImportError:
    win32 = None


try:
    from ..platform.posix import list_dir
except ImportError:
    def list_dir(path: str) -> list[str]:
        try:
            return [p.name for p in Path(path).iterdir()]
        except (OSError, PermissionError):
            return []


# ============================================================================
# Generic helpers
# ============================================================================

def _read_file(path: str, default: str = "") -> str:
    try:
        value = Path(path).read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

        return value if value else default

    except (OSError, PermissionError):
        return default


def _read_bytes(path: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except (OSError, PermissionError):
        return b""


# ============================================================================
# EDID helpers
# ============================================================================

def _decode_manufacturer(edid: bytes) -> str:
    if len(edid) < 10:
        return "Unknown"

    word = (edid[8] << 8) | edid[9]

    chars = [
        ((word >> 10) & 0x1F) + 0x40,
        ((word >> 5) & 0x1F) + 0x40,
        (word & 0x1F) + 0x40,
    ]

    try:
        result = "".join(chr(c) for c in chars)
    except ValueError:
        return "Unknown"

    if not re.fullmatch(r"[A-Z]{3}", result):
        return "Unknown"

    return result


def _decode_descriptor_text(block: bytes) -> str:
    """
    Decode an EDID monitor descriptor text block.
    """
    text = block[5:18]

    text = bytes(
        c for c in text
        if c not in (0x00, 0x0A)
    )

    try:
        return text.decode(
            "ascii",
            errors="ignore",
        ).strip()
    except UnicodeDecodeError:
        return ""


def _decode_monitor_name(edid: bytes) -> str:
    """
    Descriptor type 0xFC = monitor name.
    """
    if len(edid) < 126:
        return ""

    # Base EDID has four 18-byte descriptors.
    for offset in (54, 72, 90, 108):
        descriptor = edid[offset:offset + 18]

        if len(descriptor) < 18:
            continue

        if (
            descriptor[0:2] == b"\x00\x00"
            and descriptor[3] == 0xFC
        ):
            name = _decode_descriptor_text(
                descriptor
            )

            if name:
                return name

    return ""


def _decode_product_code(edid: bytes) -> int | None:
    if len(edid) < 12:
        return None

    return edid[10] | (edid[11] << 8)


def _decode_serial(edid: bytes) -> int | None:
    if len(edid) < 16:
        return None

    return (
        edid[12]
        | (edid[13] << 8)
        | (edid[14] << 16)
        | (edid[15] << 24)
    )


def _decode_preferred_timing(
    edid: bytes,
) -> tuple[int, int, float] | None:
    """
    Decode the first detailed timing descriptor.

    Returns:
        width, height, refresh_hz
    """
    if len(edid) < 126:
        return None

    for offset in (54, 72, 90, 108):
        descriptor = edid[offset:offset + 18]

        if len(descriptor) < 18:
            continue

        # Pixel clock, 10 kHz units.
        pixel_clock_raw = (
            descriptor[0]
            | (descriptor[1] << 8)
        )

        if pixel_clock_raw == 0:
            continue

        pixel_clock = pixel_clock_raw * 10000.0

        h_active = (
            descriptor[2]
            | ((descriptor[4] & 0xF0) << 4)
        )

        h_blanking = (
            descriptor[3]
            | ((descriptor[4] & 0x0F) << 8)
        )

        v_active = (
            descriptor[5]
            | ((descriptor[7] & 0xF0) << 4)
        )

        v_blanking = (
            descriptor[6]
            | ((descriptor[7] & 0x0F) << 8)
        )

        h_total = h_active + h_blanking
        v_total = v_active + v_blanking

        if (
            h_total <= 0
            or v_total <= 0
        ):
            continue

        refresh = (
            pixel_clock
            / (h_total * v_total)
        )

        return (
            h_active,
            v_active,
            refresh,
        )

    return None


def _parse_edid(
    edid: bytes,
) -> dict[str, object]:
    info: dict[str, object] = {
        "manufacturer": "Unknown",
        "name": "",
        "product": None,
        "serial": None,
        "width": None,
        "height": None,
        "hz": None,
    }

    if len(edid) < 128:
        return info

    # Validate EDID header.
    if edid[:8] != bytes(
        [0x00, 0xFF, 0xFF, 0xFF,
         0xFF, 0xFF, 0xFF, 0x00]
    ):
        return info

    info["manufacturer"] = _decode_manufacturer(
        edid
    )

    info["name"] = _decode_monitor_name(
        edid
    )

    info["product"] = _decode_product_code(
        edid
    )

    info["serial"] = _decode_serial(
        edid
    )

    timing = _decode_preferred_timing(
        edid
    )

    if timing:
        width, height, hz = timing

        info["width"] = width
        info["height"] = height
        info["hz"] = hz

    return info


# ============================================================================
# Resolution helpers
# ============================================================================

def _parse_mode(mode: str) -> tuple[int, int] | None:
    match = re.fullmatch(
        r"(\d+)x(\d+)",
        mode.strip(),
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


def _get_drm_mode(
    connector: str,
) -> tuple[int, int] | None:
    """
    DRM exposes modes like:

        2560x1440
        1920x1080
    """
    modes = _read_file(
        f"/sys/class/drm/{connector}/modes",
        "",
    )

    if not modes:
        return None

    for line in modes.splitlines():
        parsed = _parse_mode(line)

        if parsed:
            return parsed

    return None


# ============================================================================
# KDE Wayland refresh-rate detection
# ============================================================================

def _get_kscreen_monitors() -> list[dict]:
    """
    Try KDE's KScreen command-line interface.

    This is optional. DRM remains the primary source for monitor
    detection.

    Example output contains blocks such as:

        Output: 1
          name: "..."
          currentMode: "2560x1440@60.00"
    """
    try:
        result = subprocess.run(
            [
                "kscreen-doctor",
                "-o",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return []

    if result.returncode != 0:
        return []

    output = result.stdout

    if not output.strip():
        return []

    monitors: list[dict] = []

    current: dict | None = None

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if line.startswith("Output:"):
            if current:
                monitors.append(current)

            current = {}

            continue

        if current is None:
            continue

        mode_match = re.search(
            r"currentMode:\s*[\"']?"
            r"(\d+)x(\d+)@"
            r"([\d.]+)",
            line,
            flags=re.IGNORECASE,
        )

        if mode_match:
            current["width"] = int(
                mode_match.group(1)
            )
            current["height"] = int(
                mode_match.group(2)
            )
            current["hz"] = float(
                mode_match.group(3)
            )

            continue

        name_match = re.search(
            r"(?:name|model|displayName):\s*"
            r"[\"'](.+?)[\"']$",
            line,
            flags=re.IGNORECASE,
        )

        if name_match:
            current["name"] = (
                name_match.group(1).strip()
            )

    if current:
        monitors.append(current)

    return monitors


# ============================================================================
# Linux
# ============================================================================

def _collect_linux_monitors() -> list[dict]:
    monitors: list[dict] = []

    kscreen_monitors = (
        _get_kscreen_monitors()
    )

    drm_connectors = []

    for entry in list_dir("/sys/class/drm"):
        if "-" not in entry:
            continue

        if not re.match(
            r"^card\d+-",
            entry,
        ):
            continue

        drm_connectors.append(entry)

    for connector in sorted(
        drm_connectors
    ):
        status = _read_file(
            f"/sys/class/drm/{connector}/status",
            "",
        ).lower()

        if status != "connected":
            continue

        edid = _read_bytes(
            f"/sys/class/drm/{connector}/edid"
        )

        edid_info = _parse_edid(
            edid
        )

        name = str(
            edid_info.get(
                "name",
                "",
            )
        ).strip()

        manufacturer = str(
            edid_info.get(
                "manufacturer",
                "Unknown",
            )
        ).strip()

        # Preferred name.
        if not name:
            if manufacturer != "Unknown":
                name = (
                    f"{manufacturer} Monitor"
                )
            else:
                name = "Generic Monitor"

        mode = _get_drm_mode(
            connector
        )

        width = (
            mode[0]
            if mode
            else edid_info.get("width")
        )

        height = (
            mode[1]
            if mode
            else edid_info.get("height")
        )

        hz = edid_info.get("hz")

        # Try to match KDE's exact current mode.
        # This is useful on KDE Wayland where the currently
        # selected mode may differ from the preferred EDID mode.
        if kscreen_monitors:
            for kmon in kscreen_monitors:
                k_width = kmon.get("width")
                k_height = kmon.get("height")

                if (
                    width is not None
                    and height is not None
                    and k_width == width
                    and k_height == height
                ):
                    if kmon.get("hz") is not None:
                        hz = kmon["hz"]

                    if kmon.get("name"):
                        name = str(
                            kmon["name"]
                        ).strip()

                    break

        if hz is None:
            hz = "Unknown"

        if isinstance(hz, float):
            if hz.is_integer():
                hz = int(hz)

        monitors.append(
            {
                "name": name,
                "width": (
                    width
                    if width is not None
                    else "?"
                ),
                "height": (
                    height
                    if height is not None
                    else "?"
                ),
                "hz": hz,
                "connector": connector,
                "manufacturer": manufacturer,
                "product": edid_info.get(
                    "product"
                ),
            }
        )

    return monitors


# ============================================================================
# Windows
# ============================================================================

def _friendly_monitor_names() -> dict[str, str]:
    friendly_names: dict[str, str] = {}

    if win32 is None:
        return friendly_names

    try:
        wmi = get_monitor_wmi()

        if not wmi:
            return friendly_names

        for mon in wmi.query(
            "WmiMonitorID"
        ):
            inst = (
                getattr(
                    mon,
                    "InstanceName",
                    "",
                )
                or ""
            )

            user_name_raw = getattr(
                mon,
                "UserFriendlyName",
                None,
            )

            if not inst or not user_name_raw:
                continue

            name_str = "".join(
                chr(c)
                for c in user_name_raw
                if c > 0
            ).strip()

            if not name_str:
                continue

            key = win32.get_device_id_key(
                inst
            )

            if key:
                friendly_names[key] = name_str

    except Exception:
        pass

    return friendly_names


def _collect_windows_monitors() -> list[dict]:
    monitors: list[dict] = []

    if win32 is None:
        return monitors

    friendly_names = (
        _friendly_monitor_names()
    )

    try:
        adapters = (
            win32.enum_active_display_adapters()
        )

        for adapter in adapters:
            monitor_name = ""
            monitor_found = False

            for mon_device in (
                win32.enum_active_monitors(
                    adapter.DeviceName
                )
            ):
                key = win32.get_device_id_key(
                    mon_device.DeviceID or ""
                )

                if (
                    key
                    and key in friendly_names
                ):
                    monitor_name = (
                        friendly_names[key]
                    )

                if (
                    not monitor_name
                    and mon_device.DeviceString
                    and mon_device.DeviceString.strip()
                ):
                    monitor_name = (
                        mon_device.DeviceString.strip()
                    )

                monitor_found = True
                break

            if not monitor_found:
                continue

            if not monitor_name:
                monitor_name = (
                    "Generic PnP Monitor"
                )

            mode = (
                win32.get_current_display_settings(
                    adapter.DeviceName
                )
            )

            if mode is None:
                continue

            hz_val = mode.dmDisplayFrequency

            monitors.append(
                {
                    "name": monitor_name,
                    "width": mode.dmPelsWidth,
                    "height": mode.dmPelsHeight,
                    "hz": (
                        hz_val
                        if hz_val > 1
                        else "Default"
                    ),
                }
            )

    except Exception:
        pass

    return monitors


# ============================================================================
# Public collector
# ============================================================================

def collect_monitors() -> list[dict]:
    """
    Cross-platform monitor collector.

    Windows:
        Win32 display APIs + WMI

    Linux:
        DRM/sysfs + EDID + optional KDE KScreen
    """
    try:
        if os.name == "nt":
            monitors = (
                _collect_windows_monitors()
            )
        else:
            monitors = (
                _collect_linux_monitors()
            )

    except Exception:
        monitors = []

    if not monitors:
        return [
            {
                "name": "Unknown Monitor",
                "width": "?",
                "height": "?",
                "hz": "?",
            }
        ]

    return monitors