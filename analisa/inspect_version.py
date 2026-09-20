import pefile
from pathlib import Path

target = Path(r"D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe")
pe = pefile.PE(str(target))

if hasattr(pe, 'FileInfo'):
    for fileinfo in pe.FileInfo:
        for fi in fileinfo:
            if fi.Key.decode('utf-8', errors='ignore') == 'StringFileInfo':
                for st in fi.StringTable:
                    for entry in st.entries.items():
                        k = entry[0].decode('utf-8', errors='ignore')
                        v = entry[1].decode('utf-8', errors='ignore')
                        print(f"{k}: {v}")
            elif fi.Key.decode('utf-8', errors='ignore') == 'VarFileInfo':
                for var in fi.Var:
                    for k, v in var.entry.items():
                        print(f"Var: {k} = {v}")
