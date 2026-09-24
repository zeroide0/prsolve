import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

addresses = [
    0x1ad423b0, 0x1ad42500,
    0x1ad3d290, 0x1ad3faf0, 0x1ad3fc60, 0x1ad3fca0
]

for addr in addresses:
    print(f"=== Disassembly at file offset 0x{addr:08X} ===")
    chunk = data[addr:addr+64]
    for insn in md.disasm(chunk, addr):
        print(f"0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
        if insn.mnemonic in ('ret', 'jmp') and insn.address > addr + 10:
            break
    print()
