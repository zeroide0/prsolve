import os
import sys
import struct
from pathlib import Path

def determine_pe_version(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    idx = data.find(b'\xBD\x04\xEF\xFE')
    if idx < 0:
        return None
    file_version_ms = struct.unpack_from('<I', data, idx + 8)[0]
    file_version_ls = struct.unpack_from('<I', data, idx + 12)[0]
    return (
        (file_version_ms >> 16) & 0xFFFF,
        file_version_ms & 0xFFFF,
        (file_version_ls >> 16) & 0xFFFF,
        file_version_ls & 0xFFFF
    )

pr_dir = Path(r"D:\PR INSTALL\prsolved\pr")
print(f"Scanning {pr_dir} for binaries...")
for exe in sorted(pr_dir.glob("*.exe")):
    try:
        ver = determine_pe_version(exe)
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"EXE: {exe.name:30s} | Size: {size_mb:8.2f} MB | Version: {ver}")
    except Exception as e:
        print(f"EXE: {exe.name:30s} | Error: {e}")

for dll in sorted(pr_dir.glob("*.dll")):
    # Check interesting DLLs (registration, licensing, activation, adobe, etc.)
    name_lower = dll.name.lower()
    if any(k in name_lower for k in ["reg", "lic", "amt", "ims", "auth", "adobe", "vulcan"]):
        try:
            ver = determine_pe_version(dll)
            size_mb = dll.stat().st_size / (1024 * 1024)
            print(f"DLL: {dll.name:30s} | Size: {size_mb:8.2f} MB | Version: {ver}")
        except Exception as e:
            print(f"DLL: {dll.name:30s} | Error: {e}")
