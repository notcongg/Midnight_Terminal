import getpass
import socket
import os
import time
import ctypes
import shutil
import msvcrt
import sys
import subprocess

from pathlib import Path
from datetime import datetime

username = getpass.getuser()
hostname = socket.gethostname()
path = Path.home()
