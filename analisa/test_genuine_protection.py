"""Test implementation of Genuine Protection (Firewall + Hosts + Cache Cleanup)."""

import os
import subprocess
from pathlib import Path

# Core Adobe Genuine / License Telemetry domains responsible for:
# 1. "Anda menggunakan aplikasi Adobe tidak berlisensi (5 hari tersisa)" popup
# 2. "Silakan baca dan terima Ketentuan Penggunaan Umum Adobe" modal
ADOBE_GENUINE_DOMAINS = (
    "prod.adobegenuine.com",
    "genuine.adobe.com",
    "lcs-cpc.adobe.io",
    "lcs-robs.adobe.io",
    "lcs-ulecs.adobe.io",
    "cc-api-data.adobe.io",
    "ic.adobe.io",
    "gcos.adobe.io",
    "hbc.adobe.io",
    "fp.adobestats.io",
    "crs.cr.adobe.com",
    "workflow.licenses.adobe.com",
    "workflow-stage.licenses.adobe.com",
    "adobe.io",
    "adobestats.io",
    "ims-na1.adobelogin.com",
    "ims-prod06.adobelogin.com",
    "na1r.services.adobe.com",
    "services.adobelogin.com",
    "auth.services.adobe.com",
    "oobe.adobe.com",
    "adobeid-na1.services.adobe.com",
    "edge.adobedc.net",
    "license.adobe.com",
    "licenses.adobe.com",
)

FIREWALL_RULE_NAME = "Block Adobe Premiere Pro Outbound (pr26win)"
FIREWALL_HEADLESS_RULE_NAME = "Block Adobe Premiere Headless Outbound (pr26win)"

def get_firewall_command_add(program_path: str, rule_name: str) -> list:
    return [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={rule_name}",
        "dir=out",
        "action=block",
        f"program={program_path}",
        "enable=yes",
        "profile=any",
        "description=Blocks Adobe Premiere Pro from phoning home to genuine check servers",
    ]

def get_firewall_command_delete(rule_name: str) -> list:
    return [
        "netsh", "advfirewall", "firewall", "delete", "rule",
        f"name={rule_name}"
    ]

print("Firewall Add Command:")
print(" ".join(get_firewall_command_add(r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe", FIREWALL_RULE_NAME)))

# Hosts block format
hosts_block_header = "# --- BEGIN pr26win Adobe Genuine Protection ---"
hosts_block_footer = "# --- END pr26win Adobe Genuine Protection ---"

def generate_hosts_entries() -> str:
    lines = [hosts_block_header]
    for d in sorted(ADOBE_GENUINE_DOMAINS):
        lines.append(f"0.0.0.0 {d}")
    lines.append(hosts_block_footer)
    return "\n".join(lines) + "\n"

print("\nGenerated Hosts Block Preview:")
print(generate_hosts_entries()[:300] + "...")
