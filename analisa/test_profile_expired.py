from pathlib import Path
import re

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

# ProfileExpired2="85C075??B892010000E9"|"85C07500B800000000E9"
rx = re.compile(b'\x85\xC0\x75.\xB8\x92\x01\x00\x00\xE9', re.DOTALL)
matches = [m.start() for m in rx.finditer(pr_data)]
print("ProfileExpired2 matches:", len(matches), [hex(x) for x in matches])
for m in matches:
    print(f"  At {hex(m)}: {pr_data[m:m+16].hex()}")

# Also check other ProfileExpired patterns:
# 85 C0 75 ?? ?? ?? ?? ?? B8 92 01 00 00 E9
rx_gen = re.compile(b'\xB8\x92\x01\x00\x00\xE9', re.DOTALL)
m_gen = [m.start() for m in rx_gen.finditer(pr_data)]
print("\nB8 92 01 00 00 E9 matches:", len(m_gen), [hex(x) for x in m_gen])
for m in m_gen:
    ctx = pr_data[max(0, m-8):m+12]
    print(f"  At {hex(m)}: {ctx.hex()}")
