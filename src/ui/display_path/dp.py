import platform
from pathlib import Path


def display_path(path):
    """
    Display path in a platform-appropriate format.

    Linux: /home/username/Documents
    Windows: C:\\Users\\username\\Documents

    Uses real paths, no hardcoded formats.
    """
    return str(Path(path).resolve())