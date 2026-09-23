"""Unit test for codec validator pattern matching and patching."""

import os
from pathlib import Path

# The pattern for codec validator functions:
# 40 53 55 56 57 48 83 EC 48 8B D9 48 8D 2D
# push rbx; push rbp; push rsi; push rdi; sub rsp, 48h; mov ebx, ecx; lea rbp, [rip + disp32]
PATTERN_CODEC_VALIDATION = [
    0x40, 0x53, 0x55, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x48, 0x8B, 0xD9, 0x48, 0x8D, 0x2D,
]

def _force_codec_validation_true(data: bytearray, addr: int, sig) -> bytes:
    """Override codec validator functions to return 1 (licensed/enabled).
    
    Replaces function entry point with `B0 01 C3` (mov al, 1; ret).
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[0:3] = b'\xB0\x01\xC3'
    return bytes(res)

pr_path = Path(r"D:\PR INSTALL\fix\pr\Adobe Premiere Pro.exe")
hl_path = Path(r"D:\PR INSTALL\fix\pr\PProHeadless.exe")

with open(pr_path, "rb") as f:
    pr_data = bytearray(f.read())

with open(hl_path, "rb") as f:
    hl_data = bytearray(f.read())

import re
def find_all(data, pattern):
    key = tuple(pattern)
    parts = [b'.' if b is None else re.escape(bytes([b])) for b in pattern]
    rx = re.compile(b''.join(parts), re.DOTALL)
    return [m.start() for m in rx.finditer(data)]

# Test PR
occs_pr = find_all(pr_data, PATTERN_CODEC_VALIDATION)
print(f"Premiere matches: {len(occs_pr)} -> {[hex(o) for o in occs_pr]}")
assert len(occs_pr) == 2, f"Expected 2 matches in PR, got {len(occs_pr)}"

for addr in occs_pr:
    repl = _force_codec_validation_true(pr_data, addr, PATTERN_CODEC_VALIDATION)
    assert repl[:3] == b'\xB0\x01\xC3'
    pr_data[addr:addr+len(repl)] = repl

# Verify no more matches of unpatched pattern
assert len(find_all(pr_data, PATTERN_CODEC_VALIDATION)) == 0
print("PR codec patching test PASSED.")

# Test Headless
occs_hl = find_all(hl_data, PATTERN_CODEC_VALIDATION)
print(f"Headless matches: {len(occs_hl)} -> {[hex(o) for o in occs_hl]}")
assert len(occs_hl) == 2, f"Expected 2 matches in Headless, got {len(occs_hl)}"

for addr in occs_hl:
    repl = _force_codec_validation_true(hl_data, addr, PATTERN_CODEC_VALIDATION)
    assert repl[:3] == b'\xB0\x01\xC3'
    hl_data[addr:addr+len(repl)] = repl

assert len(find_all(hl_data, PATTERN_CODEC_VALIDATION)) == 0
print("Headless codec patching test PASSED.")

print("\nALL CODEC PATCH TESTS SUCCESSFUL!")
