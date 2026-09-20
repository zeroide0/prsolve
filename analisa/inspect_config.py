import configparser
import os

ini_path = r"D:\PR INSTALL\prsolved\analisa\config_v421.ini"
with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print(f"Total lines in config_v421.ini: {len(lines)}")

# Print sections and lines mentioning premiere or patterns
sections = []
current_sec = None
premiere_lines = []
for idx, line in enumerate(lines):
    line_s = line.strip()
    if line_s.startswith("[") and line_s.endswith("]"):
        current_sec = line_s
        sections.append((idx + 1, current_sec))
    if "premiere" in line.lower():
        premiere_lines.append((idx + 1, current_sec, line_s))

print(f"Sections found ({len(sections)}):")
for line_no, sec in sections:
    print(f"  Line {line_no:4d}: {sec}")

print(f"\nLines mentioning 'premiere' ({len(premiere_lines)}):")
for line_no, sec, text in premiere_lines:
    print(f"  Line {line_no:4d} [{sec}]: {text}")
