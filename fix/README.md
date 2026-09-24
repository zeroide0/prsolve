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
      - `CodecEntitlement_ValidationOverride`: Mengubah entry point validator lisensi codec HEVC / H.265 menjadi `mov al, 1; ret` (`B0 01 C3`) pada kedua fungsi validator internal (`0x1AD423B0` dan `0x1AD42500`). Mencegah sistem freeze dan memvalidasi izin pemutaran codec.
      - `ImporterStream_EntitlementBypass`: Mengubah percabangan validasi entitlement MP4/HEVC (`83 B8 A4 01 00 00 00 75 0D C7 44 24 74 66 00 07 A0`) dari `jne` (`75 0D`) menjadi unconditional `jmp` (`EB 0D`). Mencegah error `0xA0070066` (`imBadHeader` / `-1610153882`) yang menyebabkan video rekaman HEVC OBS Studio diimpor sebagai Audio Only.
      - `ImporterStream_FallbackBypass`: Mengubah percabangan validasi sekunder video stream (`41 83 F8 01 7E 11 84 C0 75 0D C7 44 24 74 66 00 07 A0`) dari `jne` (`75 0D`) menjadi `jmp` (`EB 0D`). Menjamin stream video tidak dialihkan (fall back) ke audio-only importer.
2. **PProHeadless (`headless`)**
   - File target: `PProHeadless.exe` (Background preview & rendering engine)
   - Bypasses:
     - `ProfileStage_ValidationOverride`
     - `PipelineRouting_SecondaryBypass`
     - `PipelineRouting_FlagInitialization`
     - `CodecEntitlement_ValidationOverride`: Mem-bypass validator lisensi HEVC pada background rendering engine (`0x1857BBA0` dan `0x1857BCF0`) agar render preview (menekan tombol `Enter`) berjalan lancar tanpa crash atau pop-up.
     - `ImporterStream_EntitlementBypass`: Mem-bypass error `0xA0070066` pada background engine (`0x18611EF2`).
     - `ImporterStream_FallbackBypass`: Mem-bypass fallback audio-only pada background engine (`0x18612C03`).
3. **JPEG Wrapper (`jpeg`)**
   - File target: `jpeg_wrapper.dll`
   - Fitur:
     - `Enable_ExtendedHardwareAcceleration`: Mengaktifkan flag kapabilitas akselerasi hardware pada kedua percabangan (`C7 84 24 34 01 00 00 00 00 00 00` -> `C7 84 24 34 01 00 00 01 00 00 00`).
4. **HEVC Codec Provisioning & Video Extension (Solusi Blank Preview / Black Screen & Audio Only)**
   - **MainConcept HEVC Decoder & Encoder Bundle**: Menyediakan `mc_dec_hevc.dll`, `mc_enc_hevc.dll`, serta manifest `.dat` yang dikemas dalam `hevc_codecs.zip`.
   - **Multi-Version Tier2 Deployment**: Otomatis mengekstrak dan memasang library ke `C:\Users\Public\Documents\AdobeInstalledCodecsTier2\14.3.0.25617`, `14.3.0`, `14.3`, `14.0`, `4.3.4`, `4.3`, `4.0`, `26.0`, serta folder aplikasi Premiere Pro.
   - **Windows Media Foundation HEVC Video Extension (`Microsoft.HEVCVideoExtension_x64.appx`)**: Otomatis memasang ekstensi codec HEVC resmi Windows untuk `AVDecoderMFT`. Mengatasi error *"Frame substitution recursion attempt aborting"* dan layar hitam pada video rekaman OBS Studio (NVENC / `hvc1`).
   - **Stale Media Cache Purging**: Membersihkan file cache `.ims`, `.mcdb`, `.pek`, dan `.cfa` lama di `AppData\Roaming\Adobe\Common\Media Cache Files`, `Media Cache`, `Peak Files`, dan `Metadata Cache` agar indeks decode yang sebelumnya rusak / diimpor sebagai audio-only otomatis di-refresh dengan stream video baru.
   - **Auto-Download Fallback**: Jika dijalankan mandiri tanpa clone repository, skrip otomatis mengunduh bundle codec dan appx langsung dari repositori dengan retry mechanism.
5. **Anti-Popup & Genuine Protection (Solusi Issue Pop-up / 5 Hari Tersisa)**
   - **Windows Defender Firewall Outbound Rules**: Memblokir koneksi internet keluar untuk `Adobe Premiere Pro.exe` dan `PProHeadless.exe` agar background check tidak dapat menghubungi server Adobe.
   - **Hosts Protection**: Memblokir domain verifikasi cloud & telemetri lisensi Adobe (`prod.adobegenuine.com`, `genuine.adobe.com`, `lcs-cpc.adobe.io`, `workflow.licenses.adobe.com`, dll.) secara bersih di `C:\Windows\System32\drivers\etc\hosts`.
   - **License & Media Cache Cleanup**: Menghapus cache token & notifikasi kedaluwarsa lokal (`SLStore`, `OperatingEnvironment`, `OOBE\opgp`, file log) serta media cache yang korup agar dialog peringatan yang tersimpan tidak muncul kembali.

---

## 🛠️ Fitur & Arsitektur Kode

- **Pola Kompilasi Pattern Caching**: Menggunakan regex bytes dengan wildcard `None` (`_compile_pattern` dan `_compiled_pattern_cache`).
- **Atomic File Write with Retry**: Penulisan file aman melalui file `.new` dan `os.replace` dengan 5 kali percobaan retry jika terkunci sementara oleh AV/Explorer (`_atomic_write_with_retry`).
- **Backup & Restore Otomatis**: Membuat file `.bak` otomatis sebelum melakukan perubahan. Saat restore, versi PE divalidasi agar tidak terjadi *downgrade*.
- **Deteksi Status (Read-Only)**: Mengecek apakah status binary adalah `MISSING`, `UNSUPPORTED`, `UNPATCHED`, atau `PATCHED` tanpa memodifikasi file.
- **Perlindungan Jaringan Anti-Popup Otomatis**: Secara otomatis mengaktifkan aturan firewall dan blokir hosts saat melakukan patch, serta mencopotnya saat restore.
- **Pencarian Path Portable**: Mendukung pencarian dinamis di direktori lokal workspace, registry Windows, maupun default path sistem.
- **Interactive Terminal UI**: Navigasi arrow key menggunakan `msvcrt` dan ANSI escape sequence (single-select & multi-select dengan toggle Spasi dan shortcut konfirmasi Enter / batal Esc).
- **Unattended CLI Execution**: Mendukung flag CLI (`--targets`, `--path`, `--restore`, `--block-network`, `--unblock-network`, `--clean-cache`, `--skip-admin`) untuk scripting dan mode non-TTY.

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

Patch semua target (Premiere Pro, PProHeadless, JPEG Wrapper, HEVC Codec Bypass, Firewall & Hosts Protection):
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --targets all
```

Patch target spesifik:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --targets premiere,headless
```

Konfigurasi perlindungan Anti-Popup saja (Firewall + Hosts + Cache Cleanup):
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --block-network
```

Memasang / menyinkronkan codec HEVC library saja (solusi blank preview & pop-up codec):
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --install-codecs
```

Membersihkan cache lisensi / notifikasi pop-up:
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --clean-cache
```

Mencopot aturan Anti-Popup (unblock firewall & hosts):
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --unblock-network
```

Restore kembali binary original dari `.bak` (dan mencopot proteksi popup):
```powershell
& .\venv\Scripts\python.exe .\fix\pr_patch.py --restore --targets all
```
