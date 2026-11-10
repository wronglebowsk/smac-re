#!/usr/bin/env python3
# M291: the hub FOUNDING scan (FUN_0055f650 0x5638a9-0x563cb3) is a STRICT
# site-value argmax over a 25-entry even-manhattan ring (tables 0x67850c/0x678990:
# center, manhattan-2 diamond, manhattan-4 diamond); score = FUN_0046e770 =
# tile value = rec byte2 high nibble (0 if rec+8 bit 0x1000 set; lazy FUN_005aff90
# when 0); ties keep the closer ring entry; eligibility adds the water/land cat
# flag (top-3-bits of byte0 below 3), rec byte3 == owner-gate, rec+9 bit 0x20
# clear. The footing (dist*10000)/(value+1) shape is REFUTED: no 0x2710 immediate
# in the 54483-B body; distance reaches the law only via FUN_004e3620 writing
# DAT_008f0d34 (nearest-location distance) and the value >= 2*(8 - that) bypass
# gate. Fit vs the m289 golden record: 7/7 recorded sites self-argmax; the
# no-owngate rival loses exactly site 6 (27,29); B10 placeholder 0/7.
# (Byte literals are bytes([...]) lists and the log parse uses split(): the
# session transport unescapes backslashes inside heredocs, so the ship form of
# this gate carries no backslash escapes at all.)
import sys, os, json, struct, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from sim import save as sv

EXE = os.path.join(ROOT, "terran.exe")
IDX = os.path.join(ROOT, "ghidra_out", "index.csv")

def sections(path):
    d = open(path, "rb").read()
    e = struct.unpack_from("<I", d, 0x3c)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    optsz = struct.unpack_from("<H", d, e + 20)[0]
    base = struct.unpack_from("<I", d, e + 52)[0]
    out = []
    o = e + 24 + optsz
    for i in range(nsec):
        name = d[o:o + 8].rstrip(bytes([0])).decode("latin1")
        vsize = struct.unpack_from("<I", d, o + 8)[0]
        vaddr = struct.unpack_from("<I", d, o + 12)[0]
        rsize = struct.unpack_from("<I", d, o + 16)[0]
        raddr = struct.unpack_from("<I", d, o + 20)[0]
        out.append((name, base + vaddr, vsize, raddr, rsize))
        o += 40
    return d, out

D, SECS = sections(EXE)

def section_of(va):
    for sec in SECS:
        (name, sva, vsz, ra, rsz) = sec
        if sva <= va < sva + vsz:
            return sec
    return None

def fbytes(va, n):
    s = section_of(va)
    if s is None:
        return None
    (name, sva, vsz, ra, rsz) = s
    off = va - sva
    if rsz and off + n <= rsz:
        return D[ra + off:ra + off + n]
    return None

def ring_bytes(va, n):
    b = fbytes(va, n)
    if b is not None:
        return b, "file:" + section_of(va)[0]
    pid = int(os.environ.get("SMAC_PID", "0"))
    if not pid:
        for ln in os.popen("pgrep -x terran.exe").read().split():
            pid = int(ln)
            break
    fd = open("/proc/" + str(pid) + "/mem", "rb")
    fd.seek(va)
    b = fd.read(n)
    fd.close()
    return b, "live:pid" + str(pid)

RES = []
def gate(n, ok, detail):
    RES.append(bool(ok))
    print("G%-2d %s  %s" % (n, "PASS" if ok else "FAIL", detail))

# G1: ring loop bounds (cmp eax,0x19 / cmp ebx,0x144), strict-max compare
# (cmp esi,[ebp-0x24] + jle 0x563cb3), best store (mov [ebp-0x24],esi).
b1 = fbytes(0x563cb7, 3)
b2 = fbytes(0x563be8, 6)
b3 = fbytes(0x563c0f, 3)
b4 = fbytes(0x563c11, 6)
b5 = fbytes(0x563caa, 3)
exp4 = (b4 is not None and b4[:2] == bytes([0x0f, 0x8e]) and
        (0x563c11 + 6 + struct.unpack("<i", b4[2:6])[0]) == 0x563cb3)
ok1 = (b1 == bytes([0x83, 0xf8, 0x19]) and
       b2 == bytes([0x81, 0xfb, 0x44, 0x01, 0x00, 0x00]) and
       b3 == bytes([0x3b, 0xf0, 0x0f]) and exp4 and
       b5 == bytes([0x89, 0x75, 0xdc]))
gate(1, ok1, "cmp0x19 %r | cmp0x144 %r | cmpesi-best %r | jle0x563cb3 %r | movbest %r" % (b1, b2, b3, b4, b5))

# G2: value law FUN_0046e770: and-eax-0x1000 to 0-leg; mov dl,[ecx+2]; sar edx,4
c1 = fbytes(0x46e792, 5)
c2 = fbytes(0x46e7a4, 3)
c3 = fbytes(0x46e7a7, 3)
gate(2, c1 == bytes([0x25, 0x00, 0x10, 0x00, 0x00]) and
        c2 == bytes([0x8a, 0x51, 0x02]) and c3 == bytes([0xc1, 0xfa, 0x04]),
     "and0x1000 %r | movdl[ecx+2] %r | sar4 %r" % (c1, c2, c3))

# G3: distance helper FUN_004e3620: 9999 sentinel init, store to DAT_008f0d34
d1 = fbytes(0x4e3631, 7)
d2 = fbytes(0x4e36f5, 6)
gate(3, d1 == bytes([0xc7, 0x45, 0xf8, 0x0f, 0x27, 0x00, 0x00]) and
        d2 == bytes([0x89, 0x0d, 0x34, 0x0d, 0x8f, 0x00]),
     "9999init %r | store0x8f0d34 %r" % (d1, d2))

# G4: REFUTED footing shape - no 0x2710 dword immediate in FUN_0055f650
size = None
for ln in open(IDX):
    p = ln.split(",")
    if p[0] == "0x0055f650":
        size = int(p[2])
        break
body = b""
va = 0x55f650
while va < 0x55f650 + size:
    chunk = fbytes(va, 4096)
    if chunk is None:
        break
    body += chunk
    va += len(chunk)
hits = []
st = 0
while True:
    i = body.find(bytes([0x10, 0x27, 0x00, 0x00]), st)
    if i < 0:
        break
    hits.append(hex(0x55f650 + i))
    st = i + 1
gate(4, bool(size and len(body) > 40000 and not hits), "body %d B read, 0x2710 hits: %s" % (len(body), hits if hits else "none"))

# G5: ring tables (file image if present, else read-only live read): center
# first, exact manhattan-2 and manhattan-4 diamonds, ascending.
bdx, srcx = ring_bytes(0x67850c, 100)
bdy, srcy = ring_bytes(0x678990, 100)
dx = struct.unpack("<25i", bdx)
dy = struct.unpack("<25i", bdy)
d2set = set((dx[i], dy[i]) for i in range(9)) - set([(0, 0)])
want2 = set((a, b) for a in range(-2, 3) for b in range(-2, 3) if abs(a) + abs(b) == 2)
d4set = set((dx[i], dy[i]) for i in range(9, 25))
want4 = set((a, b) for a in range(-4, 5) for b in range(-4, 5) if abs(a) + abs(b) == 4)
mono = all(abs(dx[i]) + abs(dy[i]) <= abs(dx[i + 1]) + abs(dy[i + 1]) for i in range(24))
gate(5, (dx[0], dy[0]) == (0, 0) and d2set == want2 and d4set == want4 and mono,
     "rings %s/%s | center(0,0) | m2diamond %s | m4diamond %s | ascending %s" % (srcx, srcy, d2set == want2, d4set == want4, mono))

S = sv.parse(os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))
W, H = S.width, S.height

def rb(x, y):
    return S.data[S.grid_off + 44 * ((W // 2) * y + (x >> 1)):][:44]

def catflag(x, y):  # top-3 bits of byte0: cat = byte0 // 32; water-class = cat below 3
    return 1 if rb(x, y)[0] // 32 < 3 else 0

def val(x, y):
    return rb(x, y)[2] // 16

def own3(x, y):
    return rb(x, y)[3]

def blocked(x, y):  # rec+9 bit 0x20
    return (rb(x, y)[9] // 32) % 2

found, destroys = [], []
for ln in open(os.path.join(ROOT, "evidence/m289_gdb_raw.log")):
    w = ln.split()
    if len(w) >= 6 and w[0] == "FOUND" and w[1] == "ret=0x4ccbe2":
        try:
            fac = int(w[2].split("=")[1]); x = int(w[3].split("=")[1])
            y = int(w[4].split("=")[1]); cnt = int(w[5].split("=")[1])
            found.append((fac, x, y, cnt))
        except Exception:
            pass
    if len(w) >= 2 and w[0] == "DESTROY" and w[1].startswith("cnt="):
        destroys.append(int(w[1].split("=")[1]))

bases = set()
for i in range(S.found_bases):
    b = S.base(i)
    if b:
        bases.add((b["x"], b["y"]))

def self_argmax(x, y, occ, own_gate=True):
    v, cf, ob, bb = val(x, y), catflag(x, y), own3(x, y), blocked(x, y)
    if bb:
        return False, "center blocked"
    for i in range(1, 25):
        nx, ny = (x + dx[i]) % W, (y + dy[i]) % H
        if catflag(nx, ny) != cf:
            continue
        if own_gate and own3(nx, ny) != ob:
            continue
        if blocked(nx, ny):
            continue
        if (nx, ny) in occ:
            continue
        if val(nx, ny) > v:
            return False, "idx" + str(i) + " at(" + str(nx) + "," + str(ny) + ") val" + str(val(nx, ny))
    return True, ""

# G6: recorded fit - all 7 founding tiles self-argmax over their own ring,
# occupancy grown by earlier foundings.
occ = set(bases)
fits, det = [], []
for (fac, x, y, cnt) in found:
    ok, why = self_argmax(x, y, occ)
    fits.append(ok)
    det.append("fac" + str(fac) + " (" + str(x) + "," + str(y) + "):" + ("ok" if ok else "LOSE " + why))
    occ.add((x, y))
gate(6, sum(fits) == 7 and len(found) == 7, "7/7 strict-argmax | " + " ".join(det))

# G7: rival rules. (a) drop the rec byte3 owner-equality gate: the record must
# falsify it at exactly one site (fac1 (27,29)); (b) B10 placeholder
# first-unoccupied row-major must reproduce 0/7.
occ = set(bases)
nog = []
for (fac, x, y, cnt) in found:
    ok, _ = self_argmax(x, y, occ, own_gate=False)
    nog.append(ok)
    occ.add((x, y))
lose_sites = ["fac" + str(found[k][0]) + "(" + str(found[k][1]) + "," + str(found[k][2]) + ")" for k in range(len(found)) if not nog[k]]
occ = set(bases)
ph = []
for (fac, x, y, cnt) in found:
    first = None
    for yy in range(H):
        for xx in range(W):
            if catflag(xx, yy) == 0 and (xx, yy) not in occ:
                first = (xx, yy)
                break
        if first:
            break
    ph.append(first == (x, y))
    occ.add((x, y))
gate(7, sum(nog) == 6 and sum(ph) == 0, "no-owngate %d/7 loses[%s] | B10-first-unoccupied %d/7" % (sum(nog), " ".join(lose_sites), sum(ph)))

# G8: null discrimination - self-argmax rate on a seeded sample of unoccupied
# land tiles; 7/7 under that null is p = rate^7 below 1e-3.
random.seed(238)
allsites = []
for yy in range(0, H, 5):
    for xx in range(0, W, 5):
        if catflag(xx, yy) == 0 and (xx, yy) not in bases and not blocked(xx, yy):
            allsites.append((xx, yy))
sample = random.sample(allsites, min(len(allsites), 150))
hh = 0
for (xx, yy) in sample:
    ok, _ = self_argmax(xx, yy, bases)
    if ok:
        hh += 1
rate = hh / float(len(sample))
p = rate ** 7
gate(8, rate <= 0.5 and p < 1e-3, "null rate %d/%d = %.3f | binom p(7/7|null) %.2e" % (hh, len(sample), rate, p))

# G9: ledger/turn context re-asserted from the golden trace.
curve = []
for ln in open(os.path.join(ROOT, "evidence/trace_m289_20261110_071759.jsonl")):
    r = json.loads(ln)
    if r.get("type") == "start":
        continue
    curve.append((r["turn"], r["state_after"]["n_bases"]))
rises = []
prev = curve[0][1]
for t, n in curve:
    if n > prev:
        rises.append(t)
    prev = n
end = curve[-1][1]
gate(9, bool(curve) and end == 23 and destroys == [21, 24] and len(rises) == 6,
     "endpoint %d = 18+7-2 | DESTROY cnts %s | rise turns %s" % (end, destroys, rises))

# G10: M290 legs re-asserted: land cat 3-6 in the 44-B record view, none on a save base tile.
okland = all(3 <= rb(x, y)[0] // 32 <= 6 and (x, y) not in bases for (fac, x, y, cnt) in found)
gate(10, okland, "all 7 recorded sites land-cat (44-B record view), none on a save base tile")

n = sum(RES)
if n == len(RES):
    print("PASS M291: %d/%d" % (n, len(RES)))
else:
    print("FAIL M291: %d/%d" % (n, len(RES)))
sys.exit(0 if n == len(RES) else 1)
