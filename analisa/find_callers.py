import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

targets = [0x1AD3D290, 0x1AD3FAF0, 0x1AD3FC60, 0x1AD3FCA0]

# Search for rel32 calls to each target
# call rel32 is E8 disp32, where disp32 = target - (addr + 5)
import struct

for target in targets:
    print(f"\n==========================================")
    print(f"Callers of 0x{target:08X}:")
    callers = []
    # Search in executable code (say from 0 to 0x30000000)
    for addr in range(0, min(len(data)-5, 0x30000000)):
        if data[addr] == 0xE8:
            disp = struct.unpack_from('<i', data, addr+1)[0]
            dest = (addr + 5 + disp) & 0xFFFFFFFF
            if dest == target:
                callers.append(addr)
    print(f"Found {len(callers)} call sites: {[hex(c) for c in callers]}")
    for c in callers[:5]:
        print(f"--- Context at call site 0x{c:08X} ---")
        chunk = data[c-20:c+30]
        for insn in md.disasm(chunk, c-20):
            print(f"0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
