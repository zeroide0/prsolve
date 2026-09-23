"""Analysis of Anti-Popup and Adobe Genuine Service mitigation methods."""

import os
import subprocess
from pathlib import Path

# 1. Inspect Adobe Genuine Service and processes on this machine
services = ["AGSService", "AGMService"]
for s in services:
    res = subprocess.run(["sc", "query", s], capture_output=True, text=True)
    print(f"Service {s} status: {res.returncode == 0}")

# 2. Inspect running Adobe processes that trigger popups
suspicious_procs = [
    "AGSService.exe",
    "AGMService.exe",
    "AdobeGCClient.exe",
    "AdobeNotificationClient.exe",
    "adobe_licensing_wf.exe",
    "adobe_licensing_helper.exe",
    "Adobe Desktop Service.exe"
]
res = subprocess.run(["tasklist"], capture_output=True, text=True)
running = [p for p in suspicious_procs if p.lower() in res.stdout.lower()]
print("Running popup-related processes:", running)

# 3. Inspect common cache directories where warning flags are stored
cache_paths = [
    os.path.expandvars(r"%ProgramData%\Adobe\OperatingEnvironment"),
    os.path.expandvars(r"%ProgramData%\Adobe\SLStore"),
    os.path.expandvars(r"%ProgramData%\Adobe\NGL"),
    os.path.expandvars(r"%AppData%\Adobe\NGL"),
    os.path.expandvars(r"%LocalAppData%\Adobe\OOBE"),
    os.path.expandvars(r"%CommonProgramFiles(x86)%\Adobe\Adobe Desktop Common\AdobeGenuineClient"),
]
for cp in cache_paths:
    exists = os.path.exists(cp)
    print(f"Cache path: {cp:65s} -> Exists: {exists}")
