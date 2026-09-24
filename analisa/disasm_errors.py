import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

matches = [0x1ad5859e, 0x1ad67f88, 0x1ad6ad7f, 0x1ad6b424, 0x1ad6ba91, 0x1ae1c3a5]

for m in matches:
    print(f"==================================================")
    print(f"Context around 0x{m:08X}:")
    chunk = data[m-30:m+40]
    for insn in md.disasm(chunk, m-30):
        mark = "==>" if insn.address == m else "   "
        print(f"{mark} 0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
