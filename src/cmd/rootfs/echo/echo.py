from pathlib import Path

def cmd_echo(args):
    global path
    if len(args) < 2:
        return

    content = " ".join(args[1:])

    target = Path(content)

    # echo file path
    if target.exists() and target.is_file():
        print(target.read_text(errors="ignore"))
    else:
        print(content)