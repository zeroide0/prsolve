from pathlib import Path
import re

target = Path(r"D:\PR INSTALL\prsolved\pr\PProHeadless.exe")
with open(target, "rb") as f:
    data = f.read()

# Pattern was: 48 8B 08 C5 F8 10 01 C5 F8 11 06 4C 89 76 10 4C 89 76 18
# Let's search for C5 F8 10 01 C5 F8 11 06
sub = bytes.fromhex("C5F81001C5F81106")
pos = 0
matches = []
while True:
    idx = data.find(sub, pos)
    if idx == -1:
        break
    matches.append(idx)
    pos = idx + 1

print(f"PProHeadless.exe matches for C5 F8 10 01 C5 F8 11 06: {len(matches)}")
for m in matches:
    print(f"  At {hex(m)}: {data[m-4:m+24].hex()}")
