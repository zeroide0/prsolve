"""Sandbox test script in analisa to test patching and restoring on copies of binaries."""

import os
import shutil
from pathlib import Path

# Set up sandbox directory
sandbox_dir = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox")
if sandbox_dir.exists():
    shutil.rmtree(sandbox_dir)
sandbox_dir.mkdir(parents=True, exist_ok=True)

pr_source = Path(r"D:\PR INSTALL\prsolved\pr")

# For testing, let's copy jpeg_wrapper.dll first (16 MB - fast to copy and test)
test_jpeg = sandbox_dir / "jpeg_wrapper.dll"
shutil.copy(pr_source / "jpeg_wrapper.dll", test_jpeg)
print(f"Copied test jpeg_wrapper.dll: {test_jpeg.stat().st_size} bytes")

# We can also test patching on a byte slice or the actual Adobe Premiere Pro.exe
# To avoid taking 745 MB if not needed, we can test byte matching and replacement logic in-memory!
print("Sandbox environment initialized.")
