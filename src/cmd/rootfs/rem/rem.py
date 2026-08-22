from src.cmd.init import *

def cmd_rem(args):

    global path

    if len(args) < 3:
        print("rem <old> <new>")
        return

    old = Path(args[1])
    new = Path(args[2])

    if not old.is_absolute():
        old = path / old

    if not new.is_absolute():
        new = path / new

    if not old.exists():
        print("Target not found.")
        return

    try:

        old.rename(new)

        print(f"Renamed -> {new}")

    except Exception as e:

        print("Rename failed:", e)