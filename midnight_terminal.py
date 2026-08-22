#!/usr/bin/env python3
"""--Midnight Terminal - (c) Congg 2026. All right reversed."""
"""--[Imports]--"""
"""--[1 - INIT]"""
from src.cmd.init import *
"""--[2 - CMDS]"""
from src.cmd.rootfs.alias import expand_alias, load_aliases
from src.cmd.utils.registry import load_commands, COMMANDS
"""--[3 - UTILS]"""
from src.cmd.utils.hw_info.hardware_infomation import get_system_info as sysinfo
"""--[4 - UI]"""
from src.ui.ui import ui
from src.ui.display_path.dp import display_path

load_commands()
load_aliases()

def main():
    ui()
    while True:
        midnight_path = display_path(path)
        cmd = input(f"{username}@{hostname}[{midnight_path}]$ ")

        if not cmd.strip(): continue
        cmd = expand_alias(cmd)
        inp = cmd.strip().split()
        command = COMMANDS.get(inp[0])

        if command is None:
            print(f"""
'{inp[0]}' is not recognized as an internal or external command,
operable program or dream (dr) file.
""")
            continue
        command(inp)

if __name__ == "__main__":
    main()
