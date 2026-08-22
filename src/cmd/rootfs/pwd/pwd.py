from pathlib import Path
from src.ui.display_path.dp import display_path

path = Path.home()

def cmd_pwd(args):
    print(display_path(path))