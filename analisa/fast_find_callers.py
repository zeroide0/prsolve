import struct
import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

targets = {
    0x1AD3D290: "Prompt_1",
    0x1AD3FAF0: "Prompt_2",
    0x1AD3FC60: "Prompt_3",
    0x1AD3FCA0: "Prompt_4",
    0x1AD423B0: "CodecVal_1",
    0x1AD42500: "CodecVal_2",
}

pos = 0
found = {}
while True:
    pos = data.find(b'\xE8', pos)
    if pos == -1 or pos >= len(data) - 5:
        break
    disp = struct.unpack_from('<i', data, pos + 1)[0]
    dest = (pos + 5 + disp) & 0xFFFFFFFF
    if dest in targets:
        name = targets[dest]
        found.setdefault(name, []).append(pos)
    pos += 1

for name, callers in found.items():
    print(f"=== Callers of {name} (total {len(callers)}) ===")
    for c in callers[:5]:
        print(f"Call at 0x{c:08X}:")
        chunk = data[c-25:c+25]
        for insn in md.disasm(chunk, c-25):
            mark = "==>" if insn.address == c else "   "
            print(f"{mark} 0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
        print()
