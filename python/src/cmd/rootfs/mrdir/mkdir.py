def cmd_mkdir(args):
    global path
    if len(args) < 2:
        return

    name = args[1]
    target = path / name

    if "." in name:  # file
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("")
    else:
        target.mkdir(parents=True, exist_ok=True)