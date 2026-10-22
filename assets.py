#!/usr/bin/env python3
"""SMAC asset pipeline: PCX -> PNG (Pillow), FLI/FLC -> PNG frames (hand decoder), contact sheets.
Usage:
  python3 assets.py pcx <srcdir> <outdir>
  python3 assets.py flic <srcdir> <outdir>
  python3 assets.py sheet <imgdir> <out.png> [cols] [cell]
Note on PCX: SMAC's .pcx files use an 8-byte-prefixed PCX variant (starts 0A 05);
Pillow 12's PCX plugin accepts magic 0A and decodes them to coherent images.
A hand-rolled classic per-row RLE decoder matches on some files (Dot*) but not
others (Icons/Airdp_sm) — the exact SMAC encoding is an open puzzle; we use
Pillow as reference decoder.
"""
import sys, os, glob, struct
from PIL import Image, ImageDraw, ImageFont

# ---------------- PCX ----------------
def pcx_to_png(src, dst):
    im = Image.open(src); im.load()
    if im.mode != 'P':
        im.save(dst)
    else:
        im.convert('RGB').save(dst)
    return im.size

# ---------------- FLIC ----------------
CHUNK_NAMES = {0x04F3:'COLOR_256_0',0x04F2:'COLOR_65536_0',0x04F1:'COLOR_256_1',
 0x04B0:'OFFLINE_KEY',0x04B1:'REAL_256_0',0x04B2:'REAL_256_1',0x04B3:'REAL_65536_0',
 0x04B4:'REAL_65536_1',0x0452:'FL1_COLOR',0x0451:'OPCODE5',0x0411:'BYTE_RUN',
 0x0412:'WORD_RUN',0x0413:'BRUN_16',0x0414:'WRUN_16',0x0415:'FULL_36_0',
 0x0416:'SMALLDELTA',0x0417:'BIGDELTA',0x0418:'TRUECOL_256',0x0419:'TRUECOL_65536',
 0x041A:'FULL_36_1',0x0430:'DELTA_FLI',0x0431:'BLACK_RAW',0x0432:'BLACK_RUN',
 0x0436:'WHITE_RUN',0x0437:'LAST_BYTE_RUN',0x0438:'COPY_LINE',0x0439:'SKIP_LINE',
 0x043A:'GREY_REP',0x043B:'GREY_RUN',0x04BA:'EXTERNAL_PIC',0x04B7:'EOL',
 0x04F1:'SELECTOR',0x04F2:'MAGIC_MASK',0x04F3b:'MAGIC_TRANSPARENCY',
 0x04F4:'MAX_SIZE',0x04F5:'ZSIZE',0x0453:'OPCODE5_FL2_PIC',0x0454:'OPCODE5_FL2_PIC'}

def flic_decode(src):
    """Return list of PIL Image (RGB). Handles 8-bit FLC/FLI common chunks."""
    d = open(src, 'rb').read()
    magic = struct.unpack('<H', d[4:6])[0]
    if magic not in (0xAF12, 0xAF13):
        raise ValueError(f"not FLIC magic {magic:#x}")
    nframes = struct.unpack('<H', d[8:10])[0]
    w, h = struct.unpack('<H', d[18:20])[0], struct.unpack('<H', d[20:22])[0]
    depth = struct.unpack('<H', d[22:24])[0]
    if depth != 8:
        raise ValueError(f"depth {depth} unsupported")
    foff = [struct.unpack('<I', d[128 + i*8:132 + i*8])[0] for i in range(nframes)]
    frames = []
    palette = [(i,i,i) for i in range(256)]
    cur = bytearray(w*h)  # current frame indices
    for fi in range(nframes):
        off = foff[fi]
        if off == 0:
            frames.append(bytes(cur)); continue
        fsize, ftype = struct.unpack('<I H', d[off:off+6])
        p = off + 6
        fend = off + fsize
        if ftype == 0xAF12:  # FLI_OLD_STYLE: skip 12-byte old header
            p += 12
        while p + 6 <= fend:
            csz, ctyp = struct.unpack('<I H', d[p:p+6])
            if csz == 0: break
            cp = p + 6; cend = p + csz
            def put(x, y, v):
                if 0 <= x < w and 0 <= y < h: cur[y*w+x] = v
            if ctyp in (0x04F3, 0x04B1):  # full 256 palette
                pal = d[cp:cp+768]
                palette = [(pal[i],pal[i+1],pal[i+2]) for i in range(0,768,3)]
            elif ctyp in (0x04F1, 0x0418, 0x04B2, 0x0452):  # palette delta variants
                first, count = struct.unpack('<HH', d[cp:cp+4]); cp += 4
                i = 0
                while i < count:
                    r, g, b = d[cp], d[cp+1], d[cp+2]; cp += 3
                    n = 1
                    if r == 0 and g == 0 and b == 0 and ctyp != 0x0418 and i < count-1:
                        n = d[cp]; cp += 1
                    elif r == 0 and g == 0 and b == 0 and ctyp == 0x0418 and i < count-1:
                        n = d[cp]; cp += 1
                    for j in range(n):
                        k = (first + i + j) % 256
                        palette[k] = (r, g, b)
                    i += n
            elif ctyp in (0x0411, 0x0451):  # BYTE_RUN / OPCODE5 (RLE rows)
                for y in range(h):
                    cnt = d[cp]; cp += 1
                    x = 0
                    while cnt:
                        if cnt < 0: cnt = -cnt
                        for _ in range(cnt):
                            put(x, y, d[cp]); cp += 1; x += 1
                        cnt = d[cp]; cp += 1
            elif ctyp == 0x0412:  # WORD_RUN
                for y in range(h):
                    cnt = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                    x = 0
                    while cnt:
                        if cnt < 0: cnt = -cnt
                        for _ in range(cnt):
                            put(x, y, d[cp]); cp += 1; x += 1
                        cnt = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
            elif ctyp in (0x0413, 0x0414):  # BRUN_16 / WRUN_16: copy rows unchanged
                pass
            elif ctyp == 0x04B0:  # OFFLINE_KEY (LRC)
                maxy = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                for y in range(maxy):
                    cnt = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                    x = 0
                    while cnt:
                        if cnt & 0x8000:
                            cnt &= 0x3FFF
                            flag = bool(cnt & 0x2000); cnt &= 0x1FFF
                            for _ in range(cnt):
                                v = d[cp]; cp += 1
                                put(x, y, cur[(y-1)*w+x] if (flag and y) else v)
                                x += 1
                        else:
                            v = d[cp]; cp += 1
                            put(x, y, cur[(y-1)*w+x] if (v & 0x80 and y) else (v & 0x7F))
                            x += 1; cnt -= 1
            elif ctyp == 0x0417:  # BIGDELTA
                maxy = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                for y in range(maxy):
                    cnt = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                    x = 0
                    while cnt:
                        if cnt > 0x8000:
                            cnt = cnt - 0x10000; x -= cnt; cnt = 0
                        else:
                            for _ in range(cnt):
                                v = d[cp]; cp += 1
                                put(x, y, cur[(y-1)*w+x] if v & 0x80 else v)
                                x += 1
                            cnt = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
            elif ctyp == 0x0416:  # SMALLDELTA
                maxy = struct.unpack('<H', d[cp:cp+2])[0]; cp += 2
                for y in range(maxy):
                    cnt = d[cp]; cp += 1
                    x = 0
                    while cnt:
                        if cnt > 128: cnt -= 256; x -= cnt; cnt = 0
                        else:
                            for _ in range(cnt):
                                v = d[cp]; cp += 1
                                put(x, y, cur[(y-1)*w+x] if v & 0x80 else v)
                                x += 1
                            cnt = d[cp]; cp += 1
            elif ctyp in (0x0431, 0x0432, 0x0436, 0x0437, 0x0438, 0x0439, 0x043A, 0x043B, 0x0430):
                pass  # FLI_256 old chunks: rare in SMAC files; skip
            elif ctyp in (0x04BA, 0x04B7, 0x04F4, 0x04F5, 0x04B9, 0x0453, 0x0454):
                pass
            else:
                raise ValueError(f"unhandled flic chunk {ctyp:#x} in {src}")
            p += csz
        frames.append(bytes(cur))
    out = []
    for fidx in frames:
        im = Image.new('P', (w, h))
        im.putdata(list(fidx))
        flat = [c for rgb in palette for c in rgb]
        im.putpalette(flat)
        out.append(im.convert('RGB'))
    return out

# ---------------- driver ----------------
def do_pcx(srcdir, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(srcdir, '**', '*.pcx'), recursive=True)) \
          + sorted(glob.glob(os.path.join(srcdir, '**', '*.PCX'), recursive=True))
    ok = fail = 0
    for f in files:
        rel = os.path.relpath(f, srcdir)
        dst = os.path.join(outdir, os.path.splitext(rel)[0] + '.png')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            pcx_to_png(f, dst); ok += 1
        except Exception as e:
            fail += 1; print(f"FAIL {rel}: {e}")
    print(f"PCX: {ok} ok, {fail} fail")

def do_flic(srcdir, outdir):
    os.makedirs(outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(srcdir, '**', '*.fl[ic]'), recursive=True)) \
          + sorted(glob.glob(os.path.join(srcdir, '**', '*.FL[IC]'), recursive=True))
    ok = fail = 0
    for f in files:
        rel = os.path.relpath(f, srcdir)
        base = os.path.splitext(rel)[0]
        dst = os.path.join(outdir, base)
        os.makedirs(dst, exist_ok=True)
        try:
            frames = flic_decode(f)
            for i, img in enumerate(frames):
                img.save(os.path.join(dst, f"{i:03d}.png"))
            print(f"OK {rel}: {len(frames)} frames")
            ok += 1
        except Exception as e:
            fail += 1; print(f"FAIL {rel}: {type(e).__name__} {e}")
    print(f"FLIC: {ok} ok, {fail} fail")

def do_sheet(imgdir, out, cols=8, cell=256):
    imgs = []
    for p in sorted(glob.glob(os.path.join(imgdir, '**', '*.png'), recursive=True)):
        try:
            im = Image.open(p); im.load()
        except Exception:
            continue
        imgs.append((os.path.relpath(p, imgdir), im))
    if not imgs: print("no images"); return
    rows = (len(imgs) + cols - 1) // cols
    cw = ch = cell
    label_h = 14
    sheet = Image.new('RGB', (cols * cw, rows * (ch + label_h)), (24, 24, 28))
    dr = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except Exception: font = ImageFont.load_default()
    for i, (name, im) in enumerate(imgs):
        im.thumbnail((cell, cell))
        x = (i % cols) * cw; y = (i // cols) * (ch + label_h)
        sheet.paste(im.convert('RGB'), (x + (cw - im.width)//2, y + (ch - im.height)//2))
        dr.text((x + 2, y + ch + 1), name[:44], fill=(200, 200, 210), font=font)
    sheet.save(out)
    print(f"sheet {out}: {len(imgs)} images, {cols}x{rows} cells")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == 'pcx': do_pcx(sys.argv[2], sys.argv[3])
    elif cmd == 'flic': do_flic(sys.argv[2], sys.argv[3])
    elif cmd == 'sheet': do_sheet(sys.argv[2], sys.argv[3], *(int(a) for a in sys.argv[4:]))
