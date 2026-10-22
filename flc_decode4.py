#!/usr/bin/env python3
"""SMAC .flc decoder v4 — fully exe-verified against terran.exe FLIC player.

Container (FUN_0062ad73 + FUN_0062bdeb):
  128-B header: magic u16@+4 == 0xAF12, W=u16@+8, H=u16@+10.
  Data @128: chunk = u32 LE size (incl 6-B hdr) + u16 type.
    0xF1FA frame container: u16 subchunk-count @+6, 16-B hdr total.
    other top-level (e.g. 0xf100, 2780-B Autodesk creator extension in
    the K:\ART\FROMJ~1 batch) -> skip by size (exe: unknown -> skip).
  After each chunk the exe seeks to chunk_start+size, so handler byte
  reads that overrun/underrun don't desync the stream.

Leaf chunk handlers (flag|2 / loop variant = the trans-aware table,
which is what in-game players use; FUN_00440290(9) sets trans=9,
ref(+0x5a4)=0 default):
  0xF1FA  recurse (u16 count @+6)
  0x4     COLOR256_24: u32 hdr, 256 RGB24 triplets -> full palette
          (index 9 = (255,0,255) magenta = transparency, Autodesk conv.)
  0xb/0xc/0x12  no-op stubs in exe dispatch -> skip
  0xd     clear buffer (FUN_0062b?)
  0xf     8-B brun (FUN_0062c06c): per row: 1 leading byte DISCARDED;
            while rem>0: s8 v;
              v<=0: literal n=-v: each byte (+ref): ==trans -> prev px;
              v>=1: RLE: next byte c (+ref): ==trans -> copy run from
                    prev row, else memset v px.
  0x10    raw rows (FUN_0062bc1d): H rows x W bytes (+ref, no trans);
          chunk size may be 1 B short of H*W (believe.flc) — trust rows*W,
          dispatcher re-syncs.
  0x7     16-B delta small-brun (FUN_0062c36f): u16 nrows; per row:
            skip-words while (u16&0xC000)==0xC000: advance -(s16) rows
            (cur AND prev);
            u16 npkt; if npkt&0x8000: tb=(lo+ref): cur_row[W] =
              (tb==trans ? prev_row[W] : tb); re-read npkt;
            packets: u8 adv (cur+=adv, prev+=adv px); s8 val:
              val>=1: literal 2*val bytes, each (+ref): ==trans->prev px;
              val<0:  cw=u16, lo'=(lo+ref), hi'=(hi+ref), n=-val words:
                lo'==T and hi'==T : copy 2n bytes from prev row
                lo'==T only       : n pairs (hi', prev_odd_byte)
                hi'==T only       : n pairs (prev_even_byte, lo')
                neither           : n words alternating lo',hi'
              val==0: no-op (keeps last color).
          Rows listed = only rows delta touches; others carry prev frame.
  unknown -> skip (seek to end)

Surface: 8-B indexed, pitch = ((W+3)>>2)<<2 standalone (exe blits onto
game surface at (x,y) with that surface's pitch).

Usage: python3 flc_decode4.py <file.flc> <outdir> [--gif] [pal-base.pcx]
"""
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

TRANS_DEFAULT = 9   # set by FUN_00440290(9) in game players
REF = 0             # object+0x5a4, never nonzero in shipped corpus

def brun(r,W,H,fb,stride,prev,trans=TRANS_DEFAULT,ref=REF):
    """FUN_0062c06c: 8-B brun, trans-aware."""
    for y in range(H):
        r.u8()  # leading byte per row, discarded by exe
        base=y*stride; x=0; rem=W
        while rem>0:
            v=r.s8()
            if v<=0:
                n=-v; lit=r.read(n)
                for i in range(n):
                    b=lit[i]
                    if ref: b=(b+ref)&0xFF
                    if x+i<W:
                        fb[base+x+i] = prev[base+x+i] if b==trans else b
                x+=n; rem-=n
            else:
                c=r.u8()
                if ref: c=(c+ref)&0xFF
                if x<W:
                    if c==trans:
                        for i in range(min(v,W-x)): fb[base+x+i]=prev[base+x+i]
                    else:
                        for i in range(min(v,W-x)): fb[base+x+i]=c
                x+=v; rem-=v

def raw10(r,W,H,fb,stride,ref=REF):
    """FUN_0062bc1d: raw rows, H*W bytes (may overrun chunk size)."""
    for y in range(H):
        row=r.read(W); base=y*stride
        for i in range(W):
            b=row[i]
            fb[base+i]=(b+ref)&0xFF if ref else b

def clear(fb):
    fb[:]=[0]*len(fb)

def delta7(r,W,H,fb,stride,prev,trans=TRANS_DEFAULT,ref=REF):
    """FUN_0062c36f: 16-B delta small-brun (flag|2 table)."""
    nrows=r.u16(); y=0
    for _ in range(nrows):
        while True:
            v=r.u16()
            if (v&0xC000)==0xC000:
                y += -struct.unpack('<h',struct.pack('<H',v))[0]
                continue
            break
        if v&0x8000:
            tb=((v&0xFF)+ref)&0xFF
            if y<H:
                fb[y*stride+W] = prev[y*stride+W] if tb==trans else tb
            npkt=r.u16()
        else:
            npkt=v
        if y>=H:
            for _ in range(npkt):
                r.u8(); val=r.s8()
                if val>=1: r.read(2*val)
                elif val<0: r.u16()
            y+=1; continue
        base=y*stride; x=0
        for _ in range(npkt):
            adv=r.u8(); x+=adv
            val=r.s8()
            if val>=1:
                n=2*val; lit=r.read(n)
                for i in range(n):
                    b=lit[i]
                    if ref: b=(b+ref)&0xFF
                    px=x+i
                    if px>=W: break
                    fb[base+px] = prev[base+px] if b==trans else b
                x+=n
            elif val<0:
                cw=r.u16(); n=-val
                lo=((cw&0xFF)+ref)&0xFF; hi=(((cw>>8)+ref)&0xFF)
                tlo = lo==trans; thi = hi==trans
                if tlo and thi:
                    for i in range(2*n):
                        px=x+i
                        if px>=W: break
                        fb[base+px]=prev[base+px]
                elif tlo:
                    for i in range(n):
                        px=x+2*i
                        if px>=W: break
                        fb[base+px]=hi
                        if px+1<W: fb[base+px+1]=prev[base+px+1]
                elif thi:
                    for i in range(n):
                        px=x+2*i
                        if px>=W: break
                        fb[base+px]=prev[base+px]
                        if px+1<W: fb[base+px+1]=lo
                else:
                    for i in range(2*n):
                        px=x+i
                        if px>=W: break
                        fb[base+px]= lo if i%2==0 else hi
                x+=2*n
            # val==0: no-op, keeps last color
        y+=1

def load_palette(p):
    img=Image.open(p).convert('P'); pal=img.getpalette()
    return [tuple(pal[3*i:3*i+3]) for i in range(256)]

def decode(path, trans=TRANS_DEFAULT, pal0=None):
    d=open(path,'rb').read()
    w=[struct.unpack('<H',d[i:i+2])[0] for i in range(0,128,2)]
    assert w[2]==0xAF12, f'bad magic {w[2]:#x}'
    W,H=w[4],w[5]; stride=((W+3)>>2)<<2
    r=R(d,128); fb=[0]*(H*stride); frames=[]
    pal=list(pal0) if pal0 else [(0,0,0)]*256
    stats={'brun':0,'delta':0,'raw':0,'cmap':0,'noop':0,'clear':0}
    def leaf(r,rend):
        nonlocal pal
        sz=r.u32(); t=r.u16()
        if sz<6: raise ValueError('chunk')
        cend=r.p+sz-6
        if t==0xF1FA:
            n=r.u16()
            for _ in range(n): leaf(r,cend)
        elif t==0x0004:
            pay=r.read(sz-6)
            trip=[tuple(pay[4+3*i:4+3*i+3]) for i in range((len(pay)-4)//3)]
            newpal=list(pal)
            for j,c in enumerate(trip):
                if j<256: newpal[j]=c
            pal=newpal; stats['cmap']+=1
        elif t==0x000F: brun(r,W,H,fb,stride,prevbuf,trans=trans); stats['brun']+=1
        elif t==0x0010: raw10(r,W,H,fb,stride); stats['raw']+=1
        elif t==0x000D: clear(fb); stats['clear']+=1
        elif t==0x0007: delta7(r,W,H,fb,stride,prevbuf,trans=trans); stats['delta']+=1
        else: stats['noop']+=1
        r.p=cend
    while r.p+16<=len(d):
        fpos=r.p
        size=r.u32(); typ=r.u16()
        if typ!=0xF1FA or size<16:
            if size<6: break
            r.p=fpos+size          # extension block: exe skips unknown by size
            continue
        subcnt=r.u16(); r.read(8); rend=fpos+size
        prevbuf=list(fb)
        for _ in range(subcnt if subcnt else 1):
            if r.p+6>rend: break
            leaf(r,rend)
        r.p=rend
        frames.append((list(fb),list(pal)))
    return W,H,stride,frames,stats

def render(W,H,stride,frames,outdir,maxf=1000):
    os.makedirs(outdir,exist_ok=True)
    imgs=[]
    for i,(px,pal) in enumerate(frames[:maxf]):
        img=Image.new('P',(W,H))
        img.putpalette([c for t in pal for c in t])
        img.putdata([px[y*stride+x] for y in range(H) for x in range(W)])
        img.save(f'{outdir}/frame_{i:02d}.png')
        imgs.append(img.convert('RGB'))
    return imgs

def contact_sheet(W,H,stride,frames,out,maxf=40):
    frames=frames[:maxf]
    n=len(frames); cols=min(n,8); rows=(n+cols-1)//cols
    cw=(W+2)*cols; ch=(H+2)*rows
    sheet=Image.new('RGB',(cw,ch),(40,40,40))
    for i,(px,pal) in enumerate(frames):
        img=Image.new('P',(W,H)); img.putpalette([c for t in pal for c in t])
        img.putdata([px[y*stride+x] for y in range(H) for x in range(W)])
        sheet.paste(img.convert('RGB'),((i%cols)*(W+2)+1,(i//cols)*(H+2)+1))
    sheet.save(out)

if __name__=='__main__':
    path=sys.argv[1]; outdir=sys.argv[2]
    args=sys.argv[3:]
    gif='--gif' in args
    pals=[a for a in args if not a.startswith('--')]
    pal0=load_palette(pals[0]) if pals else load_palette('programs/palette.pcx')
    W,H,stride,fr,stats=decode(path,pal0=pal0)
    imgs=render(W,H,stride,fr,outdir)
    contact_sheet(W,H,stride,fr,f'{outdir}/sheet.png')
    if gif and imgs:
        imgs[0].save(f'{outdir}/anim.gif',save_all=True,
                     append_images=imgs[1:],duration=100,loop=0)
    print(f'{path}: {W}x{H} {len(fr)} frames stats={stats} -> {outdir}')
