
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any


# ============================================================================
# Platform helpers
# ============================================================================

try:
    from ..platform.wmi import get_system_wmi
except ImportError:
    def get_system_wmi():
        return None


try:
    from ..platform.posix import list_dir
except ImportError:
    def list_dir(path: str) -> list[str]:
        try:
            return [entry.name for entry in Path(path).iterdir()]
        except (OSError, PermissionError):
            return []


# ============================================================================
# PCI display classes
# ============================================================================

DISPLAY_CLASSES = {
    "0x030000",
    "0x030001",
    "0x030002",
    "0x030200",
}


# ============================================================================
# Helpers
# ============================================================================

def _read_file(path: str, default: str = "Unknown") -> str:
    try:
        value = Path(path).read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

        return value if value else default

    except (OSError, PermissionError):
        return default


def _readlink_basename(path: str) -> str:
    try:
        target = os.path.realpath(path)

        if not target or target == path:
            return "Unknown"

        name = os.path.basename(target)

        return name if name else "Unknown"

    except OSError:
        return "Unknown"


def _normalise_hex(value: str) -> str:
    value = str(value).strip().lower()

    if not value:
        return "Unknown"

    if value.startswith("0x"):
        return value

    if re.fullmatch(r"[0-9a-f]{4}", value):
        return f"0x{value}"

    return value


def _normalise_class(value: str) -> str:
    value = str(value).strip().lower()

    if not value:
        return "Unknown"

    if value.startswith("0x"):
        return value

    if re.fullmatch(r"[0-9a-f]{6}", value):
        return f"0x{value}"

    return value


def _is_display_class(value: str) -> bool:
    return _normalise_class(value) in DISPLAY_CLASSES


def _is_drm_card(name: str) -> bool:
    return bool(re.fullmatch(r"card\d+", name))


# ============================================================================
# PCI information
# ============================================================================

def _get_pci_address(card: str) -> str:
    path = Path(f"/sys/class/drm/{card}/device")

    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return "Unknown"

    pci_address = resolved.name

    if re.fullmatch(
        r"[0-9a-fA-F]{4}:"
        r"[0-9a-fA-F]{2}:"
        r"[0-9a-fA-F]{2}\."
        r"[0-9a-fA-F]",
        pci_address,
    ):
        return pci_address

    return "Unknown"


# ============================================================================
# GPU name resolution
# ============================================================================

def _clean_gpu_name(name: str) -> str:
    name = str(name).strip()

    if not name:
        return "Unknown GPU"

    # Remove PCI revision suffix.
    name = re.sub(
        r"\s*\(rev\s+[0-9a-f]+\)\s*$",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    # Prefer a useful model name inside brackets.
    bracketed = re.findall(
        r"\[([^\]]+)\]",
        name,
    )

    for candidate in bracketed:
        candidate = candidate.strip()

        if not candidate:
            continue

        # Ignore generic metadata such as [AMD/ATI].
        if "/" in candidate:
            continue

        return candidate

    # Remove generic PCI class prefix.
    name = re.sub(
        r"^(?:VGA compatible controller|"
        r"3D controller|"
        r"Display controller):\s*",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip()

    # Generic manufacturer cleanup.
    if " Corporation " in name:
        candidate = name.split(
            " Corporation ",
            1,
        )[1].strip()

        if candidate:
            name = candidate

    elif " Inc. " in name:
        candidate = name.split(
            " Inc. ",
            1,
        )[1].strip()

        if candidate:
            name = candidate

    return name or "Unknown GPU"


def _resolve_with_lspci(pci_address: str) -> str:
    if pci_address == "Unknown":
        return "Unknown"

    try:
        result = subprocess.run(
            [
                "lspci",
                "-s",
                pci_address,
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "Unknown"

    line = result.stdout.strip()

    if not line or ": " not in line:
        return "Unknown"

    name = line.split(": ", 1)[1].strip()

    return _clean_gpu_name(name)


def _resolve_with_pci_ids(
    vendor_id: str,
    device_id: str,
) -> str:
    vendor_hex = _normalise_hex(
        vendor_id
    ).removeprefix("0x")

    device_hex = _normalise_hex(
        device_id
    ).removeprefix("0x")

    if (
        vendor_hex == "Unknown"
        or device_hex == "Unknown"
    ):
        return "Unknown"

    database_paths = (
        "/usr/share/hwdata/pci.ids",
        "/usr/share/pci.ids",
    )

    for database_path in database_paths:
        path = Path(database_path)

        if not path.is_file():
            continue

        try:
            lines = path.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
        except (OSError, PermissionError):
            continue

        in_vendor = False

        for line in lines:
            if re.fullmatch(
                rf"{re.escape(vendor_hex)}\s+.+",
                line,
                flags=re.IGNORECASE,
            ):
                in_vendor = True
                continue

            if (
                in_vendor
                and line
                and not line.startswith("\t")
            ):
                break

            if not in_vendor:
                continue

            match = re.fullmatch(
                rf"\t{re.escape(device_hex)}\s+(.+)",
                line,
                flags=re.IGNORECASE,
            )

            if match:
                return _clean_gpu_name(
                    match.group(1).strip()
                )

    return "Unknown"


def _resolve_gpu_name(
    pci_address: str,
    vendor_id: str,
    device_id: str,
) -> str:
    name = _resolve_with_lspci(
        pci_address
    )

    if name != "Unknown":
        return name

    name = _resolve_with_pci_ids(
        vendor_id,
        device_id,
    )

    if name != "Unknown":
        return name

    return (
        "PCI GPU ["
        f"{_normalise_hex(vendor_id)}:"
        f"{_normalise_hex(device_id)}"
        "]"
    )


# ============================================================================
# Primary / classification
# ============================================================================

def _get_primary(card: str) -> bool | None:
    value = _read_file(
        f"/sys/class/drm/{card}/device/boot_vga",
        "",
    )

    if value == "1":
        return True

    if value == "0":
        return False

    return None


def _get_gpu_type(card: str) -> str:
    """
    Do not guess Integrated/Discrete from:
    - vendor
    - device ID
    - model
    - driver
    - boot_vga
    """
    _ = card
    return "Unknown"


# ============================================================================
# Linux
# ============================================================================

def _collect_linux_gpus() -> list[dict[str, Any]]:
    gpus: list[dict[str, Any]] = []

    for card in sorted(
        list_dir("/sys/class/drm")
    ):
        if not _is_drm_card(card):
            continue

        device_root = (
            f"/sys/class/drm/{card}/device"
        )

        pci_class = _read_file(
            f"{device_root}/class",
            "Unknown",
        )

        if not _is_display_class(pci_class):
            continue

        vendor_id = _read_file(
            f"{device_root}/vendor",
            "Unknown",
        )

        device_id = _read_file(
            f"{device_root}/device",
            "Unknown",
        )

        if (
            vendor_id == "Unknown"
            or device_id == "Unknown"
        ):
            continue

        vendor_id = _normalise_hex(
            vendor_id
        )

        device_id = _normalise_hex(
            device_id
        )

        pci_class = _normalise_class(
            pci_class
        )

        pci_address = _get_pci_address(card)

        driver = _readlink_basename(
            f"{device_root}/driver"
        )

        primary = _get_primary(card)

        gpu_type = _get_gpu_type(card)

        name = _resolve_gpu_name(
            pci_address,
            vendor_id,
            device_id,
        )

        gpus.append(
            {
                "name": name,
                "vendor_id": vendor_id,
                "device_id": device_id,
                "pci_address": pci_address,
                "class": pci_class,
                "driver": driver,
                "card": card,
                "type": gpu_type,
                "primary": primary,
            }
        )

    return gpus


# ============================================================================
# Windows
# ============================================================================

def _collect_windows_gpus() -> list[dict[str, Any]]:
    gpus: list[dict[str, Any]] = []

    try:
        wmi = get_system_wmi()

        if not wmi:
            return gpus

        controllers = wmi.query(
            "Win32_VideoController"
        )

        if not controllers:
            return gpus

        seen: set[str] = set()

        for controller in controllers:
            name = getattr(
                controller,
                "Name",
                None,
            )

            if name:
                name = str(name).strip()
            else:
                name = "Unknown GPU"

            pnp_id = getattr(
                controller,
                "PNPDeviceID",
                None,
            )

            if pnp_id:
                pnp_id = str(pnp_id).strip()
            else:
                pnp_id = "Unknown"

            unique_key = (
                f"{name}|{pnp_id}"
            )

            if unique_key in seen:
                continue

            seen.add(unique_key)

            driver = getattr(
                controller,
                "DriverVersion",
                None,
            )

            if driver:
                driver = str(driver).strip()
            else:
                driver = "Unknown"

            gpus.append(
                {
                    "name": name,
                    "vendor_id": "Unknown",
                    "device_id": "Unknown",
                    "pci_address": "Unknown",
                    "class": "Unknown",
                    "driver": driver,
                    "card": "Unknown",
                    "type": "Unknown",
                    "primary": None,
                    "pnp_device_id": pnp_id,
                }
            )

    except Exception:
        pass

    return gpus


# ============================================================================
# Public API
# ============================================================================

def collect_gpu() -> dict[str, Any]:
    if os.name == "nt":
        gpus = _collect_windows_gpus()
    else:
        gpus = _collect_linux_gpus()

    result: dict[str, Any] = {
        "gpus": gpus,
        "igpu": [],
        "dgpu": [],
        "unknown": [],
    }

    for gpu in gpus:
        gpu_type = gpu.get("type")

        if gpu_type == "Integrated":
            result["igpu"].append(gpu)
        elif gpu_type == "Discrete":
            result["dgpu"].append(gpu)
        else:
            result["unknown"].append(gpu)

    return result