import os
from pathlib import Path

ini_path = r"D:\PR INSTALL\prsolved\analisa\config_v421.ini"
with open(ini_path, "r") as f:
    lines = f.readlines()

in_targets = False
targets = []
for l in lines:
    l = l.strip()
    if l == "[TargetFiles]":
        in_targets = True
        continue
    elif l.startswith("["):
        in_targets = False
    if in_targets and "=" in l:
        val = l.split("=", 1)[1]
        val = val.replace('"', '').strip()
        targets.append(val)

pr_root = Path(r"D:\PR INSTALL\prsolved\pr")
print(f"Total targets defined in config: {len(targets)}")
found = []
for t in targets:
    fname = t.split("|")[0].strip()
    matches = list(pr_root.glob(f"**/{fname}"))
    if matches:
        found.append((t, matches))

print(f"Found {len(found)} target matches in pr:")
for t, matches in found:
    for m in matches:
        rel = m.relative_to(pr_root)
        print(f"  {t:30s} -> {rel}")
