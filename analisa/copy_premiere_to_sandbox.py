import shutil
import time
from pathlib import Path

src = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
dst = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox\Adobe Premiere Pro.exe")

print(f"Copying {src.name} to sandbox...")
t0 = time.time()
shutil.copy2(src, dst)
print(f"Copied {dst.stat().st_size / (1024*1024):.2f} MB in {time.time()-t0:.2f}s")
