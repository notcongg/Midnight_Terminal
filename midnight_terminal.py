#!/usr/bin/env python3

"""Midnight Terminal - (c) Congg 2026. License GNU GPL v3.0"""

from __future__ import annotations
import os
import platform
from src.app import run


if __name__ == "__main__":
    if platform.system() == "Windows":
        os.system("title Midnight Terminal")
    run()
