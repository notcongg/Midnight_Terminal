from python.src.cmd.init import *

def cmd_crt(args):

    global path

    if len(args) < 2:
        return

    # ================= NORMAL CREATE =================
    if "->" not in args:

        name = args[1]

        target = Path(name)

        if not target.is_absolute():
            target = path / target

    # ================= CREATE TO PATH =================
    else:

        idx = args.index("->")

        name = args[1]
        dest = Path(args[idx + 1])

        if not dest.is_absolute():
            dest = path / dest

        target = dest / name

    # ================= FILE =================
    if "." in target.name:

        target.parent.mkdir(parents=True, exist_ok=True)

        if not target.exists():
            target.write_text("")

    # ================= FOLDER =================
    else:

        target.mkdir(parents=True, exist_ok=True)
