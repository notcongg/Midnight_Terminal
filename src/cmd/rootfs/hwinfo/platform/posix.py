from pathlib import Path


def read_file(path: str, default: str = "Unknown") -> str:
    try:
        return Path(path).read_text().strip()
    except (OSError, PermissionError):
        return default


def exists(path: str) -> bool:
    return Path(path).exists()


def list_dir(path: str) -> list[str]:
    try:
        return [p.name for p in Path(path).iterdir()]
    except (OSError, PermissionError):
        return []


def proc(path: str, default: str = "Unknown") -> str:
    return read_file(f"/proc/{path}", default)


def sys(path: str, default: str = "Unknown") -> str:
    return read_file(f"/sys/{path}", default)


def etc(path: str, default: str = "Unknown") -> str:
    return read_file(f"/etc/{path}", default)


def proc_exists(path: str) -> bool:
    return exists(f"/proc/{path}")


def sys_exists(path: str) -> bool:
    return exists(f"/sys/{path}")


def etc_exists(path: str) -> bool:
    return exists(f"/etc/{path}")