import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

print("\n=== Full function 0x1AD42500 ===")
for insn in md.disasm(data[0x1AD42500:0x1AD42500+150], 0x1AD42500):
    print(f"0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
    if insn.mnemonic == 'ret':
        break
