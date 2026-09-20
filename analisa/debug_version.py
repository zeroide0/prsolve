import ctypes
import ctypes.wintypes
import struct
from pathlib import Path

def determine_version(target):
    if isinstance(target, (str, Path)):
        filepath = str(target)
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
            if size > 0:
                res = ctypes.create_string_buffer(size)
                if ctypes.windll.version.GetFileVersionInfoW(filepath, 0, size, res):
                    p_info = ctypes.c_void_p()
                    u_len = ctypes.wintypes.UINT()
                    if ctypes.windll.version.VerQueryValueW(res, r"\\", ctypes.byref(p_info), ctypes.byref(u_len)):
                        info_bytes = ctypes.string_at(p_info, u_len.value)
                        dw_file_version_ms, dw_file_version_ls = struct.unpack_from('<II', info_bytes, 8)
                        return (
                            (dw_file_version_ms >> 16) & 0xFFFF,
                            dw_file_version_ms & 0xFFFF,
                            (dw_file_version_ls >> 16) & 0xFFFF,
                        )
        except Exception:
            pass

        with open(filepath, "rb") as f:
            data = f.read()
    else:
        data = target

    pos = len(data)
    while True:
        idx = data.rfind(b'\xBD\x04\xEF\xFE', 0, pos)
        if idx < 0:
            break
        if idx + 16 <= len(data):
            struc_ver = struct.unpack_from('<I', data, idx + 4)[0]
            if struc_ver == 0x00010000:
                file_version_ms = struct.unpack_from('<I', data, idx + 8)[0]
                file_version_ls = struct.unpack_from('<I', data, idx + 12)[0]
                major = (file_version_ms >> 16) & 0xFFFF
                if major in (26, 25, 24, 23):
                    return (
                        major,
                        file_version_ms & 0xFFFF,
                        (file_version_ls >> 16) & 0xFFFF,
                    )
        pos = idx
    raise Exception("Version not found")

p = r"D:\PR INSTALL\prsolved\analisa\sandbox\Adobe Premiere Pro.exe"
print("From Path :", determine_version(p))
with open(p, "rb") as f:
    b = f.read()
print("From Bytes:", determine_version(b))
