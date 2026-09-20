import time
from pathlib import Path
import re

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
with open(target_pr, "rb") as f:
    pr_data = f.read()

# Let's test flexible patterns for ProfileStage_ValidationOverride_PR
# Core signature: 08 0F B6 80 0C 01 00 00 C3 32 C0 C3 48 8B 05 ?? ?? ?? ??
# Or: 08 0F B6 80 ?? 01 00 00 C3 32 C0 C3
# Or even just: 0F B6 80 0C 01 00 00 C3 32 C0 C3

rx1 = re.compile(b'\x08\x0F\xB6\x80\x0C\x01\x00\x00\xC3\x32\xC0\xC3\x48\x8B\x05....', re.DOTALL)
m1 = [m.start() for m in rx1.finditer(pr_data)]
print("ProfileStage_ValidationOverride with wildcard disp32 matches:", len(m1), [hex(x) for x in m1])

# If not, let's search for 0F B6 80 ?? ?? 00 00 C3 32 C0 C3
rx1_sub = re.compile(b'\x0F\xB6\x80..\x00\x00\xC3\x32\xC0\xC3', re.DOTALL)
m1_sub = [m.start() for m in rx1_sub.finditer(pr_data)]
print("ProfileStage_ValidationOverride subpattern matches:", len(m1_sub), [hex(x) for x in m1_sub])
for addr in m1_sub:
    surrounding = pr_data[addr-4:addr+25]
    print(f"  At {hex(addr)}: {surrounding.hex()}")

# Now let's test PipelineRouting_QueueHandler_PR
# 24 38 48 83 C4 20 5F C3 FF 25 ?? ?? ?? ??
rx2 = re.compile(b'\x24\x38\x48\x83\xC4\x20\x5F\xC3\xFF\x25....', re.DOTALL)
m2 = [m.start() for m in rx2.finditer(pr_data)]
print("\nPipelineRouting_QueueHandler with wildcard disp32 matches:", len(m2), [hex(x) for x in m2])
for addr in m2:
    surrounding = pr_data[addr:addr+18]
    print(f"  At {hex(addr)}: {surrounding.hex()}")

# If not, let's search for 48 83 C4 20 5F C3 FF 25
rx2_sub = re.compile(b'\x48\x83\xC4\x20\x5F\xC3\xFF\x25....', re.DOTALL)
m2_sub = [m.start() for m in rx2_sub.finditer(pr_data)]
print("PipelineRouting_QueueHandler subpattern matches:", len(m2_sub), [hex(x) for x in m2_sub])
for addr in m2_sub:
    surrounding = pr_data[max(0, addr-4):addr+20]
    print(f"  At {hex(addr)}: {surrounding.hex()}")

# Let's also check jpeg_wrapper.dll for Disable_LegacyTelemetryLoop_A and Enable_ExtendedHardwareAcceleration_A
target_jpeg = Path(r"D:\PR INSTALL\prsolved\pr\jpeg_wrapper.dll")
with open(target_jpeg, "rb") as f:
    jpeg_data = f.read()

# Disable_LegacyTelemetryLoop: FF 25 .. .. .. 00 repeated or ending in FF 25 .. .. .. 00
# Let's search for 48 8B 84 24 20 02 00 00 C6 80 .. 05 00 00 00
rx_acc = re.compile(b'\x48\x8B\x84\x24\x20\x02\x00\x00\xC6\x80..\x05\x00\x00\x00', re.DOTALL)
m_acc = [m.start() for m in rx_acc.finditer(jpeg_data)]
print("\njpeg Enable_ExtendedHardwareAcceleration_A flexible matches:", len(m_acc), [hex(x) for x in m_acc])
for addr in m_acc:
    print(f"  At {hex(addr)}: {jpeg_data[addr:addr+15].hex()}")

# Let's search for Disable_LegacyTelemetryLoop_B in jpeg_wrapper
from analisa.test_exact_matches import JPEG_PATTERNS
m_tele_b = [jpeg_data.find(JPEG_PATTERNS["Disable_LegacyTelemetryLoop_B"][0])]
print("jpeg Disable_LegacyTelemetryLoop_B exact matches:", [hex(x) for x in m_tele_b if x != -1])
