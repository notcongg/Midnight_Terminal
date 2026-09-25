import os
from pathlib import Path


def midnight_config_dir() -> Path:
    if os.name == "nt":
        # Windows: %APPDATA%\Midnight
        appdata = os.environ.get("APPDATA")

        if appdata:
            path = Path(appdata) / "Midnight"
        else:
            path = (
                Path.home()
                / "AppData"
                / "Roaming"
                / "Midnight"
            )

    else:
        # Linux / Unix: ~/.config/Midnight
        path = Path.home() / ".config" / "Midnight"

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def midconf_path() -> Path:
    path = midnight_config_dir() / ".midconf"

    if not path.exists():
        path.touch()

    return path


def midhsty_path() -> Path:
    return midnight_config_dir() / ".midhsty"