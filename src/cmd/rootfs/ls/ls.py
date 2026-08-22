from src.cmd.init import *
from src.ui.display_path.dp import display_path
from src.cmd.rootfs.ls.get_vol_info import get_volume_label, get_volume_serial

def human_size(size):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def cmd_ls(args):
    global path

    show_all = False
    human = False
    target = path

    for arg in args[1:]:
        if arg.startswith("-"):
            if "a" in arg:
                show_all = True
            if "h" in arg:
                human = True
        else:
            target = Path(arg)
            if not target.is_absolute():
                target = path / target

    if not target.exists():
        print("Path not found.")
        return

    serial = get_volume_serial(target)

    print(f" Volume in drive {target.drive} {get_volume_label(target)}.")
    print(f" Volume Serial Number is {serial}\n")
    print(f" Directory of {display_path(target)}\n")

    print(f"{'Time':<22}|| {'Name':<28}|| {'Size':>12}")
    print("-" * 66)

    try:
        for f in target.iterdir():
            if not show_all and f.name.startswith("."):
                continue

            stat = f.stat()
            time = datetime.fromtimestamp(stat.st_mtime)
            time_str = time.strftime("%d/%m/%Y %H:%M")

            name = f.name
            if len(name) > 28:
                name = name[:25] + "..."

            if f.is_dir():
                size = "<DIR>"
            else:
                size_bytes = stat.st_size
                size = human_size(size_bytes) if human else f"{size_bytes} B"

            print(f"{time_str:<22}|| {name:<28}|| {size:>12}")

    except PermissionError:
        print("Access denied.")

