from pathlib import Path

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

sub = bytes.fromhex("24384883c4205fc3")
pos = 0
matches = []
while True:
    idx = pr_data.find(sub, pos)
    if idx == -1:
        break
    matches.append(idx)
    pos = idx + 1

print(f"Total matches for 24 38 48 83 c4 20 5f c3: {len(matches)}")
for idx in matches:
    following = pr_data[idx:idx+25]
    print(f"At {hex(idx)}: {following.hex()}")
