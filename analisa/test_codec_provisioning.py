import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path

def test_provisioning():
    # Setup test sandbox paths
    test_dir = Path(r"D:\PR INSTALL\prsolved\analisa\sandbox\codec_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    tier2_mock = test_dir / "AdobeInstalledCodecsTier2"
    pr_mock = test_dir / "Premiere_App"
    pr_mock.mkdir(parents=True, exist_ok=True)

    zip_path = Path(r"D:\PR INSTALL\prsolved\fix\hevc_codecs.zip")
    assert zip_path.exists(), "hevc_codecs.zip must exist in fix/"

    # Test extracting from zip
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        print("Zip entries:", names)
        assert "mc_dec_hevc.dll" in names
        assert "mc_enc_hevc.dll" in names

        for target_ver in ("4.0", "4.3", "4.3.4"):
            vdir = tier2_mock / target_ver
            vdir.mkdir(parents=True, exist_ok=True)
            for name in ("mc_dec_hevc.dll", "mc_enc_hevc.dll"):
                zf.extract(name, vdir)
                assert (vdir / name).exists()
                print(f"Successfully deployed {name} to {vdir}")

        for name in ("mc_dec_hevc.dll", "mc_enc_hevc.dll"):
            zf.extract(name, pr_mock)
            assert (pr_mock / name).exists()
            print(f"Successfully deployed {name} to {pr_mock}")

    print("ALL CODEC PROVISIONING TESTS PASSED!")

if __name__ == "__main__":
    test_provisioning()
