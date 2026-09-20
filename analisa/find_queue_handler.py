from pathlib import Path
import re

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

# Let's search for parts of PipelineRouting_QueueHandler_PR:
# "24 38 48 83 C4 20 5F C3 FF 25 02 83 29 05"
for sub in [
    b'\xFF\x25\x02\x83\x29\x05',
    b'\x83\xC4\x20\x5F\xC3\xFF\x25',
    b'\x48\x83\xC4\x20\x5F\xC3',
    b'\x24\x38\x48\x83\xC4\x20\x5F\xC3',
]:
    pos = 0
    matches = []
    while len(matches) < 5:
        idx = pr_data.find(sub, pos)
        if idx == -1:
            break
        matches.append(idx)
        pos = idx + 1
    print(f"Pattern {sub.hex()} -> matches: {len(matches)} {[hex(x) for x in matches]}")
