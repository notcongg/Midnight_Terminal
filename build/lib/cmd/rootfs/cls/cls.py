import os
import platform
import subprocess


def cmd_cls(args):
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)


def cmd_clear(args):
    if platform.system() == "Windows":
        subprocess.run(["cls"], shell=True, check=False)
    else:
        subprocess.run(["clear"], check=False)
