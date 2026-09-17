
from pathlib import Path
import os


def get_midnight_config_dir() -> Path:
    if os.name == "nt":
        appdata = os.getenv("APPDATA")

        if appdata:
            return Path(appdata) / "Midnight"

        userprofile = os.getenv("USERPROFILE")

        if userprofile:
            return (
                Path(userprofile)
                / "AppData"
                / "Roaming"
                / "Midnight"
            )

        raise RuntimeError(
            "Midnight: unable to determine config directory"
        )

    home = os.getenv("HOME")

    if not home:
        raise RuntimeError(
            "Midnight: HOME is not set"
        )

    return Path(home) / ".config" / "midnight"


MIDNIGHT_CONFIG_DIR = get_midnight_config_dir()

MIDCONF_PATH = MIDNIGHT_CONFIG_DIR / ".midconf"
MIDHSTY_PATH = MIDNIGHT_CONFIG_DIR / ".midhsty"
MIDALIAS_PATH = MIDNIGHT_CONFIG_DIR / ".midalias"