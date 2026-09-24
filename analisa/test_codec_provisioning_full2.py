import os
import shutil
from pathlib import Path

def test_provisioning():
    tier2_base = Path(r"C:\Users\Public\Documents\AdobeInstalledCodecsTier2")
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
    
    known_sources = [
        tier2_base / "14.3.0.25617",
        tier2_base / "4.0",
        tier2_base / "4.3",
        tier2_base / "4.3.4",
        tier2_base / "2.0",
        Path(r"D:\PR INSTALL\fix\Adobe Premiere Pro 2026"),
    ]
    
    dec_source = None
    enc_source = None
    for loc in known_sources:
        cand_dec = loc / "mc_dec_hevc.dll"
        cand_enc = loc / "mc_enc_hevc.dll"
        if not dec_source and cand_dec.exists() and cand_dec.stat().st_size > 1000000:
            dec_source = cand_dec
        if not enc_source and cand_enc.exists() and cand_enc.stat().st_size > 1000000:
            enc_source = cand_enc
            
    print(f"Dec source: {dec_source}")
    print(f"Enc source: {enc_source}")
    assert dec_source and enc_source, "Codecs not found!"
    
    for ver in target_versions:
        target_dir = tier2_base / ver
        target_dir.mkdir(parents=True, exist_ok=True)
        if not (target_dir / "mc_dec_hevc.dll").exists():
            shutil.copy2(dec_source, target_dir / "mc_dec_hevc.dll")
        if not (target_dir / "mc_enc_hevc.dll").exists():
            shutil.copy2(enc_source, target_dir / "mc_enc_hevc.dll")
        for dat_name in ("mc_dec_hevc.dat", "mc_enc_hevc.dat"):
            dat_path = target_dir / dat_name
            if not dat_path.exists():
                dat_path.touch()
        print(f"Verified {target_dir}:")
        print(f"  files: {[f.name for f in target_dir.iterdir()]}")

if __name__ == "__main__":
    test_provisioning()
    print("Provisioning test passed successfully!")
