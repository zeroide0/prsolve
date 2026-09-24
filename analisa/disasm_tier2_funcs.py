import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    f.seek(0x1AD3FC50)
    data = f.read(0x400)

for insn in md.disasm(data, 0x1AD3FC50):
    print(f"0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
