import os
from pathlib import Path

pr_dir = Path(r"D:\PR INSTALL\prsolved\pr")

# Search in js, html, json, xml in pr directory for strings
keywords = ["adobegenuine", "genuine", "diskon 70%", "tidak berlisensi", "unlicensed", "lcs-cpc", "prod.adobegenuine"]

found = []
for p in pr_dir.rglob("*.*"):
    if p.suffix.lower() in [".js", ".json", ".html", ".xml", ".css", ".txt", ".strings"]:
        try:
            with open(p, "rb") as f:
                content = f.read().lower()
            for kw in keywords:
                if kw.encode() in content:
                    found.append((p.relative_to(pr_dir), kw))
        except Exception:
            pass

print(f"Total occurrences found in text resources: {len(found)}")
for rel, kw in found[:20]:
    print(f"  {rel} -> {kw}")
