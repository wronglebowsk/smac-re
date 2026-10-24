
import struct, subprocess, os
pid=subprocess.check_output(["pgrep","-x","terran.exe"]).decode().split()[0]
f=open("/proc/%s/mem"%pid,"rb")
BASES=0x95da10; STRIDE=0x130
def rd(a,n):
    f.seek(a); return f.read(n)
out=[]
for i in range(76):
    b=BASES+i*STRIDE
    rec=rd(b,0xd4)
    x,y=struct.unpack_from("<HH",rec,0); fac=rec[4]; pop=rec[6]
    d30=struct.unpack_from("<I",rec,0x30)[0]; d34=struct.unpack_from("<I",rec,0x34)[0]
    d78=struct.unpack_from("<I",rec,0x78)[0]; c7c=struct.unpack_from("<i",rec,0x7c)[0]
    c80=struct.unpack_from("<i",rec,0x80)[0]; nib=struct.unpack_from("<II",rec,0x84)
    fac_bm=struct.unpack_from("<Q",rec,0x8c)[0]&((1<<40)-1)
    vec=struct.unpack_from("<4i",rec,0xbc)
    out.append((i,fac,pop,hex(d30),hex(d34),hex(d78),c7c,c80,[hex((nib[0]>>(k*4))&0xF) for k in range(8)]+[hex((nib[1]>>(k*4))&0xF) for k in range(8)],hex(fac_bm),vec))
for r in out:
    print("idx %2d fac %d pop %d d30 %s d34 %s d78 %s c7c %3d c80 %2d nib %s fac %s vec %s"%r)
# globals
for g in (0x8f0c68,0x8f0d30,0x8f0cc8,0x68cbb0,0x8f0d60,0x92a27c,0x92a2a4,0x92a2cc,0x92a394,0x985b10,0x985b48,0x985bc0,0x985ba8,0x985db8,0x985dc4,0x91c628,0x985afc,0x926bd8):
    print(hex(g), struct.unpack("<i",rd(g,4))[0])
f.close()
