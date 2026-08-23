from python.src.cmd.init import *

def cmd_find(args):

    global path

    if len(args) < 2:
        return

    keyword = args[1]

    found = False

    for root, dirs, files in os.walk(path):

        for name in dirs + files:

            if keyword.lower() in name.lower():

                print(Path(root) / name)

                found = True

    if not found:
        print("Nothing found.")
