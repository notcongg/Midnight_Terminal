from src.cmd.init import *

def cmd_which(args):

    if len(args) < 2:
        return

    target = args[1]

    # PATH ENV
    for p in os.environ.get("PATH", "").split(os.pathsep):

        full = Path(p) / target

        # windows exe
        if os.name == "nt":

            exts = ["", ".exe", ".bat", ".cmd"]

            for ext in exts:

                fp = Path(str(full) + ext)

                if fp.exists():
                    print(fp)
                    return

        else:

            if full.exists():
                print(full)
                return

    print("Not found.")