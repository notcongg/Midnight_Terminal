from __future__ import annotations

from ..platform.wmi import get_system_wmi


def collect_gpu() -> dict:
    gpus = {"igpu": [], "dgpu": []}
    seen: set[str] = set()
    try:
        for gpu in get_system_wmi().query("Win32_VideoController"):
            name = str(gpu.Name).strip() if gpu.Name else "Unknown GPU"
            if name in seen or any(
                kw in name.lower() for kw in ["virtual", "remote", "citrix"]
            ):
                continue
            seen.add(name)

            name_lower = name.lower()
            is_igpu = False

            if "intel" in name_lower:
                is_igpu = "arc" not in name_lower
            elif "radeon" in name_lower or "amd" in name_lower:
                is_igpu = not any(
                    kw in name_lower for kw in ["rx ", "pro ", "xt ", "discrete"]
                )
            elif any(
                kw in name_lower
                for kw in ["nvidia", "geforce", "rtx", "gtx", "quadro"]
            ):
                is_igpu = False
            else:
                is_igpu = True

            if is_igpu:
                gpus["igpu"].append(name)
            else:
                gpus["dgpu"].append(name)
    except Exception:
        pass
    return gpus
