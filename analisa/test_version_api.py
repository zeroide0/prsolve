import ctypes
from ctypes import wintypes
import os
from pathlib import Path

def get_file_version(filepath: str):
    """Retrieve file version tuple (major, minor, build, rev) using Windows Version.dll."""
    size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
    if size == 0:
        return None
    res = ctypes.create_string_buffer(size)
    if not ctypes.windll.version.GetFileVersionInfoW(filepath, 0, size, res):
        return None
    p_info = ctypes.c_void_p()
    u_len = ctypes.wintypes.UINT()
    if not ctypes.windll.version.VerQueryValueW(res, r"\\", ctypes.byref(p_info), ctypes.byref(u_len)):
        return None
    
    # VS_FIXEDFILEINFO structure
    # dwFileVersionMS is at offset 8, dwFileVersionLS at offset 12
    # dwProductVersionMS at offset 16, dwProductVersionLS at offset 20
    info_bytes = ctypes.string_at(p_info, u_len.value)
    import struct
    dw_file_version_ms, dw_file_version_ls = struct.unpack_from('<II', info_bytes, 8)
    dw_prod_version_ms, dw_prod_version_ls = struct.unpack_from('<II', info_bytes, 16)
    
    file_ver = (
        (dw_file_version_ms >> 16) & 0xFFFF,
        dw_file_version_ms & 0xFFFF,
        (dw_file_version_ls >> 16) & 0xFFFF,
        dw_file_version_ls & 0xFFFF,
    )
    prod_ver = (
        (dw_prod_version_ms >> 16) & 0xFFFF,
        dw_prod_version_ms & 0xFFFF,
        (dw_prod_version_ls >> 16) & 0xFFFF,
        dw_prod_version_ls & 0xFFFF,
    )
    return file_ver, prod_ver

ver = get_file_version(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
print("Retrieved version:", ver)
