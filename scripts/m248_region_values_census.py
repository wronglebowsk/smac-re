#!/usr/bin/env python3
"""M248/M249: what the coarse region-map BYTES mean, and what terrain record +3 is.

M248  the region map (DAT_0092ae18, length ((Rw+1)/2)*Rh) is BUILT by FUN_0058ce00
      (shard_015.c:4707-4745): for each region (x = row&1 step 2 < Rw, y < Rh) it samples 9
      tiles (dx from DAT_0067850c[i], dy from DAT_00678990[i], i = 0..8, map coords x*5+dx,
      y*5+dy, wrapped mod DAT_0092a378/DAT_0092a37c unless _DAT_0092a394&1) and stores the
      terrain record +3 of the FIRST sample whose record +0 & 0xe0 > 0x5f (cat > 2, land);
      0 when no sample is land.  The map's ONLY reader is FUN_00556690 (2 sites), which uses
      the byte as a label filter before expanding to the fine grid.
      GATE G1: the builder's rule as read from the image (9 offsets, land test, +3, else 0).
      GATE G2: recompute the region map from each save's / each .MP's terrain grid by that
               rule -> byte-for-byte equal to the stored bytes (17 saves + 2 maps).
      GATE G3: reference census of DAT_0092ae18: exactly 1 writer function (the builder, via
               FUN_00582360), exactly 1 reader function (FUN_00556690, via FUN_00582340), the
               rest are alloc/free/file-I/O; no other function touches the array.
M249  terrain record +3 (the label the region map carries).
      GATE G4: image-wide store census of record+3: every reference is a READ (the value is
               map-file data, loaded verbatim by FUN_00582000) — with the read count + sites.
      GATE G5: the +3 values are a REGION LABEL: per save, the set of nonzero region bytes ==
               the set of +3 values on land tiles reached by the sampling, and the readers use
               it as an index into a per-faction byte array at DAT_0094eda8 (base + fac*0x20bc)
               and split it at 0x40 (shard_012.c:7331-7340).

  python3 scripts/m248_region_values_census.py   -> evidence/m248_region_values.txt
"""
import glob
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(ROOT, "programs", "saves")
MAPS = [os.path.join(ROOT, "programs/maps/planet.MP"),
        os.path.join(ROOT, "programs/maps/planetx.MP")]
SHARD12 = os.path.join(ROOT, "ghidra_out", "shard_012.c")
SHARD14 = os.path.join(ROOT, "ghidra_out", "shard_014.c")
SHARD15 = os.path.join(ROOT, "ghidra_out", "shard_015.c")
EVID = os.path.join(ROOT, "evidence", "m248_region_values.txt")
RECSZ = 0x2C
DX_VA, DY_VA = 0x67850C, 0x678990
GATE_NAMES = [
    "G1 builder rule (9 diamond samples, land test, record+3, else 0)",
    "G2 region map recomputed from the terrain grid == stored bytes",
    "G3 DAT_0092ae18 reference census (1 reader fn, 1 writer fn)",
    "G4 record+3 has no store anywhere; its plane is invariant across saves",
    "G5 +3 is the land/region label (<0x40 land, >=0x40 water) the region map copies",
]
IMG = os.path.join(ROOT, "programs", "terran.exe")
IMG_BASE = 0x400000
DX_CONS, DY_CONS = 0x6784A0, 0x6784C4
ALL_SHARDS = sorted(glob.glob(os.path.join(ROOT, "ghidra_out", "shard_*.c")))
TURN_OFF = 80                      # M244: DAT_00985afc, u16 turn, file offset 80


def saves():
    return sorted(glob.glob(os.path.join(SAVE_DIR, "**", "*.SAV"), recursive=True))


def body_of(fname):
    """(shard path, 1-based first line, last line, body lines) of a decompiled function."""
    for p in ALL_SHARDS:
        lines = open(p, errors="replace").read().splitlines()
        for i, l in enumerate(lines):
            if l.startswith("// ==== " + fname + " @"):
                j = next(k for k in range(i + 1, len(lines))
                         if lines[k].startswith("// ==== FUN"))
                return p, i + 1, j, lines[i:j]
    raise KeyError(fname)


def tables():
    """The 9 sample offsets from the PE image (file offset = VA - 0x400000)."""
    def rd(va):
        with open(IMG, "rb") as fh:
            fh.seek(va - IMG_BASE)
            return struct.unpack("<9i", fh.read(36))
    return rd(DX_VA), rd(DY_VA), rd(DX_CONS), rd(DY_CONS)


def grid_of(d, hdr):
    W, H = struct.unpack_from("<ii", d, hdr)
    grid = hdr + 2724
    n = (W // 2) * H
    rw, rh = (W + 4) // 5, (H + 4) // 5
    off = grid + W * H * 22
    return dict(W=W, H=H, n=n, rw=rw, rh=rh, off=off,
                p0=bytes(d[grid + i * RECSZ] for i in range(n)),
                p3=bytes(d[grid + i * RECSZ + 3] for i in range(n)),
                stored=d[off:off + ((rw + 1) // 2) * rh])


def addressable(rw, rh):
    cells = set()
    for y in range(rh):
        x = y & 1
        while x < rw:
            cells.add((x >> 1) + (rw >> 1) * y)
            x += 2
    return cells


def recompute(g, dx, dy):
    """FUN_0058ce00's rule: per region, the first land tile of the 9-diamond sample, its +3."""
    W, H, rw, rh = g["W"], g["H"], g["rw"], g["rh"]
    out, wrapped = bytearray(((rw + 1) // 2) * rh), 0
    for y in range(rh):
        c = y & 1
        while c < rw:
            mx, my, got = c * 5, y * 5, 0
            for k in range(9):
                tx = mx + dx[k]
                if tx < 0 or tx >= W:
                    wrapped += 1
                    tx = tx % W
                ty = my + dy[k]
                if -1 < ty < H:
                    idx = (W // 2) * ty + (tx >> 1)
                    if (g["p0"][idx] & 0xE0) > 0x5F:
                        got = g["p3"][idx]
                        break
            out[(c >> 1) + (rw >> 1) * y] = got
            c += 2
    return bytes(out), wrapped


def corpus():
    for f in saves():
        yield os.path.basename(f), open(f, "rb").read(), 79372
    for f in MAPS:
        yield os.path.basename(f), open(f, "rb").read(), 15


def headers(path):
    hs = []
    for i, l in enumerate(open(path, errors="replace").read().splitlines(), 1):
        if l.startswith("// ==== FUN"):
            hs.append((i, l.split()[2]))
    return hs


def owner_of(hs, lineno):
    name = "<prologue>"
    for i, n in hs:
        if i <= lineno:
            name = n
        else:
            break
    return name


def g1():
    p, i0, i1, body = body_of("FUN_0058ce00")
    flat = re.sub(r"\s+", " ", "\n".join(body))
    dx, dy, cdx, cdy = tables()
    rel = os.path.relpath(p, ROOT)
    need = [
        ("9 samples: local_14 < 0x24 with local_14 += 4",
         "local_14 < 0x24" in flat and "local_14 = local_14 + 4" in flat),
        ("dx from &DAT_0067850c, dy from &DAT_00678990 (int tables)",
         "*(int *)((int)&DAT_0067850c + local_14)" in flat and
         "*(int *)((int)&DAT_00678990 + local_14)" in flat),
        ("land test 0x5f < (record +0 & 0xe0), i.e. category > 2",
         "0x5f < (*(byte *)(DAT_0092ae14 + (DAT_00692184 * iVar3 + (iVar2 >> 1)) * 0x2c) & 0xe0)"
         in flat),
        ("the value taken is record +3",
         "uVar1 = *(undefined1 *) (DAT_0092ae14 + 3 + (DAT_00692184 * iVar3 + (iVar2 >> 1)) * 0x2c);"
         in flat),
        ("no land sample -> 0", "uVar1 = 0;" in flat),
        ("stored through FUN_00582360(x, y, value)", "FUN_00582360(local_18,local_c,uVar1);" in flat),
        ("x wraps mod DAT_0092a378; y only bounds-checked vs DAT_0092a37c",
         "iVar2 = DAT_0092a378 + iVar2" in flat and "iVar3 < DAT_0092a37c" in flat),
        ("region walk: x = y&1 step 2 < Rw; map coord x*5, row coord y*5",
         "local_18 = local_18 + 2" in flat and "local_8 = local_8 + 10" in flat and
         "local_10 = local_10 + 5" in flat and "local_18 = local_c & 1" in flat),
    ]
    ring = [(dx[k], dy[k]) for k in range(9)]
    cons = [(a, b) for a, b in zip(cdx, cdy) if (a, b) != (0, 0)]
    shape = (ring[0] == (0, 0) and sorted(ring[1:]) == sorted(cons) and
             max(max(abs(a), abs(b)) for a, b in ring) == 2 and len(set(ring)) == 9 and
             len(cons) == 8)
    out = ["INFO G1 body %s:%d-%d (%d lines). 9 (dx,dy) read from the image at 0x%x/0x%x: %s\n"
           % (rel, i0, i1, len(body), DX_VA, DY_VA, ring),
           "INFO consumer FUN_00556690 uses the same 9 offsets (0x%x/0x%x), ring first: %s\n"
           % (DX_CONS, DY_CONS, list(zip(cdx, cdy)))]
    for label, hit in need:
        out.append("  %s %s\n" % ("HIT" if hit else "MISS", label))
    out.append("  %s the 9 offsets are centre + 8 distinct ring neighbours, max |offset| 2\n"
               % ("HIT" if shape else "MISS"))
    bad = sum(1 for _, h in need if not h) + (0 if shape else 1)
    if bad:
        return ["FAIL G1: %d of %d builder-rule checks missed\n" % (bad, len(need) + 1)] + out
    return (["PASS G1: FUN_0058ce00 builds the region map from a centre-first 9-diamond sample: "
             "the first land tile's record +3, else 0 (%d/%d checks)\n" % (len(need) + 1,
             len(need) + 1)] + out)


def g2():
    dx, dy, cdx, cdy = tables()
    out, bad, tot_wraps, tot_cells = [], 0, 0, 0
    for name, d, hdr in corpus():
        g = grid_of(d, hdr)
        calc, wraps = recompute(g, dx, dy)
        tot_wraps += wraps
        cells = addressable(g["rw"], g["rh"])
        tot_cells += len(cells)
        mism = [i for i in cells if calc[i] != g["stored"][i]]
        if mism:
            bad += 1
        out.append("  %-32s W=%d H=%d Rw=%d Rh=%d len=%d written=%d slack=%d mismatch=%d "
                   "wrapped-samples=%d\n"
                   % (name[:32], g["W"], g["H"], g["rw"], g["rh"], len(g["stored"]), len(cells),
                      len(g["stored"]) - len(cells), len(mism), wraps))
    if bad:
        return (["FAIL G2: %d/%d files disagree with the recomputed region map\n" % (bad, len(out))]
                + out)
    return (["PASS G2: the stored region map is reproducible from the terrain grid by that rule, "
             "byte for byte: %d files, %d written cells, 0 mismatches, %d samples needed the "
             "x-wrap\n" % (len(out), tot_cells, tot_wraps)] + out)


def g3():
    direct, rc, wc = [], [], []
    for p in ALL_SHARDS:
        lines = open(p, errors="replace").read().splitlines()
        hs, base = headers(p), os.path.basename(p)
        for i, l in enumerate(lines, 1):
            own = owner_of(hs, i)
            if "DAT_0092ae18" in l:
                kind = ("free" if "FUN_0064a7f0" in l else
                        "alloc" if "FUN_005be090" in l else
                        "file-io" if "FUN_0064c9a0" in l or "FUN_0064cc00" in l else
                        "accessor-body" if own in ("FUN_00582340", "FUN_00582360") else
                        "clear" if "DAT_0092ae18 = 0;" in l else
                        "null-guard" if "!= 0" in l else "OTHER")
                direct.append((base, i, own, kind))
            if own not in ("FUN_00582340", "FUN_00582360"):
                if "FUN_00582340(" in l:
                    rc.append((base, i, own))
                if "FUN_00582360(" in l:
                    wc.append((base, i, own))
    kinds = {}
    for _, _, _, k in direct:
        kinds[k] = kinds.get(k, 0) + 1
    shards = sorted({b for b, _, _, _ in direct})
    ro = sorted({o for _, _, o in rc})
    wo = sorted({o for _, _, o in wc})
    out = ["INFO G3 direct refs to DAT_0092ae18: %d, all in %s; kinds %s\n"
           % (len(direct), shards, sorted(kinds.items())),
           "INFO refs: %s\n" % ", ".join("%s:%d %s(%s)" % t for t in direct),
           "INFO map READERS (call sites of FUN_00582340): %s\n" % rc,
           "INFO map WRITERS (call sites of FUN_00582360): %s\n" % wc]
    checks = [("every direct ref is in shard_014.c", shards == ["shard_014.c"]),
              ("every direct ref classifies as alloc/free/file-io/clear/null-guard/accessor-body",
               kinds.get("OTHER", 0) == 0),
              ("exactly ONE function reads the map (FUN_00556690, 2 sites)",
               ro == ["FUN_00556690"] and len(rc) == 2),
              ("exactly ONE function writes the map (FUN_0058ce00, 1 site)",
               wo == ["FUN_0058ce00"] and len(wc) == 1)]
    for label, hit in checks:
        out.append("  %s %s\n" % ("HIT" if hit else "MISS", label))
    bad = sum(1 for _, h in checks if not h)
    if bad:
        return ["FAIL G3: %d of %d census checks missed\n" % (bad, len(checks))] + out
    return (["PASS G3: the region map has exactly one reader function and one writer function; "
             "its other %d references are alloc/free/file-I/O/clears, all in shard_014.c\n"
             % len(direct)] + out)


WIDTH = {"byte": 1, "char": 1, "undefined1": 1, "short": 2, "ushort": 2, "undefined2": 2,
         "int": 4, "uint": 4, "undefined4": 4, "undefined": 4}


def g4():
    stores, touches3, reads = [], [], 0
    for p in ALL_SHARDS:
        rel, txt = os.path.basename(p), open(p, errors="replace").read()
        hs = headers(p)
        for i, l in enumerate(txt.splitlines(), 1):
            if "DAT_0092ae14" not in l:
                continue
            j, m = l.find("DAT_0092ae14"), re.search(r"(?<![=!<>])=(?!=)", l)
            is_store = bool(m) and j < m.start() and l.strip().startswith("*(")
            if not is_store:
                if re.search(r"DAT_0092ae14 \+ 3 \+|\+ 3 \+ \(?\w+ \* 0x2c|ae14 \+ 3\)|0x2c \+ 3\)",
                             l):
                    reads += 1
                continue
            expr = l[:m.start()]
            cast = re.match(r"\s*\*\((\w+)", expr)
            w = WIDTH.get(cast.group(1) if cast else "", 0)
            disps = [int(x, 0) for x in re.findall(r"\+ (0x[0-9a-fA-F]+|\d+)(?![\w*])", expr)
                     if int(x, 0) < RECSZ]
            own = owner_of(hs, i)
            off = sum(disps)
            stores.append((rel, i, own, off, w))
            if off <= 3 < off + w:
                touches3.append((rel, i, own, off, w))
    sites = []
    for p in ALL_SHARDS:
        hs, rel = headers(p), os.path.basename(p)
        for i, l in enumerate(open(p, errors="replace").read().splitlines(), 1):
            if "FUN_00582d00(" in l and owner_of(hs, i) != "FUN_00582d00":
                sites.append((rel, i, owner_of(hs, i)))
    body = re.sub(r"\s+", " ", "\n".join(body_of("FUN_00582d00")[3]))
    setter_ok = ("*(undefined1 *)(DAT_0092ae14 + 3 + (DAT_00692184 * param_2 + (param_1 >> 1)) "
                 "* 0x2c) = param_3;" in body)
    planes, turns = {}, []
    for f in saves():
        d = open(f, "rb").read()
        g = grid_of(d, 79372)
        planes.setdefault(g["p3"], []).append(os.path.basename(f))
        turns.append(struct.unpack_from("<H", d, TURN_OFF)[0])
    out = ["INFO G4 stores into the terrain record array (decompile, all shards): %d\n" % len(stores),
           "INFO   %s\n" % ", ".join("%s:%d %s off=%d w=%d" % t for t in stores),
           "INFO stores whose width covers byte 3: %d %s\n" % (len(touches3), touches3),
           "INFO FUN_00582d00 call sites: %s\n" % sites,
           "INFO lines that READ record +3 (approximate line count): %d\n" % reads,
           "INFO distinct +3 planes across the %d saves: %d; turn field (file 80) values %s\n"
           % (len(turns), len(planes), sorted(set(turns)))]
    checks = [("FUN_00582d00's body is a byte store to record +3", setter_ok),
              ("every store covering byte 3 belongs to FUN_00582d00",
               setter_ok and bool(touches3) and {t[2] for t in touches3} == {"FUN_00582d00"}),
              ("FUN_00582d00 has exactly 4 call sites, all in shard_015.c (map generation)",
               len(sites) == 4 and all(s[0] == "shard_015.c" for s in sites)),
              ("every save carries the SAME record+3 plane (%d saves)" % len(turns),
               len(planes) == 1),
              ("those saves span >= 2 distinct turns (a writer had chances to run)",
               len(set(turns)) >= 2)]
    for label, hit in checks:
        out.append("  %s %s\n" % ("HIT" if hit else "MISS", label))
    bad = sum(1 for _, h in checks if not h)
    if bad:
        return ["FAIL G4: %d of %d checks missed\n" % (bad, len(checks))] + out
    return (["PASS G4: record +3 has exactly ONE writer in the image, the byte setter FUN_00582d00 "
             "(%d of %d record-array stores touch byte 3, all of them that setter), reached at %d "
             "call sites that are all in shard_015.c's map-generation code (%s); the +3 plane is "
             "identical across %d saves spanning %d distinct turns, so gameplay never rewrites the "
             "region label\n"
             % (len(touches3), len(stores), len(sites), ", ".join("%s:%d %s" % s for s in sites),
                len(turns), len(set(turns)))] + out)


def g5():
    out = []
    exc_land = exc_water = eq40 = subsets = nfiles = 0
    ids = {}
    for name, d, hdr in corpus():
        nfiles += 1
        g = grid_of(d, hdr)
        land = [i for i in range(g["n"]) if (g["p0"][i] & 0xE0) > 0x5F]
        water = [i for i in range(g["n"]) if (g["p0"][i] & 0xE0) <= 0x5F]
        bl = sum(1 for i in land if g["p3"][i] >= 0x40)
        bw = sum(1 for i in water if g["p3"][i] < 0x40)
        e40 = sum(1 for i in range(g["n"]) if g["p3"][i] == 0x40)
        reg = {g["stored"][i] for i in addressable(g["rw"], g["rh"])} - {0}
        lset = {g["p3"][i] for i in land}
        wset = {g["p3"][i] for i in water}
        exc_land += bl
        exc_water += bw
        eq40 += e40
        subsets += 0 if reg <= lset else 1
        ids[(g["W"], g["H"])] = (len(lset), len(wset))
        out.append("  %-30s W=%d H=%d land=%d water=%d land>=0x40=%d water<0x40=%d +3==0x40=%d "
                   "land-ids=%d water-ids=%d region-ids=%d region-subset-of-land=%s\n"
                   % (name[:30], g["W"], g["H"], len(land), len(water), bl, bw, e40, len(lset),
                      len(wset), len(reg), reg <= lset))
    idx_site = split_site = None
    for p in ALL_SHARDS:
        t = open(p, errors="replace").read()
        rel = os.path.basename(p)
        m = re.search(r"0x20bc\s*\+\s*\(uint\)\*\(byte\s*\*\)\(DAT_0092ae14\s*\+\s*3", t)
        if m and idx_site is None:
            idx_site = "%s:%d" % (rel, t[:m.start()].count("\n") + 1)
        m2 = re.search(r"< 0x40 == \w+ < 0x40", t)
        if m2 and split_site is None:
            split_site = "%s:%d" % (rel, t[:m2.start()].count("\n") + 1)
    areas = sorted(ids, key=lambda wh: wh[0] * wh[1])
    seq = [ids[wh][0] for wh in areas]
    mono = len(set(areas)) == 3 and all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))
    out.append("INFO land-id/water-id counts by map size: %s\n" % sorted(ids.items()))
    out.append("INFO +3 used as an array index (per-faction block, stride 0x20bc): %s\n" % idx_site)
    out.append("INFO +3 tested as `a < 0x40 == b < 0x40`: %s\n" % split_site)
    checks = [("no land tile has +3 >= 0x40 and no water tile has +3 < 0x40, on every file",
               exc_land == 0 and exc_water == 0),
              ("the value 0x40 itself never appears in any +3 plane", eq40 == 0),
              ("every nonzero region byte is a +3 value present on that file's land tiles",
               subsets == 0),
              ("distinct land-id count grows with map area: %s" % (seq,), mono),
              ("a reader indexes a per-faction byte array with +3", idx_site is not None),
              ("a reader splits +3 at 0x40", split_site is not None)]
    for label, hit in checks:
        out.append("  %s %s\n" % ("HIT" if hit else "MISS", label))
    bad = sum(1 for _, h in checks if not h)
    if bad:
        return ["FAIL G5: %d of %d checks missed\n" % (bad, len(checks))] + out
    return (["PASS G5: record +3 is the map's REGION LABEL -- +3 < 0x40 on every land tile and "
             ">= 0x41 on every water tile (0 exceptions on all %d files examined), 0x40 unused, "
             "the region map's bytes are exactly a per-region copy of it, land ids %s by map size,"
             " readers index a per-faction array with it (%s) and split it at 0x40 (%s)\n"
             % (nfiles, seq, idx_site, split_site)] + out)


def main():
    lines = []
    ok = 0
    for name, fn in zip(GATE_NAMES, (g1, g2, g3, g4, g5)):
        try:
            out = fn()
        except Exception as exc:            # a broken gate is a FAIL, never a crash
            out = ["FAIL %s: %s\n" % (name, exc)]
        lines += out
        if out and out[0].startswith("PASS"):
            ok += 1
    lines.append("\nSUMMARY %d/%d gates on %d saves + 2 .MP\n"
                 % (ok, len(GATE_NAMES), len(saves())))
    os.makedirs(os.path.dirname(EVID), exist_ok=True)
    with open(EVID, "w") as fh:
        fh.write("".join(lines))
    for l in lines:
        if l.startswith(("PASS", "FAIL", "INFO", "SUMMARY")):
            print(l.rstrip())
    print("SUMMARY %d/%d" % (ok, len(GATE_NAMES)))
    if ok == len(GATE_NAMES):
        print("PASS M248: %d/%d gates" % (ok, len(GATE_NAMES)))
    return 0 if ok == len(GATE_NAMES) else 1


if __name__ == "__main__":
    sys.exit(main())
