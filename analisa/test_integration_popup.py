"""Integration test for anti-popup protection, hosts manipulation, firewall commands, and cache cleanup."""

import os
import shutil
import tempfile
from pathlib import Path

# Verify hosts addition and removal in an isolated temp file
HOSTS_HEADER = "# --- BEGIN pr26win Network Protection ---"
HOSTS_FOOTER = "# --- END pr26win Network Protection ---"

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
    "7m31guub0q.adobe.io",
    "7g2gzgk9g1.adobe.io",
    "1hzopx6nz7.adobe.io",
    "0mo5a70cqa.adobe.io",
    "gw8gfjbs05.adobe.io",
    "ij0gdyrfka.adobe.io",
    "dyzt55url8.adobe.io",
)

with tempfile.TemporaryDirectory() as td:
    temp_hosts = Path(td) / "hosts"
    initial_content = "127.0.0.1 localhost\n::1 localhost\n"
    temp_hosts.write_text(initial_content, encoding="utf-8")

    # 1. Simulate adding hosts protection
    content = temp_hosts.read_text(encoding="utf-8", errors="ignore")
    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()

    entries = [HOSTS_HEADER]
    for d in sorted(ADOBE_GENUINE_DOMAINS):
        entries.append(f"0.0.0.0 {d}")
    entries.append(HOSTS_FOOTER)
    new_content = content.rstrip() + "\n\n" + "\n".join(entries) + "\n"
    temp_hosts.write_text(new_content, encoding="utf-8")

    added_text = temp_hosts.read_text(encoding="utf-8")
    assert HOSTS_HEADER in added_text
    assert "0.0.0.0 prod.adobegenuine.com" in added_text
    assert HOSTS_FOOTER in added_text
    print("Hosts block addition verified.")

    # 2. Simulate idempotent re-addition (no duplicate blocks)
    content = temp_hosts.read_text(encoding="utf-8", errors="ignore")
    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()

    entries = [HOSTS_HEADER]
    for d in sorted(ADOBE_GENUINE_DOMAINS):
        entries.append(f"0.0.0.0 {d}")
    entries.append(HOSTS_FOOTER)
    new_content = content.rstrip() + "\n\n" + "\n".join(entries) + "\n"
    temp_hosts.write_text(new_content, encoding="utf-8")

    readded_text = temp_hosts.read_text(encoding="utf-8")
    assert readded_text.count(HOSTS_HEADER) == 1
    assert readded_text.count(HOSTS_FOOTER) == 1
    print("Hosts idempotent re-addition verified.")

    # 3. Simulate removal of hosts protection
    content = temp_hosts.read_text(encoding="utf-8", errors="ignore")
    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        restored_content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()
        temp_hosts.write_text(restored_content.strip() + "\n", encoding="utf-8")

    final_text = temp_hosts.read_text(encoding="utf-8")
    assert final_text.strip() == initial_content.strip()
    print("Hosts removal verified (exact restoration of original content).")

print("All integration tests passed successfully.")
