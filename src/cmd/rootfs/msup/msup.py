import ctypes
import platform
from pathlib import Path


# ============================================================
# NATIVE LIBRARY
# ============================================================

def _load_msup():
    system = platform.system()

    if system == "Linux":
        library_name = "libmidnight_msup.so"
        platform_name = "linux"

    elif system == "Windows":
        library_name = "midnight_msup.dll"
        platform_name = "windows"

    else:
        raise RuntimeError(
            f"Unsupported platform: {system}"
        )

    library_path = (
        Path(__file__).resolve().parent
        / "platform"
        / platform_name
        / library_name
    )

    if not library_path.exists():
        raise FileNotFoundError(
            f"MSUP native library not found: {library_path}"
        )

    return ctypes.CDLL(str(library_path))


_msup = _load_msup()


# ============================================================
# NATIVE API
# ============================================================

_msup.midnight_msup_execute.argtypes = [
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_char_p),
]

_msup.midnight_msup_execute.restype = ctypes.c_int


_msup.midnight_msup_is_active.argtypes = []

_msup.midnight_msup_is_active.restype = ctypes.c_int


_msup.midnight_msup_deactivate.argtypes = []

_msup.midnight_msup_deactivate.restype = ctypes.c_int


# ============================================================
# COMMAND
# ============================================================

def cmd_msup(*args):
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])

    argv = ["msup", *args]
    argc = len(argv)

    argv_c = (ctypes.c_char_p * (argc + 1))()

    for index, arg in enumerate(argv):
        argv_c[index] = str(arg).encode()

    argv_c[argc] = None

    _msup.midnight_msup_execute(
        argc,
        argv_c,
    )

    # Native MSUP writes directly to stdout/stderr.
    # Midnight command executor expects a string return value.
    return ""


# ============================================================
# STATE
# ============================================================

def is_active():
    return bool(
        _msup.midnight_msup_is_active()
    )


# ============================================================
# MAN PAGE
# ============================================================

def man_msup():
    return r"""
MSUP(1)                     Midnight Terminal                     MSUP(1)

NAME
    msup - Midnight SUPERUserPermissions

SYNOPSIS
    msup -s
    msup -cpswd
    msup -a
    msup -e
    msup -status
    msup -h
    msup -v

DESCRIPTION
    msup manages the Midnight Terminal superuser state.

    MSUP is an application-level privilege system for Midnight Terminal.
    It does not grant operating-system root or administrator privileges.

OPTIONS
    -s
        Set up the initial Midnight superuser password.

    -cpswd
        Change the current Midnight superuser password.

    -a
        Activate Midnight superuser mode.

        Authentication is required before activation.

    -e
        Deactivate Midnight superuser mode.

    -status
        Show the current Midnight superuser state.

    -h
        Display MSUP usage and available options.

    -v
        Display the MSUP version.

STATE
    When MSUP is active, Midnight Terminal changes its prompt to indicate
    superuser mode.

    Example:

        ╭─[congg@archlinux]-[/home/congg]-[MSUP]
        ╰─#>

    When MSUP is inactive:

        ╭─[congg@archlinux]-[/home/congg]
        ╰─$>

PASSWORD
    The MSUP password is stored as a password hash.

    Passwords are never stored in plaintext.

FILES
    Linux
        ~/.config/midnight/.midps

    Windows
        %APPDATA%\Midnight\.midps

SECURITY
    MSUP state is process-scoped.

    Activating MSUP does not make the operating-system user root or
    administrator. MSUP only controls Midnight Terminal's own privilege
    state.

EXAMPLES
    Set up the initial password:

        msup -s

    Activate MSUP:

        msup -a

    Check the current state:

        msup -status

    Deactivate MSUP:

        msup -e

    Change the password:

        msup -cpswd

SEE ALSO
    midnight(1)

AUTHOR
    Congg

COPYRIGHT
    Copyright (C) 2026 Congg
"""