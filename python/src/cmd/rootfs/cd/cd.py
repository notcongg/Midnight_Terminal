from python.src.cmd.init import *

def cmd_cd(args):
    global path

    if len(args) < 2:
        print(path)
        return

    new_path = Path(args[1])

    if not new_path.is_absolute():
        new_path = path / new_path

    if new_path.exists() and new_path.is_dir():
        path = new_path.resolve()
    else:
        print("The system cannot find the path specified.")
