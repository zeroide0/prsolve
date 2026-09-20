import os
import re
from pathlib import Path

# Helper to parse hex pattern with '??' or wildcard to regex
def hex_to_regex(hex_str):
    hex_str = hex_str.strip().replace(" ", "")
    parts = []
    i = 0
    while i < len(hex_str):
        pair = hex_str[i:i+2]
        if pair == "??" or pair == "?":
            parts.append(b'.')
        else:
            parts.append(re.escape(bytes.fromhex(pair)))
        i += 2
    return re.compile(b''.join(parts), re.DOTALL)

# Patterns defined in config_v421.ini
PATTERNS = {
    "ProfileStage_ValidationOverride_PR": (
        "080FB6800C010000C332C0C3488B05A942760D",
        "080FB6800C01000090B001C3488B05A942760D"
    ),
    "PipelineRouting_QueueHandler_PR": (
        "24384883C4205FC3FF2502832905",
        "24384883C4205FC3B800000000C3"
    ),
    "PipelineRouting_StructuralRedirect_PR": (
        "488B08C5F81001C5F811064C8976104C897618",
        "488B08C5F81001C5F811064C8976004C897618"
    ),
    "PipelineRouting_FlagInitialization_PR": (
        "66C783D000000000018B8424A8000000",
        "66C783D000000001018B8424A8000000"
    ),
    "PipelineRouting_SecondaryBypass_PR": (
        "4500C680D000000000498B75004881C690",
        "4500C680D000000001498B75004881C690"
    ),
    # Also check beta patterns just in case
    "ProfileStage_ValidationOverride_PRB": (
        "080FB68091000000C3B001C3CCCCCCCCCCCCCCCC",
        "080FB6809100000090B001C3CCCCCCCCCCCCCCCC"
    ),
    "PipelineRouting_QueueHandler_PRB": (
        "24384883C4205FC3FF2502832905",
        "24384883C4205FC3B800000000C3"
    ),
    "PipelineRouting_StructuralRedirect_PRB": (
        "488B08C5F81001C5F811064C8976104C897618",
        "488B08C5F81001C5F811064C8976004C897618"
    ),
    "PipelineRouting_FlagInitialization_PRB": (
        "66C783D000000000018B8424A8000000",
        "66C783D000000001018B8424A8000000"
    ),
    "PipelineRouting_SecondaryBypass_PRB": (
        "4500C680D000000000498B75004881C690",
        "4500C680D000000001498B75004881C690"
    ),
    # Default patterns
    "ProfileExpired2": (
        "85C075??B892010000E9",
        "85C07500B800000000E9"
    ),
    "ProfileExpired1": (
        "85C075??????????75??B892010000E9",
        "31C075004883FF0F7500B800000000E9"
    ),
    "ProfileExpired9_AMEPP": (
        "E8????????????75??B918000000E8????????48????????????4885C00F84????0000C5F9EFC0C5F81100488D0D????????C7",
        "E8????????????6690B918000000E8????????48????????????4885C0660F1F440000C5F9EFC0C5F81100488D0D????????C7"
    ),
    "ProfileExpired9_2026_A": (
        "????????85F67546B918000000E8",
        "????????85F66690B918000000E8"
    ),
    "ProfileExpired9_2026_B": (
        "488BD04885C00F84????????C5F9EFC0",
        "488BD04885C0660F1F440000C5F9EFC0"
    ),
    "TeamProjectEnabler": (
        "488379????740A488379????7403B001C332C0C3",
        "488379????740A488379????7403B001C3B001C3"
    ),
    "TeamProjectEnabler2": (
        "488D4B08FF15??????004885C07408B0014883C4205BC332C04883C4",
        "488D4B08FF15??????004885C07408B0014883C4205BC3B0014883C4"
    ),
    "DvaWF_AlwaysTrue": (
        "7403B001C332C0C3",
        "7403B001C3B001C3"
    ),
    "DvaWF_JZ_Short": (
        "7408B0014883C4205BC332C04883C4205BC3",
        "7408B0014883C4205BC3B0014883C4205BC3"
    ),
}

target_file = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
print(f"Reading {target_file} ({target_file.stat().st_size / 1024 / 1024:.2f} MB)...")
with open(target_file, "rb") as f:
    data = f.read()

print("Scanning Adobe Premiere Pro.exe for patterns...")
for name, (pat_hex, rep_hex) in PATTERNS.items():
    rx = hex_to_regex(pat_hex)
    matches = [m.start() for m in rx.finditer(data)]
    # Also check if already patched
    rx_patched = hex_to_regex(rep_hex)
    patched_matches = [m.start() for m in rx_patched.finditer(data)]
    print(f"Pattern {name:40s} -> Unpatched matches: {len(matches)} {['0x%X' % m for m in matches[:5]]} | Patched matches: {len(patched_matches)}")
