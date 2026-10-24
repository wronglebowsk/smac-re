
import struct
p=2124624
f=open(f"/proc/{p}/mem","rb",0)
def rd(a,n):
    f.seek(a); return f.read(n)
G=[0x985b10,0x985aec,0x985b30,0x92a27c,0x92a290,0x92a294,0x92ada8,0x8f0c34,0x8f0c38,0x8f0c48,0x8f0c4c,0x8f0c6c,0x8f0c70,0x8f0c2c,0x8f0d38,0x8f0d64,0x985ba8,0x985bac,0x985bb0,0x985af0,0x92a378,0x92a37c,0x92a394,0x692184,0x985ae8]
out=open('evidence/m53l_globals.txt','w')
vals={}
for a in G:
    v=struct.unpack('<I',rd(a,4))[0]; vals[a]=v
    out.write(f"0x{a:x} = {v} (signed {v-(1<<32 if v>0x80000000 else 0)})\n")
era=vals[0x985aec]
out.write(f"\nera idx 0x985aec = {era}\n")
ptrs=[struct.unpack('<I',rd(0x68cbb8+i*4,4))[0] for i in range(16)]
out.write("era table ptrs @0x68cbb8:\n")
seen={}
for i,q in enumerate(ptrs):
    out.write(f"  [{i}] 0x{q:08x}")
    if q and 0x400000<q<0xc00000 and q not in seen:
        d=struct.unpack('<12i',rd(q,48))
        seen[q]=d
        out.write(f"  -> {list(d)}")
    elif q in seen:
        out.write(f"  -> (same as above) {list(seen[q])}")
    out.write("\n")
out.write(f"\nmask dword = {vals[0x985b10]:#x} lo_byte={vals[0x985b10]&0xff:#x} hi_byte={(vals[0x985b10]>>8)&0xff:#x}\n")
out.close()
print(open('evidence/m53l_globals.txt').read()[:1900])
