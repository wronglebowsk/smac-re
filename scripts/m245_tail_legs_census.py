#!/usr/bin/env python3
"""M245/M246/M247: what the save tail's last three legs are (static + one /proc read).

M245  the 216-B leg = 9 rows x 6 dwords of per-window map-view state: the codec loop walks the 8
      pointers DAT_007cdecc..DAT_007cdee8 (bound `< 0x7cdeec`) then the inline object &DAT_008cda4c,
      and FUN_00596620 moves the six fields +0x1dd78 +0x1dd74 +0x1dd70 +0x1dd98 +0x1dd9c +0x1dda0 of
      each. Read back live from /proc against the save the box has loaded.
M246  the final 4 B = the timeGetTime() dword FUN_00597ce0 writes AFTER the codec returns.
M247  the region map's row stride: the only two element accessors of DAT_0092ae18 index with
      DAT_0092ad9c>>1, while the malloc/file length is ((DAT_0092ad9c+1)/2)*Rh.

  sudo -n python3 scripts/m245_tail_legs_census.py   -> evidence/m245_tail_legs.txt
"""
import glob
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(ROOT, "programs", "saves")
MAPS = [os.path.join(ROOT, "programs/maps/planet.MP"), os.path.join(ROOT, "programs/maps/planetx.MP")]
SHARD14 = os.path.join(ROOT, "ghidra_out", "shard_014.c")
SHARD15 = os.path.join(ROOT, "ghidra_out", "shard_015.c")
EVID = os.path.join(ROOT, "evidence", "m245_tail_legs.txt")
OFFS = [0x1dd78, 0x1dd74, 0x1dd70, 0x1dd98, 0x1dd9c, 0x1dda0]
VIEW_ARRAY, VIEW_INLINE = 0x7CDECC, 0x8CDA4C
MAP_HDR_OFF, MAP_HDR_LEN, CELL = 79372, 2724, 22


def saves():
    return sorted(glob.glob(os.path.join(SAVE_DIR, "**", "*.SAV"), recursive=True))


def body_of(path, fname):
    lines = open(path, errors="replace").read().splitlines()
    i0 = next(i for i, l in enumerate(lines) if l.startswith("// ==== " + fname))
    i1 = next(i for i, l in enumerate(lines[i0 + 1:], i0 + 1) if l.startswith("// ==== FUN"))
    return lines[i0:i1]


def dims_and_region(d, hdr_off):
    w, h = struct.unpack_from("<ii", d, hdr_off)
    rw, rh = (w + 4) // 5, (h + 4) // 5
    n = ((rw + 1) // 2) * rh
    off = hdr_off + MAP_HDR_LEN + w * h * CELL
    return w, h, rw, rh, off, d[off:off + n]


def addressable(rw, rh):
    """Every byte the two accessors can reach: index = (x>>1) + (rw>>1)*y, x = y&1 step 2 < rw."""
    cells = set()
    for y in range(rh):
        x = y & 1
        while x < rw:
            cells.add((x >> 1) + (rw >> 1) * y)
            x += 2
    return cells


def g1_codec_leg():
    s15 = open(SHARD15, errors="replace").read().splitlines()
    seen = []
    for l in body_of(SHARD15, "FUN_00596620"):
        m = re.search(r"param_1 \+ (0x1dd[0-9a-f]{2})", l)
        if m and int(m.group(1), 16) not in seen:
            seen.append(int(m.group(1), 16))
    j0 = next(i for i, l in enumerate(s15) if "puVar18 = &DAT_007cdecc;" in l)
    loop = "\n".join(s15[j0:j0 + 14])
    mb = re.search(r"while \(\(int\)puVar18 < (0x7cde[0-9a-f]{2})\)", loop)
    slots = (int(mb.group(1), 16) - VIEW_ARRAY) // 4 if mb else -1
    inline = "&DAT_008cda4c" in loop
    ids_ok, bad = 0, []
    for f in saves():
        t = open(f, "rb").read()[-228:-12]
        col0 = [struct.unpack_from("<i", t, r * 24)[0] for r in range(8)]
        if col0 == list(range(8)):
            ids_ok += 1
        else:
            bad.append(os.path.basename(f) + " " + repr(col0))
    good = (seen == OFFS and inline and slots == 8 and (slots + 1) * 6 * 4 == 216
            and ids_ok == len(saves()))
    return good, ("offsets=%s slots=%d inline=%s rows=%d  row0..7 ids==0..7 on %d/%d saves bad=%s"
                  % ([hex(o) for o in seen], slots, inline, slots + 1, ids_ok, len(saves()), bad[:2]))


def g2_live_readback():
    pids = subprocess.run(["pgrep", "-f", "terran.exe"], capture_output=True, text=True).stdout.split()
    pid = max((int(p) for p in pids), default=0)
    if not pid:
        return False, "no terran.exe running"
    st = open("/proc/%d/status" % pid).read()
    tp = [l for l in st.splitlines() if l.startswith("TracerPid")][0].split()[1]
    if tp != "0":
        return False, "TracerPid=%s (a debugger owns the box)" % tp
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    ptrs = struct.unpack("<8i", os.pread(fd, 32, VIEW_ARRAY))
    blob = b"".join(os.pread(fd, 4, (b & 0xFFFFFFFF) + o) for b in list(ptrs) + [VIEW_INLINE]
                    for o in OFFS)
    pair = os.pread(fd, 8, 0x91C188)
    hits = [os.path.basename(f) for f in saves() if open(f, "rb").read()[-228:-12] == blob]
    # The byte-for-byte equality is the claim; the match must also DISCRIMINATE (some saves
    # carry a different view state), so 1 <= len(hits) < len(saves).  "exactly one" was this
    # script's own false premise: 7 saves share one view state because they were written in
    # one session without scrolling -- see evidence/m245_tail_legs.txt.
    good = 1 <= len(hits) < len(saves()) and len(blob) == 216
    return good, ("pid=%d TracerPid=0 ptrs=%s live216head=%s live[c188,c18c]=%s matches=%d/%d %s"
                  % (pid, [hex(p & 0xFFFFFFFF) for p in ptrs], blob[:16].hex(), pair.hex(),
                     len(hits), len(saves()), hits))


def g3_tail_timestamp():
    body = body_of(SHARD15, "FUN_00597ce0")

    def find(pat):
        for k, l in enumerate(body):
            if re.search(pat, l):
                return k
        return -1
    a = find(r"local_8 = timeGetTime\(\)")
    b = find(r"FUN_00596850\(iVar2,1\)")
    c = find(r"FUN_0064c9a0\(&local_8,4,1,iVar2\)")
    rec = []
    for f in saves():
        d = open(f, "rb").read()
        rec.append((os.path.getmtime(f), struct.unpack("<I", d[-4:])[0], os.path.basename(f)))
    rec.sort()
    n_same, viol = 0, []
    for i in range(len(rec) - 1):
        m0, v0, n0 = rec[i]
        m1, v1, n1 = rec[i + 1]
        dm = m1 - m0
        if dm <= 120:
            n_same += 1
            if abs((v1 - v0) - dm * 1000) > 2500:
                viol.append("%s->%s dt=%ds dv=%dms" % (n0, n1, dm, v1 - v0))
    byval = {}
    for m, v, n in rec:
        byval.setdefault(v, []).append(m)
    copies = [(hex(v), max(ts) - min(ts), len(ts)) for v, ts in byval.items()
              if len(ts) > 1 and max(ts) - min(ts) > 60]
    good = a >= 0 and b > a and c > b and n_same >= 3 and not viol and len(copies) >= 1
    return good, ("timeGetTime@%d codec@%d trailing-write@%d; same-session pairs=%d violations=%s; "
                  "one dword many mtimes=%s" % (a, b, c, n_same, viol[:3], copies[:3]))


def g4_stride_sites():
    funcs = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "ghidra_out", "shard_*.c"))):
        cur = None
        for i, l in enumerate(open(p, errors="replace"), 1):
            if l.startswith("// ==== FUN"):
                cur = l.split()[2]
            elif cur and "DAT_0092ae18" in l:
                funcs.setdefault(cur, []).append((os.path.basename(p), i, l.strip()))
    info, n_acc, other = {}, 0, []
    for fn in sorted(funcs):
        src = SHARD14 if fn.startswith("FUN_0058") else SHARD15
        try:
            txt = "\n".join(body_of(src, fn))
        except StopIteration:
            txt = " ".join(r[2] for r in funcs[fn])
        uses_stride = "DAT_0092ad9c >> 1" in txt
        blob_only = "DAT_0092ada4" in txt or "FUN_0064a7f0" in txt
        info[fn] = ("stride6" if uses_stride else "-") + ("/plus1" if "(DAT_0092ad9c + 1) / 2" in txt
                                                         else "-") + ("/blob" if blob_only else "")
        if uses_stride:
            n_acc += 1
        elif not blob_only:
            other.append(fn)
    cnt7 = sum(1 for p in glob.glob(os.path.join(ROOT, "ghidra_out", "shard_*.c"))
               for l in open(p, errors="replace") if "(DAT_0092ad9c + 1) / 2" in l)
    good = n_acc == 2 and cnt7 == 1 and not other
    return good, "funcs=%s stride6-funcs=%d non-accessor-non-blob=%s (Rw+1)/2 sites image-wide=%d" % (
        info, n_acc, other, cnt7)


def g5_residue():
    rows, bad = [], []
    for f in saves():
        w, h, rw, rh, off, reg = dims_and_region(open(f, "rb").read(), MAP_HDR_OFF)
        rows.append((os.path.basename(f), rw, rh, reg, addressable(rw, rh)))
    for f in MAPS:
        w, h, rw, rh, off, reg = dims_and_region(open(f, "rb").read(), 15)
        rows.append((os.path.basename(f), rw, rh, reg, addressable(rw, rh)))
    n17 = 0
    for name, rw, rh, reg, cells in rows:
        ncells, slack = len(cells), len(reg) - len(cells)
        contig = sorted(cells) == list(range(ncells))
        tail = reg[ncells:] if slack > 0 else b""
        clean = b"\xcd" not in reg[:ncells]
        is_save = name.endswith(".SAV")
        if is_save and contig and slack == 12 and tail == b"\xcd" * 12 and clean:
            n17 += 1
        if not contig or not clean or tail != b"\xcd" * slack or (not is_save and slack != 0):
            bad.append("%s rw=%d rh=%d len=%d contig=%s slack=%d tail=%s 0xcd-in-written=%s"
                       % (name, rw, rh, len(reg), contig, slack, tail.hex()[:24], not clean))
    good = not bad and n17 == len(saves())
    return good, ("saves: addressable 0..78 contiguous, slack 12 == 0xcd, no 0xcd in 0..78 -> %d/%d; "
                  ".MP (rw even) slack 0; bad=%s" % (n17, len(saves()), bad[:3]))


GATES = [("G1 216-B leg = 9 rows x 6 view fields (codec loop + FUN_00596620 offsets + row ids)",
          g1_codec_leg),
         ("G2 the live 9 view objects' 6 fields == the 216 B of >=1 save and NOT of all 17",
          g2_live_readback),
         ("G3 trailing dword == the timeGetTime() dword written after the codec, not at file write",
          g3_tail_timestamp),
         ("G4 every DAT_0092ae18 accessor indexes with Rw>>1; (Rw+1)/2 appears only as the length",
          g4_stride_sites),
         ("G5 builder write set == 0..78 at 64x64; bytes 79..90 are 0xcd residue in 17/17 saves",
          g5_residue)]


def main():
    lines, ok = [], 0
    for name, fn in GATES:
        try:
            good, detail = fn()
        except Exception as exc:
            good, detail = False, "EXC %s: %s" % (type(exc).__name__, exc)
        ok += 1 if good else 0
        lines.append("%s %s\n    %s" % ("PASS" if good else "FAIL", name, detail))
        print(lines[-1])
    lines.append("\nSUMMARY %d/%d gates on %d saves + 2 .MP\n" % (ok, len(GATES), len(saves())))
    with open(EVID, "w") as f:
        f.write("\n".join(lines))
    try:
        os.chmod(EVID, 0o644)
    except OSError:
        pass
    print("SUMMARY %d/%d" % (ok, len(GATES)))
    if ok == len(GATES):
        print("PASS M245: %d/%d gates" % (ok, len(GATES)))
    return 0 if ok == len(GATES) else 1


if __name__ == "__main__":
    sys.exit(main())
