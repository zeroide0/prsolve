import capstone

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

exe = r'D:\PR INSTALL\fix\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe.bak'
with open(exe, 'rb') as f:
    data = f.read()

# Let's inspect string references or data
def read_string(offset):
    s = []
    while offset < len(data) and data[offset] != 0:
        s.append(chr(data[offset]))
        offset += 1
    return ''.join(s)

# At 0x1AD3D29A: rip = 0x1AD3D2A1, disp = 0xfe08f57
ptr1 = 0x1AD3D2A1 + 0xfe08f57
print(f"String/Data at 0x{ptr1:X}:")
# It's a pointer (qword ptr)
import struct
val1 = struct.unpack_from('<Q', data, ptr1)[0]
print(f"val1 = 0x{val1:X}")

# Let's disassemble the full function at 0x1AD423B0 (up to 200 bytes)
print("\n=== Full function 0x1AD423B0 ===")
for insn in md.disasm(data[0x1AD423B0:0x1AD423B0+250], 0x1AD423B0):
    print(f"0x{insn.address:08X}:  {insn.mnemonic:8s} {insn.op_str}")
