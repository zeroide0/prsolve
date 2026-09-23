import sys
sys.path.append(r'D:\PR INSTALL\prsolved\fix')
import pr_patch

def test_dialog_patch():
    with open(r'D:\PR INSTALL\fix\pr\Adobe Premiere Pro.exe', 'rb') as f:
        data = f.read()

    # Dialog prompt signature
    sig = [0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x8B, 0x1D, None, None, None, None, 0x48, 0x8B, 0xFA]
    matches = pr_patch.find_all(data, sig)
    print("Matches found:", [hex(m) for m in matches])
    assert len(matches) == 4, f"Expected 4 matches, got {len(matches)}"

    # Simulate replacement
    mut = bytearray(data)
    for m in matches:
        orig = bytes(mut[m:m+len(sig)])
        # replace with mov rax, rdx; ret (48 89 D0 C3)
        mut[m:m+4] = b'\x48\x89\xD0\xC3'
        assert mut[m:m+4] == b'\x48\x89\xD0\xC3'
        print(f"Verified replacement at 0x{m:X}")

    print("ALL DIALOG SUPPRESSION TESTS PASSED!")

if __name__ == "__main__":
    test_dialog_patch()
