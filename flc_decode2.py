#!/usr/bin/env python3
"""SMAC .flc decoder v2 — transcribed from terran.exe:
  FUN_0062ad73  animation open (header 0x80 B, magic u16@+4==0xAF12,
                W=u16@+8, H=u16@+10)
  FUN_0062bdeb  chunk dispatch (u32 size + u16 type; 0xF1FA = container,
                recurse subchunk-count times; else leaf handlers;
                unknown -> seek size-6)
  FUN_0062b3da  type 0x0f 8-bit rows: per row [1 discarded byte], then
                packets until remaining<=0:
                  s8 c;  c >= 1 -> RLE: read 1 value byte, fill c px (val+ref)
                             c <= 0 -> literal: copy -c bytes (each +ref)
  FUN_0062bc1d  type 0x10 raw rows (W bytes/row, +ref)
  FUN_0062bb73  type 0x0d clear rect
  FUN_0062b68e  type 0x07 16-bit small-brun (see brun16)
Palette: programs/palette.pcx.
Usage: python3 flc_decode2.py <file.flc> <outdir> [pal.pcx]"""
import struct, sys, os
from PIL import Image

class R:
    def __init__(s, d, p=0): s.d, s.p = d, p
    def read(s, n):
        b = s.d[s.p:s.p+n]
        if len(b) != n: raise EOFError(f'{n}@{s.p}')
        s.p += n; return b
    def u8(s):  return s.read(1)[0]
    def s8(s):  return struct.unpack('<b', s.read(1))[0]
    def u16(s): return struct.unpack('<H', s.read(2))[0]
    def u32(s): return struct.unpack('<I', s.read(4))[0]

def rows8(r, W, H, fb, ref=0):
    """FUN_0062b3da: rows = H (this+0x5a0); each row: 1 leading byte read
    and discarded; then packets while remaining>0 (remaining starts W)."""
    for y in range(H):
        r.u8()                       # leading byte (read, unused by exe)
        base = y*W
        x = 0; remaining = W
        while remaining > 0:
            c = r.s8()
            if c >= 1:               # RLE: value byte follows
                v = r.u8()
                if ref: v = (v + ref) & 0xFF
                n = c
                for i in range(n):
                    if x < W: fb[base+x+i] = v
                x += n; remaining -= n
            else:                    # literal -c bytes
                n = -c
                lit = r.read(n)
                for i in range(n):
                    b = lit[i]
                    if ref: b = (b + ref) & 0xFF
                    if x < W: fb[base+x+i] = b
                x += n; remaining -= n

def rawrows(r, W, H, fb, ref=0):
    for y in range(H):
        row = r.read(W)
        for i in range(W):
            b = row[i]
            if ref: b = (b + ref) & 0xFF
            fb[y*W+i] = b

def load_palette(p):
    img = Image.open(p).convert('P'); pal = img.getpalette()
    return [tuple(pal[3*i:3*i+3]) for i in range(256)]

def decode(path):
    d = open(path,'rb').read()
    w = [struct.unpack('<H', d[i:i+2])[0] for i in range(0,128,2)]
    assert w[2] == 0xAF12, f'bad magic {w[2]:#x}'
    W, H = w[4], w[5]
    r = R(d, 128); fb = [0]*(W*H); frames = []
    while r.p + 16 <= len(d):
        fpos = r.p
        size = r.u32(); typ = r.u16()
        if typ != 0xF1FA or size < 16: 
            print(f'stop frame at {fpos}: size={size} typ={typ:#x}'); break
        subcnt = r.u16()
        r.read(8)                      # frame header is 16 B total
        rend = fpos + size
        def leaf(r):
            sz = r.u32(); t = r.u16()
            if sz < 6: raise ValueError('bad chunk')
            cend = r.p + sz - 6
            if t == 0xF1FA:
                n = r.u16()
                for _ in range(n): leaf(r)
            elif t == 0x000F: rows8(r, W, H, fb)
            elif t == 0x0010: rawrows(r, W, H, fb)
            elif t == 0x000D: fb[:] = [0]*(W*H)
            r.p = cend
        for _ in range(subcnt if subcnt else 1):
            if r.p + 6 > rend: break
            leaf(r)
        r.p = rend
        frames.append(list(fb))
    return W, H, frames

def render(W, H, frames, pal, outdir, maxf=40):
    os.makedirs(outdir, exist_ok=True)
    for i, px in enumerate(frames[:maxf]):
        img = Image.new('RGB', (W, H)); p = img.load()
        for y in range(H):
            for x in range(W): p[x,y] = pal[px[y*W+x]]
        img.save(f'{outdir}/frame_{i:02d}.png')
    return min(len(frames), maxf)

if __name__ == '__main__':
    path = sys.argv[1]; outdir = sys.argv[2]
    pal = load_palette(sys.argv[3] if len(sys.argv)>3 else 'programs/palette.pcx')
    W, H, fr = decode(path)
    n = render(W, H, fr, pal, outdir)
    print(f'{path}: {W}x{H}, {len(fr)} frames, {n} rendered -> {outdir}')
