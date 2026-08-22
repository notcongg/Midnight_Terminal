from src.cmd.init import *
def cmd_cat(args):

    global path

    if len(args) < 2:
        return

    target = Path(args[1])

    if not target.is_absolute():
        target = path / target

    if target.exists() and target.is_file():

        try:
            print(target.read_text(errors="ignore"))

        except Exception as e:
            print("Cannot read file:", e)

    else:
        print("File not found.")