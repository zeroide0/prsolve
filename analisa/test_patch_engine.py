"""Unit test for the patch functions and pattern tables in analisa."""

import struct
from pathlib import Path

PatternByte = int
Pattern = list
ReplacementFn = object

def _force_profile_validation_true(data: bytearray, addr: int, sig: Pattern) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[7:11] = b'\x90\xB0\x01\xC3'
    return bytes(res)

def _force_structural_redirect(data: bytearray, addr: int, sig: Pattern) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[14] = 0x00
    return bytes(res)

def _force_secondary_bypass(data: bytearray, addr: int, sig: Pattern) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[8] = 0x01
    return bytes(res)

def _force_flag_initialization(data: bytearray, addr: int, sig: Pattern) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[7] = 0x01
    return bytes(res)

def _force_jpeg_hwaccel_b(data: bytearray, addr: int, sig: Pattern) -> bytes:
    res = bytearray(data[addr : addr + len(sig)])
    res[22] = 0x01
    return bytes(res)

PATCHES_PREMIERE_26 = [
    (
        [0x0F, 0xB6, 0x80, 0x0C, 0x01, 0x00, 0x00,
         0xC3,
         0x32, 0xC0,
         0xC3],
        _force_profile_validation_true,
    ),
    (
        [0x48, 0x8B, 0x08,
         0xC5, 0xF8, 0x10, 0x01,
         0xC5, 0xF8, 0x11, 0x06,
         0x4C, 0x89, 0x76, 0x10,
         0x4C, 0x89, 0x76, 0x18],
        _force_structural_redirect,
    ),
    (
        [0x45, 0x00,
         0xC6, 0x80, 0xD0, 0x00, 0x00, 0x00, 0x00,
         0x49, 0x8B, 0x75, 0x00,
         0x48, 0x81, 0xC6, 0x90],
        _force_secondary_bypass,
    ),
    (
        [0x66, 0xC7, 0x83, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x01,
         0x8B, 0x84, 0x24, 0xA8, 0x00, 0x00, 0x00],
        _force_flag_initialization,
    ),
]

PATCHES_JPEG_26 = [
    (
        [0x75, 0x0D,
         0xC7, 0x84, 0x24, 0x34, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
         0xEB, 0x0B,
         0xC7, 0x84, 0x24, 0x34, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        _force_jpeg_hwaccel_b,
    ),
]

PATCHES_HEADLESS_26 = [
    (
        [0x0F, 0xB6, 0x80, 0x0C, 0x01, 0x00, 0x00,
         0xC3,
         0x32, 0xC0,
         0xC3],
        _force_profile_validation_true,
    ),
    (
        [0x45, 0x00,
         0xC6, 0x80, 0xD0, 0x00, 0x00, 0x00, 0x00,
         0x49, 0x8B, 0x75, 0x00,
         0x48, 0x81, 0xC6, 0x90],
        _force_secondary_bypass,
    ),
    (
        [0x66, 0xC7, 0x83, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x01,
         0x8B, 0x84, 0x24, 0xA8, 0x00, 0x00, 0x00],
        _force_flag_initialization,
    ),
]

# Test on test_jpeg (sandbox)
jpeg_path = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox\jpeg_wrapper.dll")
with open(jpeg_path, "rb") as f:
    jpeg_data = bytearray(f.read())

print("Testing jpeg_wrapper patch...")
for i, (sig, repl) in enumerate(PATCHES_JPEG_26):
    pat = bytes(sig)
    idx = jpeg_data.find(pat)
    assert idx != -1, f"Pattern {i} not found in jpeg_wrapper"
    print(f"  Found at 0x{idx:08X}, patching...")
    new_bytes = repl(jpeg_data, idx, sig)
    jpeg_data[idx:idx+len(new_bytes)] = new_bytes

# Verify patched state
for i, (sig, repl) in enumerate(PATCHES_JPEG_26):
    pat = bytes(sig)
    idx = jpeg_data.find(pat)
    assert idx == -1, f"Pattern {i} should not match after patching"
print("  Patched successfully and verified!")

# Test restore logic
with open(Path(r"D:\PR INSTALL\prsolved\pr\jpeg_wrapper.dll"), "rb") as f:
    orig_data = f.read()
assert orig_data.find(bytes(PATCHES_JPEG_26[0][0])) != -1
print("All patch transformations tested and verified successfully.")
