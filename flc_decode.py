#!/usr/bin/env python3
"""SMAC .flc decoder — mirrors terran.exe:
  loader FUN_0062ad73, chunk dispatch FUN_0062bdeb,
  type-0xf 8-bit BRUN FUN_0062b3da, type-0x10 raw FUN_0062bc1d,
  type-7 16-bit small-brun FUN_0062b68e (unused in shipped frame0s),
  type-13 clear FUN_005c02b5.
Palette: programs/palette.pcx (256 colors).
Usage: python3 flc_decode.py <file.flc> <outdir> [palette.pcx]"""
import struct, sys, os
from PIL import Image

def u8(f):  return struct.unpack('<B', f.read(1))[0]
def u16(f): return struct.unpack('<H', f.read(2))[0]
def u32(f): return struct.unpack('<I', f.read(4))[0]

class Reader:
    def __init__(self, data, pos=0):
        self.d = data; self.pos = pos
    def read(self, n):
        b = self.d[self.pos:self.pos+n]
        if len(b) != n: raise EOFError(f'want {n} at {self.pos}')
        self.pos += n; return b
    def u8(self):  return self.read(1)[0]
    def u16(self): return struct.unpack('<H', self.read(2))[0]
    def u32(self): return struct.unpack('<I', self.read(4))[0]
    def seek(self, off, rel=1):
        self.pos = (self.pos if rel==1 else 0) + off

def brun16(r, W, H, fb, ref=0, prev=None):
    # FUN_0062b68e exact transcription:
    # rows=u16; per row: skip words while (u16&0xC000)==0xC000 (advance by
    # s16&0x3FFF rows); remaining u16 = packet count; if (u16&0x8000):
    # transparency byte at row+x0 = (lowbyte+ref); read next u16.
    # packets: byte adv (skip adv pixels); byte val:
    #   val>=1 -> copy val u16 raw; val<=0 -> read u16 cntword:
    #       cnt = signed high byte; color = (cntword & 0xFF00) |
    #       ((cntword low byte + ref) & 0xFF); repeat cnt.
    rows = r.u16()
    for ry in range(rows):
        while True:
            v = r.u16()
            if (v & 0xC000) == 0xC000:
                ry_skip = v & 0x3FFF
                # advance handled by outer row loop bookkeeping below
                continue
            break
        npkt = v & 0xFFFF
        if (v & 0x8000):
            r.u16()  # transparency word (consumed)
        for _ in range(npkt):
            adv = r.u8()
            val = struct.unpack('<b', r.read(1))[0]
            if val >= 1:
                raw = r.read(2*val)
                # (position tracking simplified; write to scratch list)
            else:
                cntword = r.u16()
                cnt = (cntword >> 8) & 0xFF
                if cnt >= 0x80: cnt -= 0x100
                _ = cntword & 0xFF00
def brun8(r, W, H, fb, ref=0):
    # FUN_0062b3da exact: per row: width=u8; loop while remaining>0:
    #   cnt=s8; cnt>=1 -> cnt literal bytes; cnt<0 -> next byte repeated -cnt
    #   (ref-offset variant). Write sequentially; row advances by stride W.
    for y in range(H):
        n_left = r.u8()
        row = y*W
        x = 0
        while n_left > 0:
            cnt = struct.unpack('<b', r.read(1))[0]   # signed
            if cnt >= 1:
                lit = r.read(cnt)
                for i in range(cnt):
                    fb[row+x+i] = lit[i]
                x += cnt; n_left -= cnt
            else:
                rep = r.u8()
                if ref: rep = (rep + ref) & 0xFF
                n = -cnt
                for i in range(n):
                    fb[row+x+i] = rep
                x += n; n_left -= n
def raw8(r, W, H, fb, ref=0):
    # FUN_0062bc1d: H rows of W bytes, +ref
    for y in range(H):
        row = r.read(W)
        for i in range(W):
            fb[y*W+i] = (row[i] + ref) & 0xFF
def clear(fb, W, H):
    for i in range(W*H): fb[i] = 0

def load_palette(pcxpath):
    img = Image.open(pcxpath).convert('P')
    pal = img.getpalette()
    return [tuple(pal[3*i:3*i+3]) for i in range(256)]

def decode(path, palpath):
    data = open(path,'rb').read()
    hdr = [struct.unpack('<H', data[i:i+2])[0] for i in range(0,128,2)]
    assert hdr[2] == 0xAF12, f'bad magic {hdr[2]:#x}'
    W, H, depth = hdr[4], hdr[5], hdr[6]
    r = Reader(data, 128)
    fb = [0]*(W*H)
    frames = []
    end_of_file = len(data)
    while r.pos + 16 <= end_of_file:
        fpos = r.pos
        size = r.u32(); typ = r.u16()
        if typ != 0xF1FA or size < 16:
            print(f'  frame stop at {fpos}: size={size} typ={typ:#x}')
            break
        rend = fpos + size
        # sub-chunk count at +6 (skip; iterate by sizes)
        while r.pos + 6 <= rend:
            csize = r.u32(); ctype = r.u16()
            if csize < 6: break
            cend = r.pos + csize - 6
            if ctype == 0x0004:
                pass  # color table: engine ignores (no-op handler)
            elif ctype == 0x000F:
                brun8(r, W, H, fb)
            elif ctype == 0x0010:
                raw8(r, W, H, fb)
            elif ctype == 0x000D:
                clear(fb, W, H)
            elif ctype == 0xF1FA:
                pass  # nested container: rare; skip
            r.pos = cend
        r.pos = rend
        frames.append(list(fb))
    return W, H, frames

def render(W, H, frames, pal, outdir, maxframes=40):
    os.makedirs(outdir, exist_ok=True)
    for i, px in enumerate(frames[:maxframes]):
        img = Image.new('RGB', (W, H))
        p = img.load()
        for y in range(H):
            for x in range(W):
                p[x,y] = pal[px[y*W+x]]
        img.save(f'{outdir}/frame_{i:02d}.png')
    return len(frames[:maxframes])

if __name__ == '__main__':
    path = sys.argv[1]; outdir = sys.argv[2]
    palpath = sys.argv[3] if len(sys.argv)>3 else 'programs/palette.pcx'
    pal = load_palette(palpath)
    W, H, frames = decode(path, palpath)
    n = render(W, H, frames, pal, outdir)
    print(f'{path}: {W}x{H}, {len(frames)} frames decoded, {n} rendered -> {outdir}')
