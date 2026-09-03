from __future__ import annotations

from ..platform.wmi import get_system_wmi


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

    try:
        operating_systems = get_system_wmi().query(
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
