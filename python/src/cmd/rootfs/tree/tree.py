from python.src.cmd.init import *
from python.src.cmd.rootfs.ls.ls import human_size

def cmd_tree(args):
    global path

    show_all = False
    only_dir = False
    human = False
    depth_limit = None
    target = None

    # ================= PARSE ARGS =================
    i = 1
    while i < len(args):
        a = args[i]

        if a == "-a":
            show_all = True

        elif a == "-d":
            only_dir = True

        elif a == "-h":
            human = True

        elif a == "-L":
            if i + 1 < len(args):
                try:
                    depth_limit = int(args[i + 1])
                    i += 1
                except:
                    print("Invalid depth value.")
                    return

        else:
            # path (first non-flag wins)
            if target is None:
                p = Path(a)
                if not p.is_absolute():
                    p = path / p
                target = p

        i += 1

    # ================= DEFAULT PATH =================
    if target is None:
        target = path

    # ================= NORMALIZE PATH (CRITICAL FIX) =================
    try:
        target = Path(target).expanduser().resolve()
    except Exception:
        print("Path not found.")
        return

    if not target.exists():
        print("Path not found.")
        return

    print(target)

    # ================= SIZE FORMAT =================
    def size_fmt(p):
        try:
            if p.is_dir():
                return ""
            s = p.stat().st_size
            return f"{s} B" if not human else human_size(s)
        except:
            return ""

    # ================= FILTER =================
    def allowed(p):
        if not show_all and p.name.startswith("."):
            return False
        if only_dir and not p.is_dir():
            return False
        return True

    # ================= TREE WALK =================
    def walk(folder, prefix="", depth=0):
        if depth_limit is not None and depth > depth_limit:
            return

        try:
            items = list(filter(allowed, folder.iterdir()))
        except PermissionError:
            print(prefix + "└── [Access Denied]")
            return
        except Exception:
            return

        for idx, item in enumerate(items):
            last = idx == len(items) - 1
            connector = "└── " if last else "├── "

            name = item.name + ("/" if item.is_dir() else "")
            print(prefix + connector + name +
                  (f" {size_fmt(item)}" if not item.is_dir() else ""))

            if item.is_dir():
                extension = "    " if last else "│   "
                walk(item, prefix + extension, depth + 1)

    walk(target)

    # ================= SIZE FORMAT =================
    def size_fmt(p):
        if p.is_dir():
            return ""
        s = p.stat().st_size
        if not human:
            return f"{s} B"
        return human_size(s)

    # ================= FILTER =================
    def allowed(p):
        if not show_all and p.name.startswith("."):
            return False
        if only_dir and not p.is_dir():
            return False
        return True

    # ================= TREE WALK =================
    def walk(folder, prefix="", depth=0):
        if depth_limit is not None and depth >= depth_limit:
            return

        try:
            items = list(filter(allowed, folder.iterdir()))
        except PermissionError:
            print(prefix + "└── [Access Denied]")
            return

        for idx, item in enumerate(items):
            last = idx == len(items) - 1
            connector = "└── " if last else "├── "

            name = item.name + ("/" if item.is_dir() else "")
            print(prefix + connector + name +
                  (f" {size_fmt(item)}" if not item.is_dir() else ""))

            if item.is_dir():
                extension = "    " if last else "│   "
                walk(item, prefix + extension, depth + 1)

    walk(target)
