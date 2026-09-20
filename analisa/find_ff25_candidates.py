from pathlib import Path

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

sub = bytes.fromhex("24384883c4205fc3")
pos = 0
found = []
while True:
    idx = pr_data.find(sub, pos)
    if idx == -1:
        break
    # check if following byte (or after CC padding) is FF 25
    after = pr_data[idx+8:idx+32]
    stripped = after.lstrip(b'\xCC')
    if stripped.startswith(b'\xFF\x25'):
        found.append((idx, pr_data[idx:idx+len(sub) + (len(after) - len(stripped)) + 6]))
    pos = idx + 1

print(f"Candidates where '24 38 48 83 c4 20 5f c3' is followed by FF 25: {len(found)}")
for idx, b in found:
    print(f"  At {hex(idx)}: {b.hex()}")
