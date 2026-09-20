from pathlib import Path
import re

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

print("Analyzing vicinity of PipelineRouting patches...")
# Look for FF 25 (jmp [rip+disp32]) or B8 00 00 00 00 C3 in range 0x22800000 - 0x22A00000
start = 0x22800000
end = 0x22A00000

# Search for 24 38 48 83 C4 20 5F C3 anywhere in the binary and see if any is near this range
sub = bytes.fromhex("24384883c4205fc3")
pos = 0
matches = []
while True:
    idx = pr_data.find(sub, pos)
    if idx == -1:
        break
    matches.append(idx)
    pos = idx + 1

print(f"Total '24 38 48 83 c4 20 5f c3' matches: {len(matches)}")
near = [m for m in matches if abs(m - 0x228DCDFA) < 0x2000000]
print(f"Matches near PipelineRouting (within 32MB): {len(near)} {[hex(x) for x in near]}")

# Also check for any 'FF 25' immediately preceded by 'C3' near these functions
for m in matches:
    # check if following byte (or after CC padding) is FF 25
    after = pr_data[m+8:m+24]
    # strip CC
    stripped = after.lstrip(b'\xCC')
    if stripped.startswith(b'\xFF\x25'):
        print(f"FOUND candidate at {hex(m)}: full bytes = {pr_data[m:m+20].hex()}")
