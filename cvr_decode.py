#!/usr/bin/env python3
"""Decoder + renderer for Sid Meier's Alpha Centauri (1999) .cvr models.

.cvr = "Caviar" voxel-model container (AnimaTek International's voxel
renderer, used by SMAC for isometric 3D units; exported from 3ds Max 4).

Format cross-validated two ways:
  1. terran.exe via REA/Ghidra 12.1.4 — chunk dispatch at FUN_006446e0
     (0x6446e0), per-object reader FUN_00644f80, voxel-chunk loader
     FUN_00645170, animation readers FUN_00645270/FUN_006454f0, entry
     FUN_00614acb. The exe validates the magic numerically (0x525643),
     copies "Bad file format" (0x69a95c) / "Number of objects mismatch"
     (0x69a97c) on failure.
  2. alphacentauri2.info/wiki/Caviar (PlotinusRedux/FordPrefect spec).
Chunk TLV: u32 LE tag + u32 LE size-including-header, nesting for containers.

Voxel model (wiki VOXEL_HEADER layout, corroborated by the exe storing the
blob opaquely at obj+0x2c[i] and reading *(blob+4) as its size):
  flags u32, size u32, units-per-3D-pixel float32, next u32, end u32,
  scale SVECTOR3(int16 Z,X,Y), position SVECTOR3, rotation-center SVECTOR3,
  voxel-count u32   (42 bytes)
  flags&1: multiple voxel headers; flags&2: JUMP_HEADERs before voxel runs
  VOXEL_DATA: 3 bytes/voxel: (dir<<3|normal_hi), normal_lo, color index
  direction = 5-bit delta index (0x1A = STOP), normal = 11-bit angle code

Usage:
  python3 cvr_decode.py [files...]            validate + summarize
  python3 cvr_decode.py --list file.cvr       list voxels/frames
  python3 cvr_decode.py --render file.cvr out.png [--level N]
"""
import struct, sys, os, glob, math, collections

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "programs")

T_OUTER, T_VERSION, T_DBNAME, T_PALGRP, T_PALNAME, T_PALDATA, T_MATERIAL = \
    0x00525643, 0x01000000, 0x02000000, 0x03000000, 0x01010000, 0x01020000, 0x01030000
T_SCENE, T_SCENENAME, T_OBJCOUNT, T_FRAMECOUNT, T_OBJGRP = \
    0x04000000, 0x4010000, 0x4020000, 0x4030000, 0x4040000
T_OBJNAME, T_GEOGRP, T_VOXELS, T_ANIMGRP, T_OBJFLAG, T_OBJLOC, T_OBJMAT = \
    0x4040100, 0x4040200, 0x4040201, 0x4040300, 0x4040301, 0x4040302, 0x4040303
T_BLOBU32 = 0x4040202
T_FACEGRP, T_ANIMIDX, T_ANIMREC = 0x4040400, 0x4050001, 0x4050002

# direction deltas (z, x, y), index = byte >> 3 (wiki table, matches Ford's)
DIRECTIONS = [(-1,-1,-1),(-1,-1,0),(-1,-1,1),(-1,0,-1),(-1,0,0),(-1,0,1),
              (-1,1,-1),(-1,1,0),(-1,1,1),(0,-1,-1),(0,-1,0),(0,-1,1),
              (0,0,-1),(0,0,1),(0,1,-1),(0,1,0),(0,1,1),
              (1,-1,-1),(1,-1,0),(1,-1,1),(1,0,-1),(1,0,0),(1,0,1),
              (1,1,-1),(1,1,0),(1,1,1)]
DIR_STOP = 0x1A

class CvrError(Exception): pass

def _chunks(buf, base, end):
    pos = base
    while pos + 8 <= end:
        typ, size = struct.unpack_from("<II", buf, pos)
        if size < 8 or pos + size > end:
            raise CvrError(f"bad chunk size {size} at {pos:#x} (region {base:#x}..{end:#x})")
        yield typ, size, pos + 8
        pos += size
    if pos != end:
        raise CvrError(f"{end - pos} trailing bytes at {pos:#x}")

def _string(buf, off, size):
    return buf[off:off+size].split(b"\x00", 1)[0].decode("latin1")

def _svec3(buf, off):
    z, x, y = struct.unpack_from("<3h", buf, off)
    return (z, x, y)

def decode_normal(dirbyte, normbyte):
    """11-bit normal angle code -> unit (x, y, z) (wiki DecodeNormal)."""
    n = ((dirbyte & 7) << 8) | normbyte
    n += 88
    a1 = (88 - n % 89) / 88.0 * 2.0 * math.pi
    a2 = (n // 89) / 23.0 * math.pi / 2.0
    return (math.cos(a1)*math.sin(a2), math.cos(a2), math.sin(a1)*math.sin(a2))

def load(path):
    buf = open(path, "rb").read()
    n = len(buf)
    it = _chunks(buf, 0, n)
    typ, size, pay = next(it, (None, None, None))
    if typ != T_OUTER: raise CvrError(f"missing CVR magic (got {typ:#x})")
    if size != n: raise CvrError(f"outer size {size} != file size {n}")
    m = {"path": path, "version": None, "db_name": None, "palette": None,
         "material16": None, "scene_name": None, "obj_count": None,
         "frame_count": None, "objects": [], "unknown": []}
    for typ, size, off in _chunks(buf, pay, pay + size - 8):
        if typ == T_VERSION:
            m["version"] = struct.unpack_from("<f", buf, off)[0]
        elif typ == T_DBNAME:
            m["db_name"] = _string(buf, off, size - 8)
        elif typ == T_PALGRP:
            for t2, s2, o2 in _chunks(buf, off, off + size - 8):
                if t2 == T_PALNAME:
                    m.setdefault("pal_name", _string(buf, o2, s2 - 8))
                elif t2 == T_PALDATA:
                    if s2 - 8 != 6914: raise CvrError(f"palette size {s2-8} != 6914")
                    first, last = buf[o2], buf[o2+1]
                    phys = [tuple(buf[o2+2+i*3:o2+5+i*3]) for i in range(256)]
                    shade = [list(buf[o2+770+lv*256:o2+770+lv*256+256]) for lv in range(24)]
                    m["palette"] = {"first": first, "last": last,
                                    "physical": phys, "shade": shade}
                elif t2 == T_MATERIAL:
                    if s2 - 8 != 12292: raise CvrError(f"material size {s2-8} != 12292")
                    # 4-byte header (observed (n<<16)|0xEC variants) + 24x256 u16
                    m["material16"] = {"hdr": struct.unpack_from("<I", buf, o2)[0],
                                       "shade16": list(struct.unpack_from("<6144H", buf, o2+4))}
                else:
                    m["unknown"].append(("palette", hex(t2), s2))
        elif typ == T_SCENE:
            for t2, s2, o2 in _chunks(buf, off, off + size - 8):
                if t2 == T_SCENENAME: m["scene_name"] = _string(buf, o2, s2 - 8)
                elif t2 == T_OBJCOUNT: m["obj_count"] = struct.unpack_from("<I", buf, o2)[0]
                elif t2 == T_FRAMECOUNT: m["frame_count"] = struct.unpack_from("<I", buf, o2)[0]
                elif t2 == T_OBJGRP: m["objects"].append(_object(buf, o2, s2 - 8, m))
                else: m["unknown"].append(("scene", hex(t2), s2))
        else:
            m["unknown"].append(("top", hex(typ), size))
    if m["obj_count"] is not None and m["obj_count"] != len(m["objects"]):
        raise CvrError(f"Number of objects mismatch: declared {m['obj_count']}, "
                       f"parsed {len(m['objects'])} (exe FUN_00644d70 check)")
    return m

def _object(buf, off, endrel, m):
    o = {"name": None, "voxels": None, "frames": None, "flags": None,
         "locs": None, "mats": None}
    for t, s, po in _chunks(buf, off, off + endrel):
        if t == T_OBJNAME:
            o["name"] = _string(buf, po, s - 8)
        elif t == T_GEOGRP:
            for t2, s2, p2 in _chunks(buf, po, po + s - 8):
                if t2 == T_VOXELS:
                    o["voxels"] = decode_voxels(buf, p2, s2 - 8, o)
                elif t2 == T_BLOBU32:
                    o["blob_u32"] = struct.unpack_from("<I", buf, p2)[0]
        elif t == T_ANIMGRP:
            nf = m.get("frame_count")
            for t2, s2, p2 in _chunks(buf, po, po + s - 8):
                if t2 == T_OBJFLAG:
                    o["flags"] = list(buf[p2:p2+s2-8])
                    if nf is not None and s2 - 8 != nf:
                        raise CvrError(f"{o['name']}: flag array {s2-8} != frame count {nf}")
                elif t2 == T_OBJLOC:
                    if (s2 - 8) % 12: raise CvrError("location chunk %% 12 != 0" % ())
                    o["locs"] = [(_svec3f(buf, p2+i*12)) for i in range((s2-8)//12)]
                    if nf is not None and (s2-8)//12 != nf:
                        raise CvrError(f"{o['name']}: {s2-8} locations != {nf} frames")
                elif t2 == T_OBJMAT:
                    if (s2 - 8) % 36: raise CvrError("matrix chunk % 36 != 0")
                    o["mats"] = [struct.unpack_from("<9f", buf, p2+i*36) for i in range((s2-8)//36)]
                    if nf is not None and (s2-8)//36 != nf:
                        raise CvrError(f"{o['name']}: {s2-8} matrices != {nf} frames")
        else:
            m["unknown"].append(("object", hex(t), s))
    return o

def _svec3f(buf, off):
    z, x, y = struct.unpack_from("<3f", buf, off)
    return (z, x, y)

def decode_voxels(buf, off, size, obj):
    """Parse one CVRCHUNK_VOXEL_OBJECT payload (wiki VOXEL_HEADER/JUMP_HEADER/
    VOXEL_DATA; exe FUN_00645170 stores this blob opaquely).

    Verified corpus rules:
      - VOXEL_HEADER 42 B; flags&1 = more headers follow at h+next (next is
        relative to this header); flags&2 = JUMP_HEADERs precede voxel runs.
      - Each array region ends with zero padding (observed: 5 bytes).
      - The final voxel of a run is usually STOP-coded (dcode 0x1A) and is a
        real voxel. In multi-header single-run mode arrays are exactly
        `count` triples and may end without a STOP code.
      - Single-header jump mode: sum(jc) == count + groups (Apsid); in
        multi-header jump mode sum(jc) == count (VHTTp). Both accepted.
    """
    if size < 42: raise CvrError("voxel chunk smaller than VOXEL_HEADER")
    all_voxels = []
    headers = []
    h = off
    hdr_index = 0
    while True:
        if h + 42 > off + size: raise CvrError("truncated VOXEL_HEADER")
        flags, sz, upp, nxt, end = struct.unpack_from("<IIfII", buf, h)
        scale = _svec3(buf, h+0x14)
        pos0 = _svec3(buf, h+0x1a)
        rotc = _svec3(buf, h+0x20)
        count = struct.unpack_from("<I", buf, h+0x26)[0]
        hdr = {"index": hdr_index, "offset": h-off, "flags": flags, "size": sz,
               "units_per_pixel": upp, "scale": scale, "position": pos0,
               "rotation_center": rotc, "count": count, "next": nxt, "end": end}
        region_end = (h + nxt) if (flags & 1 and nxt) else (off + size)
        if region_end > off + size:
            raise CvrError(f"header region overrun ({region_end-off} > {size})")
        voxels = []
        p = h + 42
        groups = 0
        walked = 0
        if flags & 2:
            while True:
                if p + 32 > region_end:
                    break
                if buf[p:region_end].strip(b"\x00") == b"":
                    break
                jz = [_svec3(buf, p+i*6) for i in range(4)]
                jcount, jflags = struct.unpack_from("<II", buf, p+0x18)
                hj = 36 if (jflags & 1) else 32
                pos = tuple(pos0[i] + jz[3][i] for i in range(3))
                hdr.setdefault("jumps", []).append(
                    {"position": jz[0], "v2": jz[1], "v3": jz[2], "offset": jz[3],
                     "count": jcount, "jflags": jflags, "hdr_len": hj})
                p += hj
                for i in range(jcount):
                    if p + 3 > region_end:
                        raise CvrError(f"voxel run overrun (hdr {hdr_index} group {groups})")
                    d, nb, col = buf[p], buf[p+1], buf[p+2]
                    p += 3
                    dcode = d >> 3
                    voxels.append((pos[0], pos[1], pos[2], col,
                                   decode_normal(d, nb), groups))
                    walked += 1
                    if dcode == DIR_STOP:
                        break
                    zz, xx, yy = DIRECTIONS[dcode]
                    pos = (pos[0]+zz, pos[1]+xx, pos[2]+yy)
                groups += 1
        else:
            pos = pos0
            for i in range(count):
                if p + 3 > region_end:
                    raise CvrError(f"voxel array overrun (header {hdr_index})")
                d, nb, col = buf[p], buf[p+1], buf[p+2]
                p += 3
                dcode = d >> 3
                voxels.append((pos[0], pos[1], pos[2], col,
                               decode_normal(d, nb), 0))
                walked += 1
                if dcode == DIR_STOP:
                    if any(buf[p:region_end]):
                        raise CvrError("nonzero data after STOP in single run")
                    break
                zz, xx, yy = DIRECTIONS[dcode]
                pos = (pos[0]+zz, pos[1]+xx, pos[2]+yy)
        pad = buf[p:region_end]
        if pad.strip(b"\x00") != b"":
            raise CvrError(f"{len(pad)} nonzero trailing bytes in header region")
        hdr["walked"] = walked
        hdr["groups"] = groups
        expected = {count, count + groups} if (flags & 2) else {walked}
        if walked not in expected:
            raise CvrError(f"{obj.get('name')}: header {hdr_index} walked {walked} "
                           f"!= count {count} (groups {groups})")
        headers.append(hdr)
        all_voxels.extend(voxels)
        hdr_index += 1
        if not (flags & 1) or not nxt:
            break
        h += nxt
    return {"header": headers[0], "headers": headers, "voxels": all_voxels}

# ---------------- rendering ----------------

def voxel_points(m, obj):
    return obj["voxels"]["voxels"] if obj["voxels"] else []

def render(m, level=11, light=None, block=2):
    """Isometric voxel render -> (width, height, rgb bytearray, points)."""
    pal = m["palette"]
    all_pts = []
    for o in m["objects"]:
        all_pts.extend(voxel_points(m, o))
    if not all_pts: return None
    # isometric projection in voxel units: +y up, camera along +(1,1,1)
    c30, s30 = math.cos(math.pi/6), math.sin(math.pi/6)
    pts = []
    for (z, x, y, col, nrm, g) in all_pts:
        sx = (x - z) * c30
        sy = y - (x + z) * s30
        depth = x + y + z
        pts.append((sx, sy, depth, col, nrm))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    W = int((max(xs)-min(xs)+2)*block); H = int((max(ys)-min(ys)+2)*block)
    x0, y0 = min(xs), min(ys)
    img = bytearray(W*H*3)
    for (sx, sy, depth, col, nrm) in sorted(pts, key=lambda p: p[2]):   # far first
        px = int(round((sx - x0)*block)); py = H - 1 - int(round((sy - y0)*block))
        lv = level
        if light is not None:
            d = sum(nrm[i]*light[i] for i in range(3))
            lv = max(0, min(23, int(11.5 + 11.5*d)))
        idx = pal["shade"][lv][col]
        r, g, b = pal["physical"][idx]
        for dy in range(block):
            yy = min(H-1, py-dy)
            row = (yy*W + px)*3
            img[row:row+block*3] = bytes((r, g, b)) * block
    return W, H, img, len(all_pts)

def save_png(path, W, H, img):
    try:
        from PIL import Image
        Image.frombytes("RGB", (W, H), bytes(img)).save(path)
        return "PIL"
    except ImportError:
        import zlib, struct as S
        raw = b"".join(b"\x00" + img[y*W*3:(y+1)*W*3] for y in range(H))
        def chunk(t, d): return S.pack(">I", len(d)) + t + d + S.pack(">I", S.crc32(t+d) & 0xffffffff)
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", S.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
        open(path, "wb").write(png)
        return "zlib-png"

# ---------------- CLI ----------------

def summarize(m, verbose=False):
    print(f"== {os.path.basename(m['path'])}")
    print(f"   format version {m['version']:.1f}  .max source: {m['db_name']}")
    pal = m["palette"]
    print(f"   palette {m.get('pal_name')!r}: colors {pal['first']}..{pal['last']}, "
          f"24x256 shade table" + (", 16-bit material table" if m["material16"] else ""))
    print(f"   scene {m['scene_name']!r}: {len(m['objects'])} objects "
          f"(declared {m['obj_count']}), {m['frame_count']} frames")
    for o in m["objects"]:
        v = o["voxels"]
        if v:
            h = v["header"]
            nhdr = len(v.get("headers", []))
            cols = collections.Counter(x[3] for x in v["voxels"])
            print(f"   - {o['name']!r}: {len(v['voxels'])} voxels in {h['groups']} group(s)"
                  + (f", {nhdr} VOXEL_HEADERs" if nhdr > 1 else "")
                  + f", flags={h['flags']}, units/pixel={h['units_per_pixel']}, "
                  f"scale(z,x,y)={h['scale']}, pos={h['position']}, count={h['count']}, "
                  f"{len(cols)} colors")
        else:
            nf = len(o["locs"]) if o["locs"] else 0
            print(f"   - {o['name']!r}: animation-only, {nf} frame(s)"
                  + (f" [{o['flags'][0] if o['flags'] else '?'} flags]" if o["flags"] else ""))
        if verbose and v:
            for i, (z, x, y, col, nrm, g) in enumerate(v["voxels"][:12]):
                print(f"       v{i:<3} g{g} (z={z:5d},x={x:5d},y={y:5d}) color={col:#04x} "
                      f"n=({nrm[0]:6.3f},{nrm[1]:6.3f},{nrm[2]:6.3f})")
            if len(v["voxels"]) > 12: print(f"       ... {len(v['voxels'])-12} more")
        if verbose and not v and o["locs"]:
            for i in range(min(4, len(o["locs"]))):
                z, x, y = o["locs"][i]
                print(f"       frame{i} loc(z,x,y)=({z:8.3f},{x:8.3f},{y:8.3f})")
    if m["unknown"]: print(f"   UNKNOWN chunks: {m['unknown']}")

def main(argv):
    mode = "summary"
    args = argv[1:]
    if args and args[0] == "--list": mode, args = "list", args[1:]
    if args and args[0] == "--render": mode, args = "render", args[1:]
    level = 11
    if "--level" in args:
        i = args.index("--level"); level = int(args[i+1]); del args[i:i+2]
    files = args or ["Apsid.cvr", "Asas.cvr"]
    if all("*" in f for f in files):
        import itertools
        files = sorted(itertools.chain.from_iterable(glob.glob(f) for f in files))
    ok = fail = 0
    for name in files:
        path = name if os.path.exists(name) else os.path.join(DIR, name)
        try:
            m = load(path)
        except CvrError as e:
            print(f"FAIL {name}: {e}"); fail += 1; continue
        ok += 1
        if mode == "summary":
            summarize(m, verbose=len(files) <= 3)
        elif mode == "list":
            summarize(m, verbose=True)
        elif mode == "render":
            r = render(m, level=level, light=(0.5, 0.7, 0.5))
            if r is None:
                print(f"{name}: no voxels to render"); continue
            W, H, img, npts = r
            out = os.path.join(os.getcwd(),
                               os.path.splitext(os.path.basename(name))[0] + ".render.png")
            how = save_png(out, W, H, img)
            print(f"rendered {name}: {npts} voxels -> {out} ({W}x{H}, {how})")
    print(f"\nvalidated {ok}/{ok+fail} files")
    return 0 if fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
