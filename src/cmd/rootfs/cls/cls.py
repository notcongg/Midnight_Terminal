import subprocess, os

def cmd_cls(args):
    subprocess.run(
        ["cls"] if os.name == "nt" else ["clear"],
        shell=True
    )

def cmd_clear(args):
    subprocess.run(
        ["cls"] if os.name == "nt" else ["clear"],
        shell=True
    )
