from python.src.cmd.init import *

def get_volume_serial(p):
    try:
        p = Path(p)
        drive = p.anchor if p.anchor else str(p)

        kernel32 = ctypes.windll.kernel32
        serial_number = ctypes.c_ulong()

        res = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            None,
            0,
            ctypes.byref(serial_number),
            None,
            None,
            None,
            0
        )

        if res == 0:
            return "0000-0000"

        return f"{serial_number.value & 0xFFFF:04X}-{(serial_number.value >> 16) & 0xFFFF:04X}"

    except:
        return "0000-0000"

def get_volume_label(p):
    try:
        p = Path(p)
        drive = p.anchor if p.anchor else str(p)

        kernel32 = ctypes.windll.kernel32

        volume_name = ctypes.create_unicode_buffer(261)

        res = kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            volume_name,
            ctypes.sizeof(volume_name),
            None,
            None,
            None,
            None,
            0
        )

        if res == 0:
            return ""

        return f"is {volume_name.value}"

    except:
        return "has no label"
