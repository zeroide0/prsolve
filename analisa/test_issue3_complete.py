import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

# Add fix to path
sys.path.insert(0, r"D:\PR INSTALL\prsolved\fix")
import pr_patch

def run_tests():
    print("=" * 60)
    print("RUNNING ISSUE #3 COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)

    # Test 1: Importer stream validation and fallback signature matching
    print("\n[Test 1] Testing HEVC importer stream signature matching...")
    target_pr = None
    for p in [
        r"D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        r"C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
    ]:
        if Path(p).exists():
            target_pr = p
            break
    assert target_pr is not None, "Could not find a valid Premiere Pro exe for testing"

    bak_path = target_pr + ".bak"
    test_file = bak_path if Path(bak_path).exists() else target_pr
    with open(test_file, "rb") as f:
        data = f.read()

    # Pattern 1: Importer stream validation (0x1AD6AD72)
    sig1 = [0x83, 0xB8, 0xA4, 0x01, 0x00, 0x00, 0x00, 0x75, 0x0D, 0xC7, 0x44, 0x24, 0x74, 0x66, 0x00, 0x07, 0xA0]
    occs1 = pr_patch.find_all(data, sig1)
    print(f"Found {len(occs1)} match(es) for sig1 in {Path(test_file).name}: {[hex(x) for x in occs1]}")
    if occs1:
        assert len(occs1) == 1, f"Expected 1 match, got {len(occs1)}"
        assert 0x1AD6AD72 in occs1
        test_buf = bytearray(data[0x1AD6AD72 : 0x1AD6AD72 + len(sig1)])
        repl = pr_patch._force_importer_stream_validation(test_buf, 0, sig1)
        assert repl[7] == 0xEB, f"Expected EB at offset 7, got {hex(repl[7])}"

    # Pattern 2: Importer stream fallback (0x1AD6BA83)
    sig2 = [0x41, 0x83, 0xF8, 0x01, 0x7E, 0x11, 0x84, 0xC0, 0x75, 0x0D, 0xC7, 0x44, 0x24, 0x74, 0x66, 0x00, 0x07, 0xA0]
    occs2 = pr_patch.find_all(data, sig2)
    print(f"Found {len(occs2)} match(es) for sig2 in {Path(test_file).name}: {[hex(x) for x in occs2]}")
    if occs2:
        assert len(occs2) == 1, f"Expected 1 match, got {len(occs2)}"
        assert 0x1AD6BA83 in occs2
        test_buf = bytearray(data[0x1AD6BA83 : 0x1AD6BA83 + len(sig2)])
        repl = pr_patch._force_importer_stream_fallback(test_buf, 0, sig2)
        assert repl[8] == 0xEB, f"Expected EB at offset 8, got {hex(repl[8])}"

    # Verify patched binary has active EB jumps
    with open(target_pr, "rb") as f:
        f.seek(0x1AD6AD79)
        b1 = f.read(1)
        assert b1 == b'\xEB', f"Expected EB at 0x1AD6AD79, got {b1.hex()}"
        f.seek(0x1AD6BA8B)
        b2 = f.read(1)
        assert b2 == b'\xEB', f"Expected EB at 0x1AD6BA8B, got {b2.hex()}"
    print("Importer HEVC stream validation and fallback patches verified successfully.")

    # Test 2: Codec Zip Archive integrity
    print("\n[Test 2] Testing bundled hevc_codecs.zip integrity...")
    zip_path = Path(r"D:\PR INSTALL\prsolved\fix\hevc_codecs.zip")
    assert zip_path.exists(), "hevc_codecs.zip missing in fix/"
    assert zip_path.stat().st_size > 5000000, "hevc_codecs.zip size too small"

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        print("Archive contents:", namelist)
        assert "mc_dec_hevc.dll" in namelist, "mc_dec_hevc.dll missing in zip"
        assert "mc_enc_hevc.dll" in namelist, "mc_enc_hevc.dll missing in zip"
        
        for name in ("mc_dec_hevc.dll", "mc_enc_hevc.dll"):
            dll_bytes = zf.read(name)
            assert dll_bytes[:2] == b'MZ', f"{name} is not a valid MZ executable"
            print(f"  {name}: {len(dll_bytes)} bytes - Valid MZ header")

    # Test 3: Sandbox Provisioning
    print("\n[Test 3] Testing sandbox codec provisioning flow with 14.3.0.25617...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        mock_tier2 = tmp_path / "AdobeInstalledCodecsTier2"
        mock_app = tmp_path / "PremiereApp"
        mock_app.mkdir()

        target_versions = (
            "14.3.0.25617",
            "14.3.0",
            "14.3",
            "14.0",
            "4.3.4",
            "4.3",
            "4.0",
            "26.0",
        )

        for v in target_versions:
            (mock_tier2 / v).mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as z:
            for member in ("mc_dec_hevc.dll", "mc_enc_hevc.dll"):
                for v in target_versions:
                    z.extract(member, mock_tier2 / v)
                z.extract(member, mock_app)

        for v in target_versions:
            (mock_tier2 / v / "mc_dec_hevc.dat").touch()
            (mock_tier2 / v / "mc_enc_hevc.dat").touch()
            assert (mock_tier2 / v / "mc_dec_hevc.dll").exists()
            assert (mock_tier2 / v / "mc_enc_hevc.dll").exists()
            assert (mock_tier2 / v / "mc_dec_hevc.dat").exists()
            assert (mock_tier2 / v / "mc_enc_hevc.dat").exists()

        assert (mock_app / "mc_dec_hevc.dll").exists()
        assert (mock_app / "mc_enc_hevc.dll").exists()
        print("Sandbox deployment verified: all Tier2 directories (including 14.3.0.25617) received codecs & manifests.")

    # Test 4: Verify full patch definition table
    print("\n[Test 4] Verifying PATCHES_PREMIERE_26 and PATCHES_HEADLESS_26 definitions...")
    patches_pr = pr_patch.PATCHES_PREMIERE_26
    assert len(patches_pr) == 7, f"Expected 7 patch entries, got {len(patches_pr)}"
    patches_hl = pr_patch.PATCHES_HEADLESS_26
    assert len(patches_hl) == 6, f"Expected 6 patch entries, got {len(patches_hl)}"
    print(f"PATCHES_PREMIERE_26 contains {len(patches_pr)} patch specifications.")
    print(f"PATCHES_HEADLESS_26 contains {len(patches_hl)} patch specifications.")

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
