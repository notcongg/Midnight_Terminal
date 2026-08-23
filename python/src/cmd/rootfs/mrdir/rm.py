from python.src.cmd.init import *

def cmd_rm(args):
    global path

    if len(args) < 2:
        return

    force = False
    targets = []

    for a in args[1:]:
        if a == "-rf":
            force = True
        else:
            targets.append(a)

    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = path / p

        if not p.exists():
            print(f"Not found: {p}")
            continue

        if not force:
            ans = input(f"Delete {p}? (y/n): ")
            if ans.lower() != "y":
                continue

        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            print(f"Removed: {p}")
        except Exception as e:
            print("Failed:", e)
