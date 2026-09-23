"""Test genuine protection functions on mock files in analisa/sandbox."""

import os
import shutil
from pathlib import Path

sandbox = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox")
sandbox.mkdir(parents=True, exist_ok=True)

mock_hosts = sandbox / "hosts"
mock_hosts.write_text("# Initial hosts file\n127.0.0.1 localhost\n", encoding="utf-8")

HOSTS_HEADER = "# --- BEGIN pr26win Adobe Genuine Protection ---"
HOSTS_FOOTER = "# --- END pr26win Adobe Genuine Protection ---"

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

def add_hosts_protection(hosts_path: Path):
    content = hosts_path.read_text(encoding="utf-8", errors="ignore")
    # Remove existing block if present
    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()

    entries = [HOSTS_HEADER]
    for d in sorted(ADOBE_GENUINE_DOMAINS):
        entries.append(f"0.0.0.0 {d}")
    entries.append(HOSTS_FOOTER)
    
    new_content = content.rstrip() + "\n\n" + "\n".join(entries) + "\n"
    hosts_path.write_text(new_content, encoding="utf-8")

def remove_hosts_protection(hosts_path: Path):
    content = hosts_path.read_text(encoding="utf-8", errors="ignore")
    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        new_content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()
        hosts_path.write_text(new_content.strip() + "\n", encoding="utf-8")

print("Original:")
print(mock_hosts.read_text())

add_hosts_protection(mock_hosts)
print("After adding protection:")
print(mock_hosts.read_text())

remove_hosts_protection(mock_hosts)
print("After removing protection:")
print(mock_hosts.read_text())

assert mock_hosts.read_text().strip() == "# Initial hosts file\n127.0.0.1 localhost"
print("Assertion PASSED! Clean add and remove verified.")
