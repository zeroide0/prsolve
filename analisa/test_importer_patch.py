"""Sandboxed test script to verify new importer patches and tier2 codec logic."""

import shutil
from pathlib import Path

# Load patch definitions from prototype
import sys
sys.path.insert(0, r"D:\PR INSTALL\prsolved\fix")
from pr_patch import (
    find_all,
    _force_profile_validation_true,
    _force_structural_redirect,
    _force_secondary_bypass,
    _force_flag_initialization,
    _force_codec_validation_true,
)

def _force_importer_stream_validation(data: bytearray, addr: int, sig) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[7] = 0xEB
    return bytes(res)

def _force_importer_stream_fallback(data: bytearray, addr: int, sig) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[8] = 0xEB
    return bytes(res)

PATCHES_PREMIERE_TEST = [
    (
        [0x0F, 0xB6, 0x80, 0x0C, 0x01, 0x00, 0x00, 0xC3, 0x32, 0xC0, 0xC3],
        _force_profile_validation_true,
        1,
    ),
    (
        [0x48, 0x8B, 0x08, 0xC5, 0xF8, 0x10, 0x01, 0xC5, 0xF8, 0x11, 0x06, 0x4C, 0x89, 0x76, 0x10, 0x4C, 0x89, 0x76, 0x18],
        _force_structural_redirect,
        1,
    ),
    (
        [0x45, 0x00, 0xC6, 0x80, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x49, 0x8B, 0x75, 0x00, 0x48, 0x81, 0xC6, 0x90],
        _force_secondary_bypass,
        1,
    ),
    (
        [0x66, 0xC7, 0x83, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x01, 0x8B, 0x84, 0x24, 0xA8, 0x00, 0x00, 0x00],
        _force_flag_initialization,
        1,
    ),
    (
        [0x40, 0x53, 0x55, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x48, 0x8B, 0xD9, 0x48, 0x8D, 0x2D],
        _force_codec_validation_true,
        2,
    ),
    (
        [0x83, 0xB8, 0xA4, 0x01, 0x00, 0x00, 0x00, 0x75, 0x0D, 0xC7, 0x44, 0x24, 0x74, 0x66, 0x00, 0x07, 0xA0],
        _force_importer_stream_validation,
        1,
    ),
    (
        [0x41, 0x83, 0xF8, 0x01, 0x7E, 0x11, 0x84, 0xC0, 0x75, 0x0D, 0xC7, 0x44, 0x24, 0x74, 0x66, 0x00, 0x07, 0xA0],
        _force_importer_stream_fallback,
        1,
    ),
]

bak_file = r"D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak"
print(f"Testing against {bak_file}...")
with open(bak_file, "rb") as f:
    data = bytearray(f.read())

for i, (sig, repl, exp) in enumerate(PATCHES_PREMIERE_TEST):
    matches = find_all(data, sig)
    print(f"Patch {i}: found {len(matches)} match(es), expected {exp}")
    assert len(matches) == exp, f"Patch {i} mismatch! Found {len(matches)}, expected {exp}"
    for m in matches:
        new_bytes = repl(data, m, sig)
        data[m:m+len(new_bytes)] = new_bytes
        print(f"  Applied at 0x{m:08X}")

print("All Premiere Pro patches matched and applied successfully in sandbox!")
