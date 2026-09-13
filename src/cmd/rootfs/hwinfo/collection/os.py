from __future__ import annotations

import os
import platform

try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None


try:
    from ..platform.posix import etc
except ImportError:
    def etc(path: str, default: str = "Unknown") -> str:
        return default


def _parse_os_release(content: str) -> dict[str, str]:
    """Parse /etc/os-release into a simple dictionary."""
    values: dict[str, str] = {}

    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        values[key] = value

    return values


def collect_os() -> dict[str, str]:
    """
    Collect operating system information.

    Returns:
        A dictionary containing:
            - name
            - build
            - arch
    """

    info = {
        "name": "Unknown",
        "build": "Unknown",
        "arch": "Unknown",
    }

    # Windows
    if os.name == "nt":
        try:
            wmi = get_system_wmi()

            if not wmi:
                return info

            operating_systems = wmi.query(
                "Win32_OperatingSystem"
            )

            if not operating_systems:
                return info

            operating_system = operating_systems[0]

            caption = getattr(
                operating_system,
                "Caption",
                None,
            )

            build = getattr(
                operating_system,
                "BuildNumber",
                None,
            )

            architecture = getattr(
                operating_system,
                "OSArchitecture",
                None,
            )

            if caption:
                info["name"] = str(caption).strip()

            if build:
                info["build"] = str(build).strip()

            if architecture:
                info["arch"] = str(architecture).strip()

        except Exception:
            # Hardware information should never crash HWINFO.
            pass

        return info

    # POSIX / Linux
    try:
        release = etc("os-release", "")

        if release:
            values = _parse_os_release(release)

            name = values.get("PRETTY_NAME") or values.get("NAME")
            build = (
                values.get("BUILD_ID")
                or values.get("VERSION_ID")
                or values.get("VERSION")
            )

            if name:
                info["name"] = name

            if build:
                info["build"] = build

        architecture = platform.machine()

        if architecture:
            info["arch"] = architecture.strip()

    except Exception:
        # Hardware information should never crash HWINFO.
        pass

    return info