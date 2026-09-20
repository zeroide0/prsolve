import os
import time
from pathlib import Path

# The exact PR patterns from config_v421.ini
PR_PATTERNS = {
    "ProfileStage_ValidationOverride_PR": (
        bytes.fromhex("080FB6800C010000C332C0C3488B05A942760D"),
        bytes.fromhex("080FB6800C01000090B001C3488B05A942760D"),
        "Override profile validation: changes `C3 32 C0 C3` to `90 B0 01 C3` (nop; mov al, 1; ret)"
    ),
    "PipelineRouting_QueueHandler_PR": (
        bytes.fromhex("24384883C4205FC3FF2502832905"),
        bytes.fromhex("24384883C4205FC3B800000000C3"),
        "Queue handler bypass: replaces jump table stub with `B8 00 00 00 00 C3` (mov eax, 0; ret)"
    ),
    "PipelineRouting_StructuralRedirect_PR": (
        bytes.fromhex("488B08C5F81001C5F811064C8976104C897618"),
        bytes.fromhex("488B08C5F81001C5F811064C8976004C897618"),
        "Structural redirect: changes offset 10h to 00h"
    ),
    "PipelineRouting_FlagInitialization_PR": (
        bytes.fromhex("66C783D000000000018B8424A8000000"),
        bytes.fromhex("66C783D000000001018B8424A8000000"),
        "Flag initialization: changes flag word from 0100h to 0101h"
    ),
    "PipelineRouting_SecondaryBypass_PR": (
        bytes.fromhex("4500C680D000000000498B75004881C690"),
        bytes.fromhex("4500C680D000000001498B75004881C690"),
        "Secondary bypass: changes byte [rax+0D0h] from 0 to 1"
    ),
}

# Also test jpeg_wrapper.dll patterns
JPEG_PATTERNS = {
    "Disable_LegacyTelemetryLoop_A": (
        bytes.fromhex("FF25EC8FA700FF25D68FA700FF25C88FA700FF25828CA700FF255C94A700FF254E94A700FF254094A700FF253294A700FF256494A700"),
        bytes.fromhex("FF25EC8FA700FF25D68FA700FF25C88FA700FF25828CA700FF255C94A700FF254E94A700FF254094A700FF253294A700B800000000C3"),
        "Disable legacy telemetry loop A in jpeg_wrapper.dll"
    ),
    "Enable_ExtendedHardwareAcceleration_A": (
        bytes.fromhex("488B842420020000C6805C05000000"),
        bytes.fromhex("488B842420020000C6805C05000001"),
        "Enable hardware acceleration flag A in jpeg_wrapper.dll"
    ),
    "Enable_ExtendedHardwareAcceleration_B": (
        bytes.fromhex("750DC784243401000001000000EB0BC784243401000000000000"),
        bytes.fromhex("750DC784243401000001000000EB0BC784243401000001000000"),
        "Enable hardware acceleration flag B in jpeg_wrapper.dll"
    ),
}

def find_all_exact(data, pat):
    matches = []
    idx = data.find(pat)
    while idx != -1:
        matches.append(idx)
        idx = data.find(pat, idx + 1)
    return matches

target_pr = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
print(f"Loading {target_pr.name}...")
t0 = time.time()
with open(target_pr, "rb") as f:
    pr_data = f.read()
print(f"Loaded {len(pr_data)/(1024*1024):.2f} MB in {time.time()-t0:.2f}s")

print("\n--- Adobe Premiere Pro.exe Results ---")
for name, (orig, repl, desc) in PR_PATTERNS.items():
    orig_matches = find_all_exact(pr_data, orig)
    repl_matches = find_all_exact(pr_data, repl)
    print(f"[{name}]")
    print(f"  Description: {desc}")
    print(f"  Original matches: {len(orig_matches)} {[hex(x) for x in orig_matches]}")
    print(f"  Patched matches : {len(repl_matches)} {[hex(x) for x in repl_matches]}")

target_jpeg = Path(r"D:\PR INSTALL\prsolved\pr\jpeg_wrapper.dll")
if target_jpeg.exists():
    print(f"\nLoading {target_jpeg.name}...")
    with open(target_jpeg, "rb") as f:
        jpeg_data = f.read()
    print(f"Loaded {len(jpeg_data)/(1024*1024):.2f} MB")
    print("\n--- jpeg_wrapper.dll Results ---")
    for name, (orig, repl, desc) in JPEG_PATTERNS.items():
        orig_matches = find_all_exact(jpeg_data, orig)
        repl_matches = find_all_exact(jpeg_data, repl)
        print(f"[{name}]")
        print(f"  Description: {desc}")
        print(f"  Original matches: {len(orig_matches)} {[hex(x) for x in orig_matches]}")
        print(f"  Patched matches : {len(repl_matches)} {[hex(x) for x in repl_matches]}")
else:
    print(f"\n{target_jpeg.name} does not exist in pr root.")
