import subprocess
import os
from python.src.ui.banner import print_banner

def clear():
    subprocess.run(
        ["cls"] if os.name == "nt" else ["clear"],
        shell=True
    )

def ui():clear(); print_banner()
