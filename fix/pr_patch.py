"""pr26win — patch Adobe Premiere Pro.exe, PProHeadless.exe, and jpeg_wrapper.dll
to bypass license checks and enable hardware acceleration on Windows.

Adapted specifically for Adobe Premiere Pro 2026 (v26.x) on Windows.
Architecture and pattern engine based on resolve-patch.
"""

import argparse
import ctypes
import ctypes.wintypes
import logging
import msvcrt
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import winreg
import zipfile
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

logger = logging.getLogger("pr26win")


# --------------------------------------------------------------------- constants

DEFAULT_PATH = r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe"

# Standard install paths for Premiere Pro 2026 components
DEFAULT_HEADLESS_PATHS = (
    r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\PProHeadless.exe",
)

DEFAULT_JPEG_PATHS = (
    r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\jpeg_wrapper.dll",
)

# Registry keys / file extensions used by the auto-locator
SHELLOPEN_EXTENSION_KEYS = (
    r"Software\Classes\Adobe.PremierePro.Project\shell\open\command",
    r"Software\Classes\Premiere.Project\shell\open\command",
)

# Firewall rule names for outbound blocking
FIREWALL_RULE_PREMIERE = "Block Adobe Premiere Pro Outbound (pr26win)"
FIREWALL_RULE_HEADLESS = "Block Adobe Premiere Headless Outbound (pr26win)"

# Hosts file path and markers
HOSTS_FILE_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
HOSTS_HEADER = "# --- BEGIN pr26win Network Protection ---"
HOSTS_FOOTER = "# --- END pr26win Network Protection ---"

# Adobe cloud licensing and telemetry endpoints known to trigger genuine expiration modals
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

# Pattern entry: int (0..255) for an exact byte, None for a single-byte wildcard.
PatternByte = Optional[int]
Pattern = Sequence[PatternByte]
# Replacement: either fixed bytes, or a callable computing bytes from context.
ReplacementFn = Callable[[bytearray, int, Pattern], bytes]
Replacement = Union[bytes, ReplacementFn]


class PatchError(Exception):
    """Anything that prevents the patch from proceeding cleanly."""


# --------------------------------------------------------------------- pattern matching

_compiled_pattern_cache: dict = {}


def _compile_pattern(pattern: Pattern) -> "re.Pattern[bytes]":
    key = tuple(pattern)
    rx = _compiled_pattern_cache.get(key)
    if rx is None:
        parts = [b'.' if b is None else re.escape(bytes([b])) for b in pattern]
        rx = re.compile(b''.join(parts), re.DOTALL)
        _compiled_pattern_cache[key] = rx
    return rx


def find_all(data: bytes, pattern: Pattern, start: int = 0,
             end: Optional[int] = None) -> list:
    """Return absolute offsets where `pattern` matches inside `data[start:end]`."""
    if end is None:
        end = len(data)
    return [m.start() for m in _compile_pattern(pattern).finditer(data, start, end)]


# --------------------------------------------------------------------- replacement callables

def _force_profile_validation_true(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Override profile validation stage check in Adobe Premiere Pro (Windows x64 PE).

    Original sequence:
      0F B6 80 0C 01 00 00  movzx eax, byte ptr [rax + 10Ch]
      C3                    ret
      32 C0                 xor al, al
      C3                    ret

    Patch the exit stub to `90 B0 01 C3` (nop; mov al, 1; ret) so it unconditionally
    reports license entitlement as valid without failing into the unactivated fallback.
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[7:11] = b'\x90\xB0\x01\xC3'
    return bytes(res)


def _force_structural_redirect(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Pipeline routing structural redirect bypass (Windows x64 PE).

    Converts:
      4C 89 76 10  (mov qword ptr [rsi + 10h], r14)
    To:
      4C 89 76 00  (mov qword ptr [rsi + 00h], r14)

    Redirects the context structure entitlement pointer to bypass the enforcement loop.
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[14] = 0x00
    return bytes(res)


def _force_secondary_bypass(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Secondary entitlement flag bypass in pipeline routing.

    Converts:
      C6 80 D0 00 00 00 00  (mov byte ptr [rax + 0D0h], 0)
    To:
      C6 80 D0 00 00 00 01  (mov byte ptr [rax + 0D0h], 1)
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[8] = 0x01
    return bytes(res)


def _force_flag_initialization(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Pipeline routing flag word initialization.

    Converts:
      66 C7 83 D0 00 00 00 00 01  (mov word ptr [rbx + 0D0h], 0100h)
    To:
      66 C7 83 D0 00 00 00 01 01  (mov word ptr [rbx + 0D0h], 0101h)
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[7] = 0x01
    return bytes(res)


def _force_jpeg_hwaccel_b(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Extended hardware acceleration enabler in jpeg_wrapper.dll.

    Converts:
      C7 84 24 34 01 00 00 00 00 00 00  (mov dword ptr [rsp + 134h], 0)
    To:
      C7 84 24 34 01 00 00 01 00 00 00  (mov dword ptr [rsp + 134h], 1)
    Forces the hardware acceleration capability flag to remain active on both branches.
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[22] = 0x01
    return bytes(res)


def _force_codec_validation_true(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Override codec validator functions to return 1 (licensed/enabled).

    Converts:
      40 53 55 56 57 48 83 EC 48 8B D9 48 8D 2D ...  (push rbx; push rbp; push rsi; ...)
    To:
      B0 01 C3 ...  (mov al, 1; ret)
    Forces HEVC / H.265 and proprietary codec feature gates to report valid license
    entitlements, preventing background upgrade network checks, preview render freezes,
    and the Creative Cloud codec modal dialog.
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[0:3] = b'\xB0\x01\xC3'
    return bytes(res)


def _suppress_dialog_prompt(data: bytearray, addr: int, sig: Pattern) -> bytes:
    """Suppress upgrade prompt modal dialogs (mov rax, rdx; ret).

    Converts:
      48 89 5C 24 08  (mov qword ptr [rsp + 8], rbx)
    To:
      48 89 D0 C3     (mov rax, rdx; ret)
    Prevents modal dialog popups from interrupting workflow on missing or optional codec checks.
    """
    res = bytearray(data[addr : addr + len(sig)])
    res[0:4] = b'\x48\x89\xD0\xC3'
    return bytes(res)


# --------------------------------------------------------------------- patch tables

PATCHES_PREMIERE_26: "list[tuple[Pattern, Replacement, int]]" = [
    (
        [0x0F, 0xB6, 0x80, 0x0C, 0x01, 0x00, 0x00,
         0xC3,
         0x32, 0xC0,
         0xC3],
        _force_profile_validation_true,
        1,
    ),
    (
        [0x48, 0x8B, 0x08,
         0xC5, 0xF8, 0x10, 0x01,
         0xC5, 0xF8, 0x11, 0x06,
         0x4C, 0x89, 0x76, 0x10,
         0x4C, 0x89, 0x76, 0x18],
        _force_structural_redirect,
        1,
    ),
    (
        [0x45, 0x00,
         0xC6, 0x80, 0xD0, 0x00, 0x00, 0x00, 0x00,
         0x49, 0x8B, 0x75, 0x00,
         0x48, 0x81, 0xC6, 0x90],
        _force_secondary_bypass,
        1,
    ),
    (
        [0x66, 0xC7, 0x83, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x01,
         0x8B, 0x84, 0x24, 0xA8, 0x00, 0x00, 0x00],
        _force_flag_initialization,
        1,
    ),
    (
        [0x40, 0x53, 0x55, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x48, 0x8B, 0xD9, 0x48, 0x8D, 0x2D],
        _force_codec_validation_true,
        2,
    ),
    (
        [0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x8B, 0x1D, None, None, None, None, 0x48, 0x8B, 0xFA],
        _suppress_dialog_prompt,
        4,
    ),
]

PATCHES_HEADLESS_26: "list[tuple[Pattern, Replacement, int]]" = [
    (
        [0x0F, 0xB6, 0x80, 0x0C, 0x01, 0x00, 0x00,
         0xC3,
         0x32, 0xC0,
         0xC3],
        _force_profile_validation_true,
        1,
    ),
    (
        [0x45, 0x00,
         0xC6, 0x80, 0xD0, 0x00, 0x00, 0x00, 0x00,
         0x49, 0x8B, 0x75, 0x00,
         0x48, 0x81, 0xC6, 0x90],
        _force_secondary_bypass,
        1,
    ),
    (
        [0x66, 0xC7, 0x83, 0xD0, 0x00, 0x00, 0x00, 0x00, 0x01,
         0x8B, 0x84, 0x24, 0xA8, 0x00, 0x00, 0x00],
        _force_flag_initialization,
        1,
    ),
    (
        [0x40, 0x53, 0x55, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x48, 0x8B, 0xD9, 0x48, 0x8D, 0x2D],
        _force_codec_validation_true,
        2,
    ),
]

PATCHES_JPEG_26: "list[tuple[Pattern, Replacement]]" = [
    (
        [0x75, 0x0D,
         0xC7, 0x84, 0x24, 0x34, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
         0xEB, 0x0B,
         0xC7, 0x84, 0x24, 0x34, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        _force_jpeg_hwaccel_b,
    ),
]


# --------------------------------------------------------------------- PE version

def determine_version(target: Union[str, Path, bytes]) -> "tuple[int, int, int]":
    """Read binary version. Prefers Windows Version API for precision if a file path
    is provided, falling back to PE resource table scan."""
    if isinstance(target, (str, Path)):
        filepath = str(target)
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
            if size > 0:
                res = ctypes.create_string_buffer(size)
                if ctypes.windll.version.GetFileVersionInfoW(filepath, 0, size, res):
                    p_info = ctypes.c_void_p()
                    u_len = ctypes.wintypes.UINT()
                    if ctypes.windll.version.VerQueryValueW(res, r"\\", ctypes.byref(p_info), ctypes.byref(u_len)):
                        info_bytes = ctypes.string_at(p_info, u_len.value)
                        dw_file_version_ms, dw_file_version_ls = struct.unpack_from('<II', info_bytes, 8)
                        return (
                            (dw_file_version_ms >> 16) & 0xFFFF,
                            dw_file_version_ms & 0xFFFF,
                            (dw_file_version_ls >> 16) & 0xFFFF,
                        )
        except Exception:
            pass

        with open(filepath, "rb") as f:
            data = f.read()
    else:
        data = target

    # Search backwards for VS_FIXEDFILEINFO signature: 0xFEEF04BD followed by dwStrucVersion 0x00010000
    pos = len(data)
    while True:
        idx = data.rfind(b'\xBD\x04\xEF\xFE', 0, pos)
        if idx < 0:
            break
        if idx + 16 <= len(data):
            struc_ver = struct.unpack_from('<I', data, idx + 4)[0]
            if struc_ver == 0x00010000:
                file_version_ms = struct.unpack_from('<I', data, idx + 8)[0]
                file_version_ls = struct.unpack_from('<I', data, idx + 12)[0]
                major = (file_version_ms >> 16) & 0xFFFF
                if major in (26, 25, 24, 23):
                    return (
                        major,
                        file_version_ms & 0xFFFF,
                        (file_version_ls >> 16) & 0xFFFF,
                    )
        pos = idx

    raise PatchError("Failed to parse PE header version signature.")


# --------------------------------------------------------------------- atomic write

def _atomic_write_with_retry(target: str, payload: bytes, action: str) -> None:
    """Write `payload` to `target` via `target + .new` + os.replace, retrying
    up to 5x on transient locks (AV scanner, Explorer preview thumbnailer, etc.)."""
    tmp_path = target + ".new"
    last_err: Optional[OSError] = None
    for attempt in range(5):
        try:
            with open(tmp_path, "wb") as f:
                f.write(payload)
            os.replace(tmp_path, target)
            return
        except OSError as e:
            last_err = e
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            logger.warning("%s attempt %d/5 failed: %s — retrying in 2s",
                           action, attempt + 1, e)
            time.sleep(2)
    raise PatchError(
        f"Unable to {action} binary: {last_err}. "
        "Make sure Premiere Pro isn't running, close any Explorer window showing the folder, "
        "and run this script as Administrator."
    )


# --------------------------------------------------------------------- main patch / restore

def _select_patches(version: "tuple[int, int, int]") -> "list[tuple[Pattern, Replacement]]":
    """Pick the patch table for the detected version. This tool supports v26.x."""
    major, minor, micro = version
    if major == 26:
        return PATCHES_PREMIERE_26
    raise PatchError(
        f"Premiere Pro {major}.{minor}.{micro} is unsupported. "
        "This tool is optimized for v26.x (2026)."
    )


def patch(premiere_path: str) -> None:
    """Patch Adobe Premiere Pro.exe in place. Backs up to <path>.bak first if and only
    if any patch actually modified the binary."""
    try:
        with open(premiere_path, "rb") as f:
            data = bytearray(f.read())
    except OSError:
        raise PatchError("Adobe Premiere Pro executable could not be located.")

    version = determine_version(premiere_path)
    logger.info("detected Premiere Pro version %d.%d.%d", *version)

    patches = _select_patches(version)
    modified = False

    for i, patch_def in enumerate(patches):
        sig = patch_def[0]
        replacement = patch_def[1]
        expected_matches = patch_def[2] if len(patch_def) > 2 else 1

        occs = find_all(data, sig)
        if not occs:
            logger.info("patch[%d]: no match (already patched or layout differs)", i)
            continue
        if len(occs) != expected_matches:
            logger.warning("patch[%d]: expected %d match(es), found %d — skipping",
                           i, expected_matches, len(occs))
            continue
        for addr in occs:
            repl_bytes = replacement(data, addr, sig) if callable(replacement) else replacement
            logger.info("patch[%d]: applying at file offset 0x%08X (%d bytes)",
                        i, addr, len(repl_bytes))
            data[addr:addr + len(repl_bytes)] = repl_bytes
            modified = True

    if not modified:
        raise PatchError(
            "No patches applied. Either this version is unsupported, the "
            "binary is already patched, or the byte offsets have shifted."
        )

    bak_path = premiere_path + ".bak"
    if not Path(bak_path).exists():
        try:
            shutil.copy(premiere_path, bak_path)
            logger.info("backup written to %s", bak_path)
        except OSError as e:
            raise PatchError(f"Unable to backup Adobe Premiere Pro.exe: {e}") from e
    else:
        logger.info("preserving existing backup at %s", bak_path)

    _atomic_write_with_retry(premiere_path, bytes(data), action="write")


def restore(premiere_path: str) -> None:
    """Restore Adobe Premiere Pro.exe from <path>.bak."""
    bak = premiere_path + ".bak"
    if not Path(bak).exists():
        raise PatchError(f"No backup found at {bak}")
    with open(bak, "rb") as f:
        bak_data = f.read()

    try:
        bak_version = determine_version(bak_data)
    except PatchError:
        bak_version = None
    cur_version = None
    try:
        cur_version = determine_version(premiere_path)
    except (OSError, PatchError):
        pass
    if bak_version and cur_version and bak_version != cur_version:
        logger.warning(
            "backup is %d.%d.%d but current binary is %d.%d.%d — "
            "restore would downgrade. Aborting. Delete %s manually if "
            "you really want to overwrite.",
            *bak_version, *cur_version, bak,
        )
        raise PatchError("backup version mismatch")

    _atomic_write_with_retry(premiere_path, bak_data, action="restore")
    logger.info("restored %s from %s", premiere_path, bak)


# --------------------------------------------------------------------- secondary targets

def patch_headless(headless_path: str) -> None:
    """Patch PProHeadless.exe in place."""
    try:
        with open(headless_path, "rb") as f:
            data = bytearray(f.read())
    except OSError as e:
        raise PatchError(f"could not read {headless_path}: {e}") from e

    modified = False
    for i, patch_def in enumerate(PATCHES_HEADLESS_26):
        sig = patch_def[0]
        replacement = patch_def[1]
        expected_matches = patch_def[2] if len(patch_def) > 2 else 1

        occs = find_all(data, sig)
        if not occs:
            logger.info("headless patch[%d]: no match (already patched or differs)", i)
            continue
        if len(occs) != expected_matches:
            logger.warning("headless patch[%d]: expected %d match(es), found %d — skipping",
                           i, expected_matches, len(occs))
            continue
        for addr in occs:
            repl_bytes = replacement(data, addr, sig) if callable(replacement) else replacement
            logger.info("headless patch[%d]: applying at file offset 0x%08X (%d bytes)",
                        i, addr, len(repl_bytes))
            data[addr:addr + len(repl_bytes)] = repl_bytes
            modified = True

    if not modified:
        raise PatchError(
            f"No headless patches applied to {headless_path}."
        )

    bak_path = headless_path + ".bak"
    if not Path(bak_path).exists():
        try:
            shutil.copy(headless_path, bak_path)
            logger.info("backup written to %s", bak_path)
        except OSError as e:
            raise PatchError(f"unable to backup {headless_path}: {e}") from e
    else:
        logger.info("preserving existing backup at %s", bak_path)

    _atomic_write_with_retry(headless_path, bytes(data), action="write")


def restore_headless(headless_path: str) -> None:
    """Restore PProHeadless.exe from .bak."""
    bak = headless_path + ".bak"
    if not Path(bak).exists():
        raise PatchError(f"No backup found at {bak}")
    with open(bak, "rb") as f:
        bak_data = f.read()
    _atomic_write_with_retry(headless_path, bak_data, action="restore")
    logger.info("restored %s from %s", headless_path, bak)


def patch_jpeg(jpeg_path: str) -> None:
    """Patch jpeg_wrapper.dll in place."""
    try:
        with open(jpeg_path, "rb") as f:
            data = bytearray(f.read())
    except OSError as e:
        raise PatchError(f"could not read {jpeg_path}: {e}") from e

    modified = False
    for i, (sig, replacement) in enumerate(PATCHES_JPEG_26):
        occs = find_all(data, sig)
        if not occs:
            logger.info("jpeg patch[%d]: no match (already patched or differs)", i)
            continue
        if len(occs) > 1:
            logger.warning("jpeg patch[%d]: matched %d times — skipping", i, len(occs))
            continue
        addr = occs[0]
        repl_bytes = replacement(data, addr, sig) if callable(replacement) else replacement
        logger.info("jpeg patch[%d]: applying at file offset 0x%08X (%d bytes)",
                    i, addr, len(repl_bytes))
        data[addr:addr + len(repl_bytes)] = repl_bytes
        modified = True

    if not modified:
        raise PatchError(
            f"No patches applied to {jpeg_path}."
        )

    bak_path = jpeg_path + ".bak"
    if not Path(bak_path).exists():
        try:
            shutil.copy(jpeg_path, bak_path)
            logger.info("backup written to %s", bak_path)
        except OSError as e:
            raise PatchError(f"unable to backup {jpeg_path}: {e}") from e
    else:
        logger.info("preserving existing backup at %s", bak_path)

    _atomic_write_with_retry(jpeg_path, bytes(data), action="write")


def restore_jpeg(jpeg_path: str) -> None:
    """Restore jpeg_wrapper.dll from .bak."""
    bak = jpeg_path + ".bak"
    if not Path(bak).exists():
        raise PatchError(f"No backup found at {bak}")
    with open(bak, "rb") as f:
        bak_data = f.read()
    _atomic_write_with_retry(jpeg_path, bak_data, action="restore")
    logger.info("restored %s from %s", jpeg_path, bak)


# --------------------------------------------------------------------- anti-popup & network protection

def configure_firewall(premiere_path: Optional[str] = None,
                       headless_path: Optional[str] = None,
                       enable: bool = True) -> None:
    """Add or remove Windows Defender Firewall outbound block rules for Premiere executables.

    Prevents background online checks from receiving revocation / license expiration prompts.
    """
    targets = []
    if premiere_path and Path(premiere_path).exists():
        targets.append((FIREWALL_RULE_PREMIERE, premiere_path))
    if headless_path and Path(headless_path).exists():
        targets.append((FIREWALL_RULE_HEADLESS, headless_path))

    for rule_name, exe_path in targets:
        try:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
                capture_output=True,
                text=True,
            )
        except OSError:
            pass

        if enable:
            try:
                cmd = [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={rule_name}",
                    "dir=out",
                    "action=block",
                    f"program={exe_path}",
                    "enable=yes",
                    "profile=any",
                    "description=Block Adobe Premiere Pro outbound telemetry calls (pr26win)",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    logger.info("firewall outbound block added: %s (%s)", rule_name, exe_path)
                else:
                    logger.warning("could not add firewall rule %s: %s", rule_name,
                                   res.stderr.strip() or res.stdout.strip())
            except OSError as e:
                logger.warning("failed to execute netsh for firewall rule %s: %s", rule_name, e)
        else:
            logger.info("firewall rule removed: %s", rule_name)


def configure_hosts(enable: bool = True, hosts_path: Optional[Path] = None) -> None:
    """Add or remove Adobe telemetry endpoints in the Windows hosts file."""
    hp = hosts_path or HOSTS_FILE_PATH
    if not hp.exists():
        logger.warning("hosts file does not exist at %s, skipping hosts protection", hp)
        return

    bak_hosts = hp.with_name("hosts.pr26bak")
    if enable and not bak_hosts.exists():
        try:
            shutil.copy(hp, bak_hosts)
            logger.info("hosts backup written to %s", bak_hosts)
        except OSError as e:
            logger.warning("could not create hosts backup: %s", e)

    try:
        content = hp.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        logger.warning("unable to read hosts file: %s", e)
        return

    if HOSTS_HEADER in content and HOSTS_FOOTER in content:
        start_idx = content.find(HOSTS_HEADER)
        end_idx = content.find(HOSTS_FOOTER) + len(HOSTS_FOOTER)
        content = content[:start_idx].rstrip() + "\n" + content[end_idx:].lstrip()

    if enable:
        entries = [HOSTS_HEADER]
        for d in sorted(ADOBE_GENUINE_DOMAINS):
            entries.append(f"0.0.0.0 {d}")
        entries.append(HOSTS_FOOTER)
        new_content = content.rstrip() + "\n\n" + "\n".join(entries) + "\n"
    else:
        new_content = content.strip() + "\n"

    try:
        if os.name == "nt":
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(hp))
            file_attribute_readonly = 0x0001
            if attrs != -1 and (attrs & file_attribute_readonly):
                ctypes.windll.kernel32.SetFileAttributesW(str(hp), attrs & ~file_attribute_readonly)

        hp.write_text(new_content, encoding="utf-8")
        if enable:
            logger.info("configured %d domains in hosts file (%s)", len(ADOBE_GENUINE_DOMAINS), hp)
        else:
            logger.info("removed hosts protection block from %s", hp)
    except OSError as e:
        logger.warning("failed to write hosts file: %s (run as Administrator)", e)


def clear_license_cache() -> None:
    """Clear stale Adobe licensing notification and Genuine Service caches.

    Removes cached warning flags so that countdown / Terms of Use dialogs do not persist.
    """
    cleaned = 0
    cache_dirs = []

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        cache_dirs.append(Path(local_app_data) / "Adobe" / "OOBE" / "opgp")
        cache_dirs.append(Path(local_app_data) / "Adobe" / "NGL")

    prog_data = os.environ.get("ProgramData", r"C:\ProgramData")
    if prog_data:
        cache_dirs.append(Path(prog_data) / "Adobe" / "OperatingEnvironment")
        cache_dirs.append(Path(prog_data) / "Adobe" / "SLStore")
        cache_dirs.append(Path(prog_data) / "Adobe" / "NGL")

    for cdir in cache_dirs:
        if cdir.exists():
            try:
                if cdir.is_dir():
                    shutil.rmtree(cdir, ignore_errors=True)
                else:
                    cdir.unlink(missing_ok=True)
                logger.info("cleaned cache path: %s", cdir)
                cleaned += 1
            except OSError as e:
                logger.debug("could not remove cache %s: %s", cdir, e)

    app_data = os.environ.get("APPDATA")
    search_dirs = [d for d in [local_app_data, app_data] if d]
    for base in search_dirs:
        adobe_dir = Path(base) / "Adobe"
        if adobe_dir.exists():
            try:
                for log_file in adobe_dir.rglob("gude*.log"):
                    try:
                        log_file.unlink()
                        cleaned += 1
                    except OSError:
                        pass
            except OSError:
                pass

    logger.info("license cache cleanup completed (%d items processed)", cleaned)


def setup_codec_tier2_directory(premiere_dir: Optional[Path] = None) -> bool:
    """Ensure AdobeInstalledCodecsTier2 directory exists and provisions codec libraries.

    Provisions mc_dec_hevc.dll and mc_enc_hevc.dll across all Tier2 versions (4.0, 4.3, 4.3.4)
    and the Premiere Pro application folder. Checks local Tier2 directories, application roots,
    bundled zip archive, and falls back to download, ensuring HEVC/H.265 playback and preview
    function correctly without blank/black screens or missing codec prompts.
    """
    tier2_base = Path(r"C:\Users\Public\Documents\AdobeInstalledCodecsTier2")
    try:
        tier2_base.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    target_versions = ("4.0", "4.3", "4.3.4")
    for ver in target_versions:
        try:
            (tier2_base / ver).mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    known_sources = [
        tier2_base / "4.0",
        tier2_base / "4.3",
        tier2_base / "4.3.4",
        tier2_base / "2.0",
        Path(r"C:\Program Files\Adobe\Adobe Premiere Pro 2026"),
        Path(r"C:\Program Files\Adobe\Adobe Media Encoder 2026"),
        Path(r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files"),
    ]
    if premiere_dir and Path(premiere_dir).exists():
        known_sources.insert(0, Path(premiere_dir))

    dec_source: Optional[Path] = None
    enc_source: Optional[Path] = None

    for loc in known_sources:
        cand_dec = loc / "mc_dec_hevc.dll"
        cand_enc = loc / "mc_enc_hevc.dll"
        if not dec_source and cand_dec.exists() and cand_dec.stat().st_size > 1000000:
            dec_source = cand_dec
        if not enc_source and cand_enc.exists() and cand_enc.stat().st_size > 1000000:
            enc_source = cand_enc

    # If codecs are not found locally on the system, search for bundled zip or download
    if not dec_source or not enc_source:
        zip_candidates = [
            Path(__file__).resolve().parent / "hevc_codecs.zip",
            Path(__file__).resolve().parent / "codecs" / "hevc_codecs.zip",
            Path.cwd() / "hevc_codecs.zip",
            Path.cwd() / "fix" / "hevc_codecs.zip",
            Path.cwd() / "analisa" / "hevc_codecs.zip",
            tier2_base / "hevc_codecs.zip",
        ]
        found_zip = None
        for zc in zip_candidates:
            if zc.exists() and zc.stat().st_size > 1000000:
                found_zip = zc
                break

        if not found_zip:
            download_url = "https://raw.githubusercontent.com/zeroide0/prsolve/main/fix/hevc_codecs.zip"
            dest_zip = tier2_base / "hevc_codecs.zip"
            logger.info("downloading HEVC codec bundle from %s...", download_url)
            try:
                req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp, open(dest_zip, "wb") as out_file:
                    shutil.copyfileobj(resp, out_file)
                if dest_zip.exists() and dest_zip.stat().st_size > 1000000:
                    found_zip = dest_zip
                    logger.info("successfully downloaded HEVC codec bundle (%d bytes)", dest_zip.stat().st_size)
            except Exception as e:
                logger.warning("could not download codec bundle automatically: %s", e)

        if found_zip:
            cache_dir = tier2_base / "cache"
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(found_zip, "r") as zf:
                    for member in ("mc_dec_hevc.dll", "mc_enc_hevc.dll"):
                        if member in zf.namelist():
                            zf.extract(member, cache_dir)
                if (cache_dir / "mc_dec_hevc.dll").exists():
                    dec_source = cache_dir / "mc_dec_hevc.dll"
                if (cache_dir / "mc_enc_hevc.dll").exists():
                    enc_source = cache_dir / "mc_enc_hevc.dll"
            except Exception as e:
                logger.warning("failed to extract codec bundle: %s", e)

    provisioned_count = 0
    for target_ver in target_versions:
        target_dir = tier2_base / target_ver
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            if dec_source and not (target_dir / "mc_dec_hevc.dll").exists():
                shutil.copy2(dec_source, target_dir / "mc_dec_hevc.dll")
                logger.info("provisioned mc_dec_hevc.dll to %s", target_dir)
                provisioned_count += 1
            if enc_source and not (target_dir / "mc_enc_hevc.dll").exists():
                shutil.copy2(enc_source, target_dir / "mc_enc_hevc.dll")
                logger.info("provisioned mc_enc_hevc.dll to %s", target_dir)
                provisioned_count += 1
        except OSError as e:
            logger.debug("could not provision codecs to %s: %s", target_dir, e)

    if premiere_dir and Path(premiere_dir).exists():
        p_dir = Path(premiere_dir)
        try:
            if dec_source and not (p_dir / "mc_dec_hevc.dll").exists():
                shutil.copy2(dec_source, p_dir / "mc_dec_hevc.dll")
                logger.info("provisioned mc_dec_hevc.dll to app directory: %s", p_dir)
                provisioned_count += 1
            if enc_source and not (p_dir / "mc_enc_hevc.dll").exists():
                shutil.copy2(enc_source, p_dir / "mc_enc_hevc.dll")
                logger.info("provisioned mc_enc_hevc.dll to app directory: %s", p_dir)
                provisioned_count += 1
        except OSError as e:
            logger.debug("could not provision codecs to %s: %s", p_dir, e)

    # 4. Ensure Windows Media Foundation HEVC Video Extension is installed
    setup_windows_hevc_extension()

    # 5. Clear stale media cache files so failed decodes are re-indexed
    clear_media_cache()

    if dec_source:
        logger.info("HEVC decoding libraries verified and ready")
        return True
    else:
        logger.warning("HEVC codec libraries could not be provisioned automatically")
        return False


def setup_windows_hevc_extension() -> bool:
    """Ensure Microsoft.HEVCVideoExtension is installed in Windows Media Foundation.

    Windows 10/11 does not ship with HEVC/H.265 Media Foundation transforms by default.
    Without this extension, Premiere Pro's AVDecoderMFT cannot decode MP4 HEVC files
    (resulting in 'Frame substitution recursion attempt aborting' and blank black preview).
    """
    # 1. Check if already installed
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-AppxPackage *HEVC* | Select-Object -ExpandProperty PackageFullName"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            logger.info("Windows HEVC Video Extension is active: %s", res.stdout.strip().splitlines()[0])
            return True
    except Exception as e:
        logger.debug("could not query AppxPackage: %s", e)

    # 2. Search for bundled Appx
    appx_candidates = [
        Path(__file__).resolve().parent / "Microsoft.HEVCVideoExtension_x64.appx",
        Path.cwd() / "Microsoft.HEVCVideoExtension_x64.appx",
        Path.cwd() / "fix" / "Microsoft.HEVCVideoExtension_x64.appx",
        Path.cwd() / "analisa" / "Microsoft.HEVCVideoExtension_x64.appx",
    ]
    found_appx = None
    for cand in appx_candidates:
        if cand.exists() and cand.stat().st_size > 1000000:
            found_appx = cand
            break

    # 3. Fallback download if missing
    if not found_appx:
        download_url = "https://raw.githubusercontent.com/zeroide0/prsolve/main/fix/Microsoft.HEVCVideoExtension_x64.appx"
        dest_appx = Path(os.environ.get("TEMP", ".")) / "Microsoft.HEVCVideoExtension_x64.appx"
        logger.info("downloading Windows HEVC Video Extension from %s...", download_url)
        try:
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_appx, "wb") as out_file:
                shutil.copyfileobj(resp, out_file)
            if dest_appx.exists() and dest_appx.stat().st_size > 1000000:
                found_appx = dest_appx
                logger.info("successfully downloaded Windows HEVC Extension (%d bytes)", dest_appx.stat().st_size)
        except Exception as e:
            logger.warning("could not download Windows HEVC Extension automatically: %s", e)

    # 4. Install via Add-AppxPackage
    if found_appx:
        logger.info("installing Windows HEVC Video Extension (%s)...", found_appx.name)
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Add-AppxPackage -Path '{found_appx}'"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if res.returncode == 0:
                logger.info("Windows HEVC Video Extension successfully installed")
                return True
            else:
                logger.warning("Add-AppxPackage failed: %s", res.stderr.strip())
        except Exception as e:
            logger.warning("failed to execute Add-AppxPackage: %s", e)

    return False


def clear_media_cache() -> int:
    """Purge stale Premiere Pro Media Cache and Media Cache Files (.ims, .mcdb).

    When a media file is opened without proper codecs, Premiere Pro caches negative
    open results (mOpenResult error codes) in .ims files, causing persistent
    'Frame substitution recursion aborting' and black preview playback even after
    codecs are installed. Purging forces Premiere Pro to rebuild fresh stream indexes.
    """
    cleaned = 0
    common_dir = Path(os.environ.get("APPDATA", "")) / "Adobe" / "Common"
    cache_dirs = [
        common_dir / "Media Cache Files",
        common_dir / "Media Cache",
    ]
    for cdir in cache_dirs:
        if cdir.exists():
            try:
                for f in cdir.iterdir():
                    if f.is_file() and f.suffix.lower() in (".ims", ".mcdb", ".cfa", ".pek"):
                        try:
                            f.unlink()
                            cleaned += 1
                        except OSError:
                            pass
            except OSError:
                pass
    logger.info("media cache cleanup completed (%d items purged)", cleaned)
    return cleaned


# --------------------------------------------------------------------- state detection (no writes)

def state_of_premiere(premiere_path: str) -> str:
    """Classify an Adobe Premiere Pro.exe install without modifying it.

    Returns one of: MISSING, UNSUPPORTED, UNPATCHED, PATCHED."""
    if not Path(premiere_path).exists():
        return "MISSING"
    try:
        version = determine_version(premiere_path)
        patches = _select_patches(version)
    except (OSError, PatchError):
        return "UNSUPPORTED"

    with open(premiere_path, "rb") as f:
        data = f.read()

    for item in patches:
        sig = item[0]
        if find_all(data, sig):
            return "UNPATCHED"
    return "PATCHED"


def state_of_headless(headless_path: str) -> str:
    """Classify a PProHeadless.exe install without modifying it."""
    if not Path(headless_path).exists():
        return "MISSING"
    with open(headless_path, "rb") as f:
        data = f.read()
    for item in PATCHES_HEADLESS_26:
        sig = item[0]
        if find_all(data, sig):
            return "UNPATCHED"
    return "PATCHED"


def state_of_jpeg(dll_path: str) -> str:
    """Classify a jpeg_wrapper.dll install without modifying it."""
    if not Path(dll_path).exists():
        return "MISSING"
    with open(dll_path, "rb") as f:
        data = f.read()
    for item in PATCHES_JPEG_26:
        sig = item[0]
        if find_all(data, sig):
            return "UNPATCHED"
    return "PATCHED"


# --------------------------------------------------------------------- locate

def _path_from_registry() -> Optional[str]:
    """Look up Adobe Premiere Pro.exe via file associations in the Windows Registry."""
    for key_path in SHELLOPEN_EXTENSION_KEYS:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "")
                # Extract path from '"C:\...\Adobe Premiere Pro.exe" "%1"'
                m = re.search(r'"([^"]+Adobe Premiere Pro\.exe)"', value, re.IGNORECASE)
                if m and Path(m.group(1)).exists():
                    return m.group(1)
        except OSError:
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "")
                m = re.search(r'"([^"]+Adobe Premiere Pro\.exe)"', value, re.IGNORECASE)
                if m and Path(m.group(1)).exists():
                    return m.group(1)
        except OSError:
            pass
    return None


def locate() -> str:
    """Find Adobe Premiere Pro.exe via local relative paths, registry, or standard paths."""
    # 1. Local workspace / relative check
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "Adobe Premiere Pro.exe",
        script_dir / "pr" / "Adobe Premiere Pro.exe",
        script_dir.parent / "pr" / "Adobe Premiere Pro.exe",
        Path.cwd() / "Adobe Premiere Pro.exe",
        Path.cwd() / "pr" / "Adobe Premiere Pro.exe",
    ]
    for cand in candidates:
        if cand.exists():
            logger.info("Premiere Pro found in local path: %s", cand)
            return str(cand)

    # 2. Registry lookup
    reg_path = _path_from_registry()
    if reg_path is not None:
        logger.info("Premiere Pro found via registry: %s", reg_path)
        return reg_path

    # 3. Default install path
    if Path(DEFAULT_PATH).exists():
        return DEFAULT_PATH

    raise PatchError("Adobe Premiere Pro could not be located.")


def locate_headless(premiere_path: Optional[str] = None) -> list:
    """Return all PProHeadless.exe paths present on disk."""
    paths = []
    if premiere_path:
        p = Path(premiere_path).with_name("PProHeadless.exe")
        if p.exists():
            paths.append(str(p))
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "PProHeadless.exe",
        script_dir / "pr" / "PProHeadless.exe",
        script_dir.parent / "pr" / "PProHeadless.exe",
        Path.cwd() / "PProHeadless.exe",
        Path.cwd() / "pr" / "PProHeadless.exe",
    ]
    for cand in candidates:
        if cand.exists() and str(cand) not in paths:
            paths.append(str(cand))
    for dp in DEFAULT_HEADLESS_PATHS:
        if Path(dp).exists() and dp not in paths:
            paths.append(dp)
    return paths


def locate_jpeg(premiere_path: Optional[str] = None) -> list:
    """Return all jpeg_wrapper.dll paths present on disk."""
    paths = []
    if premiere_path:
        p = Path(premiere_path).with_name("jpeg_wrapper.dll")
        if p.exists():
            paths.append(str(p))
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "jpeg_wrapper.dll",
        script_dir / "pr" / "jpeg_wrapper.dll",
        script_dir.parent / "pr" / "jpeg_wrapper.dll",
        Path.cwd() / "jpeg_wrapper.dll",
        Path.cwd() / "pr" / "jpeg_wrapper.dll",
    ]
    for cand in candidates:
        if cand.exists() and str(cand) not in paths:
            paths.append(str(cand))
    for dp in DEFAULT_JPEG_PATHS:
        if Path(dp).exists() and dp not in paths:
            paths.append(dp)
    return paths


def _kill_premiere() -> bool:
    """Best-effort kill of any running Premiere Pro or related processes."""
    killed = False
    targets = (
        "Adobe Premiere Pro.exe",
        "PProHeadless.exe",
        "dynamiclinkmanager.exe",
        "TeamProjectsLocalHub.exe",
        "dvaapprelauncher.exe",
        "AdobeGCClient.exe",
        "AdobeNotificationClient.exe",
        "AGSService.exe",
        "AGMService.exe",
    )
    for img in targets:
        try:
            res = subprocess.run(
                ["taskkill", "/F", "/IM", img],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                logger.info("killed running %s", img)
                killed = True
        except OSError:
            pass
    return killed


# --------------------------------------------------------------------- CLI & menu

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Patch Adobe Premiere Pro 2026 (v26.x) on Windows. Run as Administrator.",
    )
    p.add_argument("--restore", action="store_true",
                   help="restore from .bak files and exit (applies to all selected targets)")
    p.add_argument("--path", default=None,
                   help="explicit path to Adobe Premiere Pro.exe (skips auto-locate)")
    p.add_argument("--targets", default=None,
                   help="comma-separated targets (premiere, headless, jpeg, all). "
                        "If omitted on a TTY, an interactive menu is shown instead.")
    p.add_argument("--skip-admin", action="store_true",
                   help="skip Administrator check (for sandbox/user directories)")
    p.add_argument("--block-network", action="store_true",
                   help="configure firewall rules and hosts entries to block genuine popups")
    p.add_argument("--unblock-network", action="store_true",
                   help="remove firewall rules and hosts entries")
    p.add_argument("--clean-cache", action="store_true",
                   help="clean stale Adobe licensing/genuine notification caches")
    p.add_argument("--install-codecs", action="store_true",
                   help="provision HEVC/H.265 decoders to AdobeInstalledCodecsTier2 and app directory")
    p.add_argument("--no-network-block", action="store_true",
                   help="skip automatic firewall/hosts blocking when patching")
    return p


def _require_admin(skip: bool = False) -> None:
    """Exit immediately if not running as Administrator on Windows."""
    if skip:
        return
    if sys.platform != "win32":
        logger.error("This script only runs on Windows.")
        raise SystemExit(1)
    if not ctypes.windll.shell32.IsUserAnAdmin():
        logger.error("This script must be run as Administrator.")
        logger.error("Right-click your terminal/PowerShell and choose 'Run as administrator'.")
        raise SystemExit(1)


def _parse_targets(spec: str) -> "set[str]":
    valid = {"premiere", "headless", "jpeg"}
    raw = {t.strip().lower() for t in spec.split(",") if t.strip()}
    if "all" in raw:
        return valid
    bad = raw - valid
    if bad:
        logger.error("unknown --targets value(s): %s (valid: premiere, headless, jpeg, all)",
                     ", ".join(sorted(bad)))
        raise SystemExit(2)
    return raw


def _build_target_rows(premiere_path: Optional[str]) -> "list[tuple[str, str, str, str]]":
    rows: list[tuple[str, str, str, str]] = []
    if premiere_path is not None:
        rows.append(("premiere",
                     "Adobe Premiere Pro.exe",
                     premiere_path,
                     state_of_premiere(premiere_path)))
    else:
        rows.append(("premiere",
                     "Adobe Premiere Pro.exe",
                     DEFAULT_PATH,
                     "MISSING"))

    headless_paths = locate_headless(premiere_path)
    if headless_paths:
        for hp in headless_paths:
            rows.append(("headless",
                         "PProHeadless.exe",
                         hp,
                         state_of_headless(hp)))
    else:
        rows.append(("headless",
                     "PProHeadless.exe",
                     DEFAULT_HEADLESS_PATHS[0],
                     "MISSING"))

    jpeg_paths = locate_jpeg(premiere_path)
    if jpeg_paths:
        for jp in jpeg_paths:
            rows.append(("jpeg",
                         "jpeg_wrapper.dll (HW Acceleration)",
                         jp,
                         state_of_jpeg(jp)))
    else:
        rows.append(("jpeg",
                         "jpeg_wrapper.dll (HW Acceleration)",
                         DEFAULT_JPEG_PATHS[0],
                         "MISSING"))

    return rows


# ----- ANSI & Key handling -----

def _enable_ansi() -> None:
    try:
        STD_OUTPUT_HANDLE = -11
        ENABLE_VT = 0x0004
        kernel32 = ctypes.windll.kernel32
        h = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h, mode.value | ENABLE_VT)
    except Exception:
        pass


def _read_key() -> str:
    ch = msvcrt.getch()
    if ch in (b'\xe0', b'\x00'):
        ch2 = msvcrt.getch()
        return {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right'}.get(ch2, '')
    if ch in (b'\r', b'\n'):
        return 'enter'
    if ch == b'\x1b':
        return 'escape'
    if ch == b' ':
        return 'space'
    if ch == b'\x03':
        raise KeyboardInterrupt
    try:
        return ch.decode('utf-8', errors='replace').lower()
    except UnicodeDecodeError:
        return ''


class _RedrawRegion:
    def __init__(self) -> None:
        self.lines: int = 0

    def render(self, lines: "list[str]") -> None:
        flat: list[str] = []
        for line in lines:
            flat.extend(line.split('\n'))
        if self.lines:
            sys.stdout.write(f'\r\x1b[{self.lines}A')
        for line in flat:
            sys.stdout.write('\x1b[2K' + line + '\n')
        self.lines = len(flat)
        sys.stdout.flush()


def _arrow_single_select(header: str, options: "list[str]", footer: str = "") -> Optional[int]:
    cursor = 0
    region = _RedrawRegion()
    while True:
        lines = [header, ""]
        for i, opt in enumerate(options):
            mark = ">" if i == cursor else " "
            lines.append(f" {mark} {opt}")
        if footer:
            lines.extend(["", footer])
        region.render(lines)
        try:
            key = _read_key()
        except KeyboardInterrupt:
            return None
        if key == 'up' and cursor > 0:
            cursor -= 1
        elif key == 'down' and cursor < len(options) - 1:
            cursor += 1
        elif key == 'enter':
            return cursor
        elif key in ('escape', 'q'):
            return None


def _arrow_multi_select(header: str, options: "list[str]",
                        preselected: "Optional[set[int]]" = None,
                        footer: str = "") -> "Optional[set[int]]":
    cursor = 0
    selected: set[int] = set(preselected) if preselected else set()
    region = _RedrawRegion()
    while True:
        lines = [header, ""]
        for i, opt in enumerate(options):
            arrow = ">" if i == cursor else " "
            box = "[x]" if i in selected else "[ ]"
            lines.append(f" {arrow} {box} {opt}")
        if footer:
            lines.extend(["", footer])
        region.render(lines)
        try:
            key = _read_key()
        except KeyboardInterrupt:
            return None
        if key == 'up' and cursor > 0:
            cursor -= 1
        elif key == 'down' and cursor < len(options) - 1:
            cursor += 1
        elif key == 'space':
            if cursor in selected:
                selected.discard(cursor)
            else:
                selected.add(cursor)
        elif key == 'a':
            selected = set() if len(selected) == len(options) else set(range(len(options)))
        elif key == 'enter':
            return selected if selected else None
        elif key in ('escape', 'q'):
            return None


# --------------------------------------------------------------------- interactive menu

def interactive_menu(premiere_path: Optional[str],
                     action_filter: Optional[str] = None
                     ) -> "tuple[Optional[str], list[tuple[str, str]]]":
    rows = _build_target_rows(premiere_path)

    print()
    print(r"""
    ██████╗ ██████╗ ███████╗███╗   ███╗██╗███████╗██████╗ ███████╗
    ██╔══██╗██╔══██╗██╔════╝████╗ ████║██║██╔════╝██╔══██╗██╔════╝
    ██████╔╝██████╔╝█████╗  ██╔████╔██║██║█████╗  ██████╔╝█████╗  
    ██╔═══╝ ██╔══██╗██╔══╝  ██║╚██╔╝██║██║██╔══╝  ██╔══██╗██╔══╝  
    ██║     ██║  ██║███████╗██║ ╚═╝ ██║██║███████╗██║  ██║███████╗
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
             - Adobe Premiere Pro 2026 Patcher (Windows) -
    """)

    if action_filter is None:
        idx = _arrow_single_select(
            header="\nWhat do you want to do?",
            options=[
                "Patch installed targets (with anti-popup & HEVC protection)",
                "Restore from .bak (and remove popup protection)",
                "Provision HEVC/H.265 Codecs (Fix blank preview & codec modals)",
                "Configure Anti-Popup Protection (Firewall & Hosts)",
                "Remove Anti-Popup Protection",
                "Clean License Notification Cache",
                "Quit",
            ],
            footer="(Up/Down to move, Enter to confirm, q/Esc to cancel)",
        )
        if idx is None or idx == 6:
            return None, []
        if idx == 0:
            action = "patch"
        elif idx == 1:
            action = "restore"
        elif idx == 2:
            return "install_codecs", []
        elif idx == 3:
            return "block_network", []
        elif idx == 4:
            return "unblock_network", []
        elif idx == 5:
            return "clean_cache", []
    else:
        action = action_filter

    if action == "patch":
        relevant = [r for r in rows if r[3] in ("UNPATCHED", "PATCHED", "UNSUPPORTED")]
        preselect = {i for i, r in enumerate(relevant) if r[3] == "UNPATCHED"}
    else:  # restore
        relevant = [r for r in rows if r[3] == "PATCHED"]
        preselect = set(range(len(relevant)))

    if not relevant:
        if action == "patch":
            print("\nNo installed targets to patch.\n")
        else:
            print("\nNothing to restore (no targets are currently patched).\n")
        return None, []

    option_lines = [f"{label:42s}  {state}" for _kind, label, _path, state in relevant]
    verb = action.upper()

    chosen_idx = _arrow_multi_select(
        header=f"\nSelect targets to {verb}:",
        options=option_lines,
        preselected=preselect,
        footer="(Up/Down move, Space toggle, A all/none, Enter confirm, q/Esc cancel)",
    )
    if not chosen_idx:
        print("\nCancelled (no targets selected).\n")
        return None, []

    print()
    print(f"About to {verb}:")
    for i in sorted(chosen_idx):
        _kind, label, _path, state = relevant[i]
        note = ""
        if action == "patch" and state == "PATCHED":
            note = "  (already patched - will be a no-op)"
        elif action == "restore" and state != "PATCHED":
            note = f"  (current state: {state})"
        print(f"  - {label}{note}")
    print()

    confirm_idx = _arrow_single_select(
        header="Continue?",
        options=["Yes, proceed", "No, cancel"],
        footer="(Up/Down + Enter, or q/Esc to cancel)",
    )
    if confirm_idx != 0:
        print("\nCancelled.\n")
        return None, []

    chosen = [(relevant[i][0], relevant[i][2]) for i in sorted(chosen_idx)]
    return action, chosen


def _execute(
    action: str,
    chosen: "list[tuple[str, str]]",
    skip_network_block: bool = False,
    premiere_path: Optional[str] = None,
) -> int:
    rc = 0
    _kill_premiere()

    for kind, path in chosen:
        try:
            if kind == "premiere":
                if action == "restore":
                    logger.info("attempting to restore Premiere Pro: %s", path)
                    restore(path)
                    logger.info("successfully restored Premiere Pro")
                else:
                    logger.info("attempting to patch Premiere Pro: %s", path)
                    patch(path)
                    logger.info("successfully patched Premiere Pro")
            elif kind == "headless":
                if action == "restore":
                    logger.info("attempting to restore PProHeadless: %s", path)
                    restore_headless(path)
                    logger.info("successfully restored PProHeadless")
                else:
                    logger.info("attempting to patch PProHeadless: %s", path)
                    patch_headless(path)
                    logger.info("successfully patched PProHeadless")
            elif kind == "jpeg":
                if action == "restore":
                    logger.info("attempting to restore jpeg_wrapper: %s", path)
                    restore_jpeg(path)
                    logger.info("successfully restored jpeg_wrapper")
                else:
                    logger.info("attempting to patch jpeg_wrapper: %s", path)
                    patch_jpeg(path)
                    logger.info("successfully patched jpeg_wrapper")
        except PatchError as e:
            logger.error("Target failed (%s): %s", path, e)
            rc = 1

    # Network protection & codec handling
    pr_exe = None
    hl_exe = None
    for k, p in chosen:
        if k == "premiere":
            pr_exe = p
        elif k == "headless":
            hl_exe = p
    if not pr_exe and premiere_path:
        pr_exe = premiere_path
    if not hl_exe and pr_exe:
        cand = Path(pr_exe).with_name("PProHeadless.exe")
        if cand.exists():
            hl_exe = str(cand)

    if action == "patch":
        setup_codec_tier2_directory(Path(pr_exe).parent if pr_exe else None)
        if not skip_network_block:
            logger.info("applying anti-popup protection (firewall & hosts)...")
            configure_firewall(pr_exe, hl_exe, enable=True)
            configure_hosts(enable=True)
            clear_license_cache()
            logger.info("anti-popup and codec protection active")
    elif action == "restore":
        if not skip_network_block:
            logger.info("reverting anti-popup protection...")
            configure_firewall(pr_exe, hl_exe, enable=False)
            configure_hosts(enable=False)
            logger.info("anti-popup protection removed")

    return rc


def _resolve_chosen_from_cli(targets_spec: str, premiere_path: Optional[str]) -> "list[tuple[str, str]]":
    targets = _parse_targets(targets_spec)
    chosen: list[tuple[str, str]] = []
    if "premiere" in targets and premiere_path is not None:
        chosen.append(("premiere", premiere_path))
    if "headless" in targets:
        for hp in locate_headless(premiere_path):
            chosen.append(("headless", hp))
    if "jpeg" in targets:
        for jp in locate_jpeg(premiere_path):
            chosen.append(("jpeg", jp))
    return chosen


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = _build_arg_parser().parse_args()

    _require_admin(skip=args.skip_admin)
    _enable_ansi()

    # Auto-locate Premiere Pro
    premiere_path: Optional[str] = None
    try:
        premiere_path = args.path or locate()
    except PatchError:
        premiere_path = None

    # Handle dedicated CLI commands directly
    if args.block_network:
        _kill_premiere()
        headless_paths = locate_headless(premiere_path)
        hl = headless_paths[0] if headless_paths else None
        configure_firewall(premiere_path, hl, enable=True)
        configure_hosts(enable=True)
        clear_license_cache()
        logger.info("Anti-popup protection successfully configured.")
        return 0

    if args.unblock_network:
        _kill_premiere()
        headless_paths = locate_headless(premiere_path)
        hl = headless_paths[0] if headless_paths else None
        configure_firewall(premiere_path, hl, enable=False)
        configure_hosts(enable=False)
        logger.info("Anti-popup protection successfully removed.")
        return 0

    if args.clean_cache:
        clear_license_cache()
        clear_media_cache()
        logger.info("License notification and media caches cleaned.")
        return 0

    if args.install_codecs:
        _kill_premiere()
        setup_codec_tier2_directory(Path(premiere_path).parent if premiere_path else None)
        logger.info("HEVC codec provisioning completed.")
        return 0

    # ---- explicit CLI mode (scripted / unattended) --------------------------
    if args.targets is not None or not sys.stdin.isatty():
        targets_spec = args.targets or "all"
        chosen = _resolve_chosen_from_cli(targets_spec, premiere_path)
        if not chosen:
            logger.info("nothing to do (no targets resolved)")
            return 0
        action = "restore" if args.restore else "patch"
        return _execute(action, chosen, skip_network_block=args.no_network_block, premiere_path=premiere_path)

    # ---- interactive flow ---------------------------------------------------
    if args.restore:
        rows = _build_target_rows(premiere_path)
        patched = [r for r in rows if r[3] == "PATCHED"]

        if not patched:
            logger.info("nothing to restore (no targets are currently patched)")
            return 0

        if len(patched) == 1:
            kind, label, path, _state = patched[0]
            print()
            print(f"Single patched install detected: {label}")
            print(f"  {path}")
            print()
            confirm_idx = _arrow_single_select(
                header=f"Restore {label} from .bak?",
                options=["Yes, restore", "No, cancel"],
                footer="(Up/Down + Enter, or q/Esc to cancel)",
            )
            if confirm_idx != 0:
                print("\nCancelled.\n")
                return 0
            return _execute("restore", [(kind, path)], skip_network_block=args.no_network_block, premiere_path=premiere_path)

        action, chosen = interactive_menu(premiere_path, action_filter="restore")
    else:
        action, chosen = interactive_menu(premiere_path, action_filter=None)

    if action is None:
        return 0

    if action == "install_codecs":
        _kill_premiere()
        setup_codec_tier2_directory(Path(premiere_path).parent if premiere_path else None)
        print("\nHEVC codec provisioning completed.\n")
        return 0

    if action == "block_network":
        _kill_premiere()
        headless_paths = locate_headless(premiere_path)
        hl = headless_paths[0] if headless_paths else None
        configure_firewall(premiere_path, hl, enable=True)
        configure_hosts(enable=True)
        clear_license_cache()
        print("\nAnti-popup protection applied successfully.\n")
        return 0

    if action == "unblock_network":
        _kill_premiere()
        headless_paths = locate_headless(premiere_path)
        hl = headless_paths[0] if headless_paths else None
        configure_firewall(premiere_path, hl, enable=False)
        configure_hosts(enable=False)
        print("\nAnti-popup protection removed.\n")
        return 0

    if action == "clean_cache":
        clear_license_cache()
        clear_media_cache()
        print("\nLicense notification and media caches cleaned successfully.\n")
        return 0

    if not chosen:
        return 0

    return _execute(action, chosen, skip_network_block=args.no_network_block, premiere_path=premiere_path)


if __name__ == "__main__":
    sys.exit(main())
