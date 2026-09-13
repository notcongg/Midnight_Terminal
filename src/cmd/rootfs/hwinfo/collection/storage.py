from __future__ import annotations

from pathlib import Path


SYS_BLOCK = Path("/sys/class/block")


def _read(path: Path, default: str = "Unknown") -> str:
    try:
        value = path.read_text().strip()
        return value if value else default
    except (OSError, PermissionError):
        return default


def _size_gib(device: Path) -> float:
    raw = _read(device / "size", "0")

    try:
        sectors = int(raw)
    except ValueError:
        return 0.0

    if sectors <= 0:
        return 0.0

    # Linux block device size is reported in 512-byte sectors.
    return round(
        (sectors * 512) / (1024 ** 3),
        2,
    )


def _is_partition(device: Path) -> bool:
    return (device / "partition").exists()


def _is_virtual(device: Path) -> bool:
    name = device.name

    return name.startswith(
        (
            "loop",
            "ram",
            "zram",
            "sr",
            "fd",
            "dm-",
        )
    )


def _get_model(device: Path) -> str:
    model = _read(
        device / "device" / "model",
        "",
    )

    if model and model != "Unknown":
        return model.strip()

    # NVMe fallback
    try:
        real_device = (device / "device").resolve()

        for path in real_device.parents:
            candidate = path / "model"

            if candidate.is_file():
                value = _read(candidate, "").strip()

                if value:
                    return value
    except OSError:
        pass

    return "Unknown Drive"


def _get_bus_type(device: Path) -> str:
    try:
        real_device = (device / "device").resolve()
    except OSError:
        return "Unknown"

    path = str(real_device).lower()

    if "nvme" in path:
        return "NVMe"

    if "ata" in path or "ahci" in path:
        return "SATA"

    if "usb" in path:
        return "USB"

    if "mmc" in path:
        return "MMC"

    if "virtio" in path:
        return "VirtIO"

    if "scsi" in path:
        return "SCSI"

    return "Unknown"


def collect_storage() -> list[dict]:
    """
    Collect physical storage devices on Linux.

    Uses sysfs directly.
    No sudo, C++, DLL, or external command required.
    """

    drives: list[dict] = []

    if not SYS_BLOCK.is_dir():
        return [
            {
                "type": "Unknown",
                "model": "Unknown Drive",
                "size_gib": 0,
            }
        ]

    for device in SYS_BLOCK.iterdir():
        if not device.exists():
            continue

        if _is_virtual(device):
            continue

        if _is_partition(device):
            continue

        size_gib = _size_gib(device)

        if size_gib <= 0:
            continue

        model = _get_model(device)
        bus = _get_bus_type(device)

        drives.append(
            {
                "type": bus,
                "model": model,
                "size_gib": size_gib,
            }
        )

    if not drives:
        return [
            {
                "type": "Unknown",
                "model": "Unknown Drive",
                "size_gib": 0,
            }
        ]

    return drives