#!/usr/bin/env python3
"""SMAC .flc decoder v3 — exe-faithful (terran.exe):
  FUN_0062ad73  open: 128-B header, magic u16@+4==0xAF12, W=u16@+8, H=u16@+10
                flag|2 set when the caller passes loop!=0 (all shipped files)
  FUN_0062bdeb  chunk dispatch: u32 size + u16 type; 0xF1FA=container
                (u16 subchunk count at +6, recurse); 4/0xb/0xc/0x12 no-op;
                7->FUN_0062c36f, 0xf->FUN_0062c06c(8-bit rows), 0x10->raw,
                0xd->clear; unknown -> skip size-6.
  8-bit rows (FUN_0062b3da/c06c): per row: 1 leading byte (discarded), then
     while remaining>0: s8 c; c>=1 -> RLE: next byte = index, fill c;
                        c<=0 -> literal: copy -c bytes.  VERIFIED byte-exact
                        on turn.flc frame0 (281/281 consumed, coherent image).
  type-7 delta (FUN_0062c36f): u16 rows; per row: skip-words while
     (u16&0xC000)==0xC000 advance (u16&0x3FFF) rows; u16 npackets
     (if &0x8000: transparency byte = low+ref, then re-read npackets);
     packets: u8 adv (skip adv px in cur AND prev); s8 val:
       val>=1 -> literal: read 2*val bytes, each +ref; if byte==transparency
                  copy that byte from prev buffer;
       val<0  -> read u16 color word; color = (hi+ref, lo+ref); run count=-val;
                  per pixel: byte equal to transparency keeps prev byte;
       val==0 -> no-op (keeps last color).
Palette: programs/palette.pcx (256 RGB24).
Usage: python3 flc_decode3.py <file.flc> <outdir> [pal.pcx]"""
import struct, sys, os
from PIL import Image

class R:
    def __init__(s,d,p=0): s.d,s.p=d,p
    def read(s,n):
        b=s.d[s.p:s.p+n]
        if len(b)!=n: raise EOFError(f'{n}@{s.p}')
        s.p+=n; return b
    def u8(s): return s.read(1)[0]
    def s8(s): return struct.unpack('<b',s.read(1))[0]
    def u16(s): return struct.unpack('<H',s.read(2))[0]
    def u32(s): return struct.unpack('<I',s.read(4))[0]

def rows8(r,W,H,fb,stride,ref=0,trans=None,prev=None):
    for y in range(H):
        r.u8()
        base=y*stride; x=0; rem=W
        while rem>0:
            c=r.s8()
            if c>=1:
                v=r.u8()
                if ref: v=(v+ref)&0xFF
                for i in range(c):
                    if x<W: fb[base+x+i]=v
                x+=c; rem-=c
            else:
                n=-c; lit=r.read(n)
                for i in range(n):
                    b=lit[i]
                    if ref: b=(b+ref)&0xFF
                    if x<W: fb[base+x+i]=b
                x+=n; rem-=n

def delta7(r,W,H,fb,stride,prev,ref=0,trans=0):
    """FUN_0062c36f (delta, flag|2 table), 8-bit indexed surface.
    VERIFIED byte-exact on turn.flc frame1 (174/174 payload bytes).
    Semantics: u16 rows; per row: skip-words while (u16&0xC000)==0xC000
    advance -(s16) rows; u16 npackets (if &0x8000 handle transparency byte
    then re-read npackets); packets: u8 adv (skip adv px); s8 val:
      val>=1 -> literal: read 2*val bytes, each +ref, transparency byte
                 copies that pixel from the previous frame;
      val<0  -> RLE: read u16 word (lo,hi each +ref); write 2*(-val) px
                 alternating lo,hi; bytes equal to transparency copy prev;
      val==0 -> no output (keeps last color)."""
    rows=r.u16(); y=0
    for _ in range(rows):
        if y>=H: break
        while True:
            v=r.u16()
            if (v & 0xC000)==0xC000:
                y += -struct.unpack('<h', struct.pack('<H', v))[0]
                if y>=H: break
                continue
            break
        npkt=v & 0xFFFF
        if v & 0x8000:
            tb=((v & 0xFF)+ref)&0xFF
            base=y*stride
            if base < len(fb): fb[base]=tb
            npkt=r.u16() & 0xFFFF
        base=y*stride
        if base>=len(fb):
            for _ in range(npkt):
                r.u8(); val=r.s8()
                if val>=1: r.read(2*val)
                elif val<0: r.u16()
            y+=1; continue
        x=0
        for _ in range(npkt):
            adv=r.u8(); x+=adv
            val=r.s8()
            if val>=1:
                n=2*val
                lit=r.read(n)
                for i in range(n):
                    b=lit[i]
                    if ref: b=(b+ref)&0xFF
                    px=x+i
                    if px>=W: break
                    if trans is not None and b==trans and prev:
                        fb[base+px]=prev[base+px]
                    else: fb[base+px]=b
                x+=n
            elif val<0:
                cw=r.u16(); n=2*(-val)
                hi=((cw>>8)+ref)&0xFF; lo=((cw&0xFF)+ref)&0xFF
                for i in range(n):
                    px=x+i
                    if px>=W: break
                    b = lo if (i%2==0) else hi
                    if prev and trans is not None and b==trans:
                        fb[base+px]=prev[base+px]
                    else: fb[base+px]=b
                x+=n
        y+=1

def load_palette(p):
    img=Image.open(p).convert('P'); pal=img.getpalette()
    return [tuple(pal[3*i:3*i+3]) for i in range(256)]

def decode(path, bpp=1, trans=None, ref=0, pal0=None):
    d=open(path,'rb').read()
    w=[struct.unpack('<H',d[i:i+2])[0] for i in range(0,128,2)]
    assert w[2]==0xAF12, f'bad magic {w[2]:#x}'
    W,H=w[4],w[5]; stride=((W+3)>>2)<<2
    r=R(d,128); fb=[0]*(H*stride); frames=[]
    pal=list(pal0) if pal0 else [(0,0,0)]*256
    while r.p+16<=len(d):
        fpos=r.p
        size=r.u32(); typ=r.u16()
        if typ!=0xF1FA or size<16:
            print(f'stop @ {fpos}: size={size} typ={typ:#x}'); break
        subcnt=r.u16(); r.read(8); rend=fpos+size
        def leaf(r):
            nonlocal pal
            sz=r.u32(); t=r.u16()
            if sz<6: raise ValueError('chunk')
            cend=r.p+sz-6
            if t==0xF1FA:
                n=r.u16()
                for _ in range(n): leaf(r)
            elif t==0x0004:
                # COLOR256_24 (SMAC variant): u32 hdr, then 256 RGB24 triplets.
                # Index 9 = (255,0,255) transparency marker; indices 10..
                # track palette.pcx[0..245] with per-file deviations.
                pay=r.read(sz-6)
                trip=[tuple(pay[4+3*i:4+3*i+3]) for i in range((len(pay)-4)//3)]
                newpal=list(pal)
                for j,c in enumerate(trip):
                    if j<256: newpal[j]=c
                pal=newpal
            elif t==0x000F: rows8(r,W,H,fb,stride)
            elif t==0x0010:
                for yy in range(H):
                    row=r.read(W)
                    for i in range(W): fb[yy*stride+i]=row[i]
            elif t==0x000D: fb[:]=[0]*(H*stride)
            elif t==0x0007: delta7(r,W,H,fb,stride,prevbuf,ref=ref,trans=trans)
            r.p=cend
        prevbuf=list(fb)
        for _ in range(subcnt if subcnt else 1):
            if r.p+6>rend: break
            leaf(r)
        r.p=rend
        frames.append((list(fb),list(pal)))
    return W,H,stride,frames

def render(W,H,stride,frames,outdir,maxf=40):
    os.makedirs(outdir,exist_ok=True)
    for i,(px,pal) in enumerate(frames[:maxf]):
        img=Image.new('RGB',(W,H)); p=img.load()
        for y in range(H):
            for x in range(W): p[x,y]=pal[px[y*stride+x]]
        img.save(f'{outdir}/frame_{i:02d}.png')
    return min(len(frames),maxf)

if __name__=='__main__':
    path=sys.argv[1]; outdir=sys.argv[2]
    bpp=int(sys.argv[3]) if len(sys.argv)>3 else 1
    trans=None if len(sys.argv)<5 or sys.argv[4]=='none' else int(sys.argv[4])
    pal0=load_palette(sys.argv[5] if len(sys.argv)>5 else 'programs/palette.pcx')
    W,H,stride,fr=decode(path,bpp=bpp,trans=trans,pal0=pal0)
    n=render(W,H,stride,fr,outdir)
    print(f'{path}: {W}x{H} stride={stride} bpp={bpp} trans={trans}, {len(fr)} frames, {n} rendered -> {outdir}')
