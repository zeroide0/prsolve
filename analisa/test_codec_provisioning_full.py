import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path

def test_full_provisioning():
    test_sandbox = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox\full_test")
    if test_sandbox.exists():
        shutil.rmtree(test_sandbox)
    test_sandbox.mkdir(parents=True, exist_ok=True)

    tier2_base = test_sandbox / "AdobeInstalledCodecsTier2"
    app_dir = test_sandbox / "Premiere_App"
    app_dir.mkdir(parents=True, exist_ok=True)

    zip_local = Path(r"D:\PR INSTALL\prsolved\fix\hevc_codecs.zip")
    assert zip_local.exists()

    cache_dir = test_sandbox / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_local, 'r') as zf:
        zf.extract("mc_dec_hevc.dll", cache_dir)
        zf.extract("mc_enc_hevc.dll", cache_dir)

    dec_src = cache_dir / "mc_dec_hevc.dll"
    enc_src = cache_dir / "mc_enc_hevc.dll"
    assert dec_src.exists() and enc_src.exists()

    for ver in ("4.0", "4.3", "4.3.4"):
        target_dir = tier2_base / ver
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dec_src, target_dir / "mc_dec_hevc.dll")
        shutil.copy2(enc_src, target_dir / "mc_enc_hevc.dll")
        assert (target_dir / "mc_dec_hevc.dll").stat().st_size == 10292784
        assert (target_dir / "mc_enc_hevc.dll").stat().st_size == 11689008

    shutil.copy2(dec_src, app_dir / "mc_dec_hevc.dll")
    shutil.copy2(enc_src, app_dir / "mc_enc_hevc.dll")
    assert (app_dir / "mc_dec_hevc.dll").stat().st_size == 10292784

    print("FULL PROVISIONING TEST SUCCESSFUL!")

if __name__ == "__main__":
    test_full_provisioning()
