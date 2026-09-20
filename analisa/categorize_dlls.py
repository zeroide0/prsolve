import os
from pathlib import Path

pr_dir = Path(r"D:\PR INSTALL\prsolved\pr")
dlls = [f.name for f in pr_dir.glob("*.dll")]
print(f"Total DLLs in pr: {len(dlls)}")

keywords = ["reg", "lic", "auth", "act", "amt", "ims", "caps", "dva", "vulcan", "app", "adobe", "token", "smapi"]
matched = {}
for kw in keywords:
    matched[kw] = [d for d in dlls if kw in d.lower()]

for kw, files in matched.items():
    if files:
        print(f"--- Keyword: {kw} ---")
        for f in sorted(files):
            print(f"  {f}")
