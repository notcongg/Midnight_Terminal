from __future__ import annotations

from ..platform.powershell import run_json_or_none


def collect_storage() -> list[dict]:
    drives: list[dict] = []
    script = (
        "Get-PhysicalDisk | Select-Object Model, Size, MediaType, BusType "
        "| ConvertTo-Json -Compress"
    )
    data = run_json_or_none(script)
    try:
        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list):
            for disk in data:
                model = (
                    str(disk.get("Model", "Unknown")).strip()
                    if disk.get("Model")
                    else "Unknown Storage"
                )
                bus = (
                    str(disk.get("BusType", "")).strip()
                    if disk.get("BusType")
                    else "Unknown"
                )
                media = (
                    str(disk.get("MediaType", "")).strip()
                    if disk.get("MediaType")
                    else "Disk"
                )
                size_bytes = disk.get("Size")
                size_gib = (
                    round(size_bytes / (1024**3), 2)
                    if isinstance(size_bytes, (int, float))
                    else 0
                )
                drives.append(
                    {
                        "type": f"{bus} {media}".strip(),
                        "model": model,
                        "size_gib": size_gib,
                    }
                )
    except Exception:
        pass

    return drives if drives else [
        {"type": "Unknown", "model": "Unknown Drive", "size_gib": 0}
    ]
