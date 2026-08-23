# ============================================================
# D:\002 - [Code]\midnight_terminal\python\src\cmd\rootfs\mv\cmd_mv.py
# ============================================================

import ctypes

from . import errors
from . import handles
from . import filesystem as fs


# ============================================================
# Error translation
# ============================================================

def win_error():
    code = errors.GetLastError()

    buffer = ctypes.wintypes.LPWSTR()

    length = errors.FormatMessageW(
        errors.FORMAT_MESSAGE_ALLOCATE_BUFFER
        | errors.FORMAT_MESSAGE_FROM_SYSTEM
        | errors.FORMAT_MESSAGE_IGNORE_INSERTS,
        None,
        code,
        errors.MAKELANGID(
            errors.LANG_NEUTRAL,
            errors.SUBLANG_DEFAULT,
        ),
        ctypes.cast(
            ctypes.byref(buffer),
            ctypes.POINTER(ctypes.wintypes.LPWSTR),
        ),
        0,
        None,
    )

    if length and buffer.value:
        message = buffer.value.strip()
        errors.LocalFree(buffer)
    else:
        message = f"Unknown error {code}"

    return code, message


class Win32Error(OSError):
    def __init__(self, code=None, message=None):
        if code is None:
            code, message = win_error()

        self.winerror = code
        super().__init__(f"[WinError {code}] {message}")


def raise_last_error():
    code, message = win_error()
    raise Win32Error(code, message)


# ============================================================
# Path helpers
# ============================================================

def exists(path):
    return (
        fs.GetFileAttributesW(path)
        != fs.INVALID_FILE_ATTRIBUTES
    )


def attributes(path):
    value = fs.GetFileAttributesW(path)

    if value == fs.INVALID_FILE_ATTRIBUTES:
        return None

    return value


def is_directory(path):
    attrs = attributes(path)

    return (
        attrs is not None
        and bool(attrs & handles.FILE_ATTRIBUTE_DIRECTORY)
    )


def is_reparse_point(path):
    attrs = attributes(path)

    return (
        attrs is not None
        and bool(attrs & handles.FILE_ATTRIBUTE_REPARSE_POINT)
    )


def full_path(path):
    size = 512

    while True:
        buffer = ctypes.create_unicode_buffer(size)
        file_part = ctypes.wintypes.LPWSTR()

        length = fs.GetFullPathNameW(
            path,
            size,
            buffer,
            ctypes.byref(file_part),
        )

        if length == 0:
            raise_last_error()

        if length < size:
            return buffer.value

        size = length + 1


def basename(path):
    path = path.rstrip("\\/")

    index = max(
        path.rfind("\\"),
        path.rfind("/"),
    )

    return path[index + 1:]


# ============================================================
# Handle-based identity
# ============================================================

def open_handle(path):
    flags = handles.FILE_FLAG_BACKUP_SEMANTICS

    if is_reparse_point(path):
        flags |= handles.FILE_FLAG_OPEN_REPARSE_POINT

    handle = handles.CreateFileW(
        path,
        0,
        handles.FILE_SHARE_READ
        | handles.FILE_SHARE_WRITE
        | handles.FILE_SHARE_DELETE,
        None,
        handles.OPEN_EXISTING,
        flags,
        None,
    )

    if handle == handles.INVALID_HANDLE_VALUE:
        raise_last_error()

    return handle


def final_path(path):
    """
    Resolve the actual filesystem path through a Windows handle.
    """

    handle = open_handle(path)

    try:
        size = 512

        while True:
            buffer = ctypes.create_unicode_buffer(size)

            length = fs.GetFinalPathNameByHandleW(
                handle,
                buffer,
                size,
                0,
            )

            if length == 0:
                raise_last_error()

            if length < size:
                return buffer.value

            size = length + 1

    finally:
        handles.CloseHandle(handle)


def file_id_info(path):
    """
    Resolve VolumeSerialNumber + FileId via FILE_ID_INFO,
    for robust cross-volume/hardlink identity checks.
    """

    handle = open_handle(path)

    try:
        info = fs.FILE_ID_INFO()

        ok = fs.GetFileInformationByHandleEx(
            handle,
            fs.FILE_INFO_BY_HANDLE_CLASS.FileIdInfo,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )

        if not ok:
            raise_last_error()

        return (
            info.VolumeSerialNumber,
            bytes(info.FileId.Identifier),
        )

    finally:
        handles.CloseHandle(handle)


# ============================================================
# Native Move
# ============================================================

def native_move(source, destination, replace=False):
    flags = (
        fs.MOVEFILE_COPY_ALLOWED
        | fs.MOVEFILE_WRITE_THROUGH
    )

    if replace:
        flags |= fs.MOVEFILE_REPLACE_EXISTING

    if not fs.MoveFileExW(
        source,
        destination,
        flags,
    ):
        raise_last_error()


# ============================================================
# Safety
# ============================================================

def is_inside(parent, child):
    parent = parent.rstrip("\\").casefold()
    child = child.rstrip("\\").casefold()

    return (
        child.startswith(parent + "\\")
    )


def same_object(source, destination):
    """
    Compare resolved filesystem identity.
    Tries FILE_ID_INFO first (volume serial + file id, robust
    across hardlinks); falls back to resolved path comparison.
    """

    try:
        return file_id_info(source) == file_id_info(destination)

    except OSError:
        pass

    try:
        source_final = final_path(source)
        destination_final = final_path(destination)

    except OSError:
        return False

    return (
        source_final.casefold()
        == destination_final.casefold()
    )


# ============================================================
# cmd_mv
# ============================================================

def cmd_mv(args):

    if not args:
        print("mv: missing operand")
        return

    force = False
    interactive = False
    verbose = False

    paths = []

    # --------------------------------------------------------
    # Parse arguments
    # --------------------------------------------------------

    for arg in args:

        if arg == "-f":
            force = True

        elif arg == "-i":
            interactive = True

        elif arg == "-v":
            verbose = True

        elif arg.startswith("-"):
            print(f"mv: unknown option '{arg}'")
            return

        else:
            paths.append(arg)

    if len(paths) != 2:
        print("mv: usage: mv [-fiv] SOURCE DEST")
        return

    source = paths[0]
    destination = paths[1]

    # --------------------------------------------------------
    # Resolve
    # --------------------------------------------------------

    try:
        source = full_path(source)
        destination = full_path(destination)

    except OSError as error:
        print(f"mv: {error}")
        return

    # --------------------------------------------------------
    # Source
    # --------------------------------------------------------

    if not exists(source):
        print(
            f"mv: cannot stat '{source}': "
            "No such file or directory"
        )
        return

    source_is_dir = is_directory(source)

    # --------------------------------------------------------
    # Destination
    # --------------------------------------------------------

    if exists(destination) and is_directory(destination):

        name = basename(source)

        if not name:
            print("mv: invalid source")
            return

        target = (
            destination.rstrip("\\")
            + "\\"
            + name
        )

    else:
        target = destination

    # --------------------------------------------------------
    # Self / recursive directory protection
    # --------------------------------------------------------

    if exists(target):

        if same_object(source, target):
            print(
                f"mv: '{source}' and "
                f"'{target}' are the same object"
            )
            return

    if source_is_dir:

        try:
            source_final = final_path(source)

        except OSError:
            source_final = source

        if exists(destination):

            try:
                destination_final = final_path(destination)

            except OSError:
                destination_final = destination

            if is_inside(
                source_final,
                destination_final,
            ):
                print(
                    f"mv: cannot move '{source}' "
                    "into a subdirectory of itself"
                )
                return

    # --------------------------------------------------------
    # Existing target
    # --------------------------------------------------------

    if exists(target):

        if interactive and not force:

            answer = input(
                f"mv: overwrite '{target}'? [y/N] "
            )

            if answer.strip().lower() not in {
                "y",
                "yes",
            }:
                return

        elif not force:

            print(
                f"mv: cannot move '{source}' "
                f"to '{target}': File exists"
            )
            return

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    try:

        native_move(
            source,
            target,
            replace=force,
        )

    except OSError as error:

        print(
            f"mv: cannot move '{source}' "
            f"to '{target}': {error}"
        )
        return

    # --------------------------------------------------------
    # Verbose
    # --------------------------------------------------------

    if verbose:
        print(
            f"'{source}' -> '{target}'"
        )
