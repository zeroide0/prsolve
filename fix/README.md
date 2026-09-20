# pr26win — Adobe Premiere Pro 2026 Patcher (Windows)

Patcher untuk **Adobe Premiere Pro 2026 (v26.x)** pada sistem operasi Windows x64 dengan arsitektur, pola pattern matching, dan gaya penulisan kode yang identik dengan [`fork.py`](file:///D:/PR%20INSTALL/prsolved/fork.py) (berbasis [`resolve-patch`](https://github.com/bearlikelion/resolve-patch)).

---

## 📌 Target yang Didukung

1. **Adobe Premiere Pro (`premiere`)**
   - File target: `Adobe Premiere Pro.exe`
   - Bypasses:
     - `ProfileStage_ValidationOverride`: Mengubah exit stub validasi lisensi profile dari `xor al, al; ret` (`32 C0 C3`) menjadi `nop; mov al, 1; ret` (`90 B0 01 C3`).
     - `PipelineRouting_StructuralRedirect`: Mengalihkan struct entitlement offset dari `10h` ke `00h` (`4C 89 76 10` -> `4C 89 76 00`).
     - `PipelineRouting_SecondaryBypass`: Mengubah entitlement active byte flag dari `0` ke `1` (`C6 80 D0 00 00 00 00` -> `C6 80 D0 00 00 00 01`).
     - `PipelineRouting_FlagInitialization`: Menginisialisasi entitlement flag word menjadi `0101h` (`66 C7 83 D0 00 00 00 00 01` -> `66 C7 83 D0 00 00 00 01 01`).
2. **PProHeadless (`headless`)**
   - File target: `PProHeadless.exe` (Background rendering engine)
   - Bypasses:
     - `ProfileStage_ValidationOverride`
     - `PipelineRouting_SecondaryBypass`
     - `PipelineRouting_FlagInitialization`
3. **JPEG Wrapper (`jpeg`)**
   - File target: `jpeg_wrapper.dll`
   - Fitur:
     - `Enable_ExtendedHardwareAcceleration`: Mengaktifkan flag kapabilitas akselerasi hardware pada kedua percabangan (`C7 84 24 34 01 00 00 00 00 00 00` -> `C7 84 24 34 01 00 00 01 00 00 00`).

---

## 🛠️ Fitur & Arsitektur Kode

- **Pola Kompilasi Pattern Caching**: Menggunakan regex bytes dengan wildcard `None` (`_compile_pattern` dan `_compiled_pattern_cache`).
- **Atomic File Write with Retry**: Penulisan file aman melalui file `.new` dan `os.replace` dengan 5 kali percobaan retry jika terkunci sementara oleh AV/Explorer (`_atomic_write_with_retry`).
- **Backup & Restore Otomatis**: Membuat file `.bak` otomatis sebelum melakukan perubahan. Saat restore, versi PE divalidasi agar tidak terjadi *downgrade*.
- **Deteksi Status (Read-Only)**: Mengecek apakah status binary adalah `MISSING`, `UNSUPPORTED`, `UNPATCHED`, atau `PATCHED` tanpa memodifikasi file.
- **Interactive Terminal UI**: Navigasi arrow key menggunakan `msvcrt` dan ANSI escape sequence (single-select & multi-select dengan toggle Spasi dan shortcut konfirmasi Enter / batal Esc).
- **Unattended CLI Execution**: Mendukung flag CLI (`--targets`, `--path`, `--restore`, `--skip-admin`) untuk scripting dan mode non-TTY.

---

## 🚀 Cara Penggunaan

Jalankan terminal / PowerShell sebagai **Administrator**:

### 1. Mode Interaktif (Arrow-Key Menu)
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py
```

Kontrol Menu:
- `Up` / `Down` : Berpindah pilihan
- `Space`       : Toggle centang target
- `A`           : Pilih semua / batalkan semua
- `Enter`       : Konfirmasi pilihan
- `Esc` / `q`   : Keluar / Batal

### 2. Mode Perintah (CLI / Otomatis)
Patch semua target:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --targets all
```

Patch target spesifik:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --targets premiere,jpeg
```

Tentukan path instalasi kustom:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --path "D:\PR INSTALL\prsolved\pr\Adobe Premiere Pro.exe" --targets all
```

Restore kembali binary original dari `.bak`:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --restore --targets all
```
