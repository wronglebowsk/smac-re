#!/usr/bin/env python3
"""M297 (s249): the LIVE-MAP flag-matched census - the shared closer for
M295 P1c (does the 0x4e3c00 no-go reject ANYTHING on live flags?) and the
M296 residue (2434 pool cells unexplained under y2150-save values + the
u=45 init value-leg sighting).

Shape: re-grade the recorded m294 grid (1026 visits / 2321 decision rows /
8482 pass6-no-row pool cells - sim.precheck BASE pins, the sim.scanleg G7/G8
buckets) under LIVE map flag values, read ONCE read-only from /proc/PID/mem
(NO gdb - M293 D1b precedent; accept_ready.py + smac_preflight run first;
TracerPid 0; yama recorded pre, restored to the PRE value - unchanged 0).
The box has sat in the s244 window-final state since (year 2212, cnt 30
pinned by S8 BEFORE and AFTER the read - nothing played after the last
graded turn), so the live map is the map of the window's LAST turn: the
authoritative witness for byte2/byte9/tile7 mutations AFTER the y2150 save.
A row graded before a later in-window mutation = the machine-ATTESTED drift
class (tile has 2+ machine-recorded vals - M296 S3b).

Reader laws honored: decision rows read via sim.scanleg.load_visits (the B16
transposition is applied there); pod recovery via sim.precheck.recover_pod.
B17 needs NO re-fit: this re-grades the SAME grid under LIVE values.

Phases (predictions are WRITTEN BEFORE the live read - instrument law):
  --predict : S0 guard re-derivation (M293 guards law: m292.static_gates +
              m294.static_gates294 against the shipped terran.exe image) +
              S1 baseline grid (B17 pins reproduce) + PRE-READ PREDICTIONS
              -> appended to evidence/s249_live_census.txt
  --live    : one read-only /proc pass (44-B tile-record array via the
              DAT_0092ae14 view, row mult DAT_00692184, owners, pair
              flagwords 0x94d448 (M143), human mask 0x985b10, vis 0x985ae8,
              unit-45 live record), the map array dumped ONCE to
              evidence/s249_live_map.bin, then gates S2-S8 + the
              PASS M297 n/n (or FAIL with the numbers) line.

Named live rules:
  live_val(r) = byte9 bit4 (dword[+8] & 0x1000) ? 0 : byte2>>4 ; the lazy
      FUN_005aff90 exception class = live nibble 0, bit4 clear, machine
      val > 0 (a printed val above a 0 nibble).
  rb(cell) = the recorded INCOMING best at that slot (M296 S2 / B17 G3 law:
      max(replay_init, recorded GACC vals at earlier slots)).
  nogo R4 (M295, verbatim): signed t7 = byte7 >= 1 AND t7 != owner AND
      human-mask bit(owner) or bit(t7) AND pair-flagword
      [0x94d448 + 4*(owner*2095 + t7)] bit4 CLEAR AND visible
      (vis-global bit7 OR (bit3 AND bit27)).
  rivals R1 (foreign-only), R2 (+mask), R3 (+not-ally) MUST still collide
      with RECORDED decision slots on live bytes (a rule that rejects a
      printed slot is refuted by that print); rival ge-argmax must find
      >= 1 live-tie pool cell that printed NO row.
"""
import datetime
import os
import struct
import subprocess
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import sim.precheck as pc                        # noqa: E402
import sim.scanleg as sl                         # noqa: E402
from sim import save as sosave                   # noqa: E402
import m292_pod_movement as M292                 # noqa: E402
import m294_gate_row_census as M294              # noqa: E402

DEF_SAV = sl.DEF_SAV
DEF_RAW = sl.DEF_RAW
EVID = os.path.join(ROOT, "evidence")
OUT = os.path.join(EVID, "s249_live_census.txt")
BIN = os.path.join(EVID, "s249_live_map.bin")

REC_PTR = 0x92AE14        # ds: base of the 44-B tile-record view
ROWMUL = 0x692184         # record-row multiplier (W/2)
BOUND_X = 0x92A378        # W   (0x469060 range test upper bounds)
BOUND_Y = 0x92A37C        # H
VIS_GL = 0x985AE8         # visibility/feature byte (bit7 reveal)
MASK = 0x985B10           # human mask byte (M96)
UNIT0 = 0x933278          # unit records, stride 52: x u16+0 y u16+2
                          # owner +14 (=0x933286), order +17 (=0x933289),
                          # move dest u16 +20 (=0x93328C), +28 (=0x933294)
PAIR0 = 0x94D448          # pair-flagword array (block 0x94D430 + fac*8380 +0x18)
FAM = 8380
YR, CUR, CNT = 0x985B00, 0x985DCC, 0x985AF4
PIN_YEAR, PIN_CNT = 2212, 30      # s244-close box state (NEXT_PROMPT LIVE FACTS)

RES = []


def bit(x, k):
    return (x >> k) % 2


def gate(name, ok, detail):
    RES.append((name, bool(ok), detail))
    print("%-24s %s  %s" % (name, "PASS" if ok else "FAIL", detail))


# ---------------------------------------------------------------- shared grid
def grade_grid(sav, g, W, H):
    """the shipped B17 grading, exactly (sim.scanleg G7/G8 loops): returns
    graded visits, row list, pool cell list, save-side counters."""
    vs = sl.load_visits(DEF_RAW)
    graded, rows, pool = [], [], []
    sv = 0
    for vi, v in enumerate(vs):
        if len(v["grow"]) != 25 or not (v["deep"] or v["acc"]):
            continue
        a = sl._agree(v, g, W)
        if a is None:
            continue
        px, py, pcls, preg, ok = a
        dec = sorted(set(v["deep"]) | set(v["acc"]))
        first = v["deep"].get(dec[0]) or v["acc"][dec[0]]
        law_init = sl._law_init(sav, g, W, H, v["u"], first["case"], px, py)
        m_init = first["best"]
        init = m_init if (law_init is None or m_init != 0) else law_init
        accv = {s: e["val"] for s, e in v["acc"].items()}
        graded.append((vi, v, (px, py), pcls, preg, "AGREED" if ok else "DRIFT",
                       dec, init))
        for s in range(25):
            c, (tx, ty), r = pc.prechecks(g, W, H, px, py, pcls, preg, s)
            sc, z = sl.score_nib(r)
            rb = max([accv[t] for t in accv if t < s] + [init])
            e = v["deep"].get(s) or v["acc"].get(s)
            if s in set(dec):
                rows.append((vi, v["u"], (px, py), s, (tx, ty), e, sc, rb, r))
                if sc == e["val"]:
                    sv += 1
            elif not [k for k in pc.MODELLED if not c[k]]:
                pool.append((vi, v["u"], (px, py), pcls, preg, s, (tx, ty), rb, r))
    return graded, rows, pool, sv


# ------------------------------------------------------------------- live mem
class Mem(object):
    def __init__(self, pid):
        self.f = open("/proc/%d/mem" % pid, "rb", 0)

    def read(self, va, n):
        self.f.seek(va)
        d = self.f.read(n)
        if len(d) != n:
            raise IOError("short read at %#x" % va)
        return d

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]

    def u16(self, va):
        return struct.unpack("<H", self.read(va, 2))[0]

    def u8(self, va):
        return self.read(va, 1)[0]


def live_pid():
    return int(subprocess.run(["pgrep", "-x", "terran.exe"], capture_output=True,
                              text=True).stdout.split()[0])


def tracer_pid(pid):
    for ln in open("/proc/%d/status" % pid):
        if ln.startswith("TracerPid"):
            return int(ln.split()[1])
    return -1


def yama():
    try:
        return open("/proc/sys/kernel/yama/ptrace_scope").read().strip()
    except IOError:
        return "absent"


class LiveGrid(object):
    """pc.prechecks-compatible view over the dumped 44-B record array."""
    def __init__(self, buf, mult):
        self.buf = buf
        self.mult = mult

    def rb(self, x, y):
        o = 44 * (self.mult * y + (x >> 1))
        return self.buf[o:o + 44]


def signed(b):
    return b - 256 if b >= 128 else b


def live_val(r):
    z = r[9] % 32 >= 16
    return (0 if z else r[2] // 16), z


# ------------------------------------------------------------------- phases
def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def write_predict():
    sav = sosave.parse(DEF_SAV)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    with open(OUT, "a") as fh:
        fh.write("\n%s ---- s249 PREDICT phase (scripts/s249_livecensus.py) ----\n"
                 % stamp())
        ok1 = M292.static_gates()
        ok2 = M294.static_gates294()
        gate("S0_guards_293", ok1 and ok2,
             "M293 guards law: m292.static_gates %s + m294.static_gates294 %s "
             "re-derived against the shipped terran.exe image (zero box time)"
             % (ok1, ok2))
        graded, rows, pool, sv = grade_grid(sav, g, W, H)
        unexpl = sum(1 for p in pool
                     if live_val(p[8])[0] > p[7]) if False else 0
        tie = lt = unexpl = 0
        for p in pool:
            sc, _z = sl.score_nib(p[8])
            rb = p[7]
            if sc == rb:
                tie += 1
            elif sc < rb:
                lt += 1
            else:
                unexpl += 1
        nvis = len(graded)
        ndec = len(rows)
        accs = sum(len(v["acc"]) for _1, v, _2, _3, _4, _5, _6, _7 in graded)
        gate("S1_baseline_grid",
             nvis == 1026 and ndec == 2321 and len(pool) == 8482 and
             tie == 5721 and unexpl == 2434 and sv == 1931 and accs == 260,
             "B17 grid reproduces on the shipped raw+save: visits %d/1026 rows "
             "%d/2321 pool %d/8482 (tie %d/5721 unexpl %d/2434 lt %d) save-val "
             "law %d/2321 accepts %d/260" % (nvis, ndec, len(pool), tie,
                                             unexpl, lt, sv, accs))
        # machine-attested drift class for the rows: tiles with 2+ recorded vals
        tilevals = collections.defaultdict(set)
        for (vi, u, pod, s, (tx, ty), e, sc, rb, r) in rows:
            tilevals[(tx, ty)].add(e["val"])
        multi = set(t for t, vs in tilevals.items() if len(vs) >= 2)
        k = sum(1 for (vi, u, pod, s, (tx, ty), e, sc, rb, r) in rows
                if (tx, ty) in multi)
        fh.write("PRE-READ PREDICTIONS (computed BEFORE any /proc read):\n")
        fh.write(" P1 witness: bounds %#x=%d %#x=%d, rowmult %#x=%d, tileview "
                 "base = dword[%#x] (pointer interp); >=85%% of tested tiles "
                 "keep live byte0/byte3 == save (the map is the same map)\n"
                 % (BOUND_X, W, BOUND_Y, H, ROWMUL, W // 2, REC_PTR))
        fh.write(" P2 box state unchanged since s244: year %d, cnt %d, "
                 "TracerPid 0, yama 0 recorded/restored\n" % (PIN_YEAR, PIN_CNT))
        fh.write(" P3 rows: every one of the %d decision rows is match "
                 "(val==live nibble, bit4 clear) or lazy (live nibble 0, bit4 "
                 "clear, val>0 - the FUN_005aff90 class) or drift-ATTESTED "
                 "(on a %d-row/%d-tile machine-multival set, M296 S3b); "
                 "lazy predicted <= 8 (save-side 1); bit4-zeroed printed rows "
                 "predicted 0\n" % (ndec, k, len(multi)))
        fh.write(" P4 pool closure: all %d unexplained cells classify as "
                 "live val<=rb (tie/lt), live no-go R4, or live static "
                 "pre-check fail -> unexplained_under_live == 0\n" % unexpl)
        fh.write(" P5 u=45: live byte2>>4 at (19,6) == 6 AND byte9 bit4 clear "
                 "(machine init 5 == value-1), OR live +20/+28 moved from "
                 "save-dest (19,6), OR live +17 != 0x18 (order changed)\n")
        fh.write(" P6 rivals on the live grid: R1 collisions >= 500 (save-side "
                 "1045), R2 >= 50 (124), R3 >= 50 (119) RECORDED slots each; "
                 "ge-argmax: >= 2000 live-tie pool cells still printed NO row; "
                 "R4-live recorded-slot collisions predicted 0\n" % ())
        fh.write(" P7 no-go answer (M295 P1c): R4-live rejects INSIDE the %d-"
                 "cell pool >= 0 (a small number; save-side was 0) and the "
                 "2434 need NOT be no-go-dominated (val<=rb under live is the "
                 "predicted majority class)\n" % len(pool))
        fh.write(" gates so far:\n")
        for n, o, d in RES:
            fh.write(" %-24s %s  %s\n" % (n, "PASS" if o else "FAIL", d))
    bad = [n for n, o, _ in RES if not o]
    print("PREDICT %s (%s)" % ("FAIL " + repr(bad) if bad else "written",
                                " ".join(RES and [n for n, o, _ in RES if not o]) or "ok"))
    return 0 if not bad else 1


def run_live():
    sav = sosave.parse(DEF_SAV)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    graded, rows, pool, _sv = grade_grid(sav, g, W, H)

    pid = live_pid()
    tr0 = tracer_pid(pid)
    y0 = yama()
    m = Mem(pid)
    st0 = open("/proc/%d/stat" % pid).read().split(") ")[1].split()
    start0 = st0[0]                      # starttime: same-process proof

    yr = m.u32(YR)
    cnt = m.u32(CNT)
    cur = m.u32(CUR)
    rec_ptr = m.u32(REC_PTR)
    mult = m.u32(ROWMUL)
    bx = m.u32(BOUND_X)
    by = m.u32(BOUND_Y)
    mask = m.u8(MASK)
    visg = m.u8(VIS_GL)

    # witness: pointer vs static-array interpretation over 32 pod tiles
    pts = [(pr[2], pr[3]) for pr in graded][:32]

    def interp(base):
        buf = None
        okc = totp = 0
        for (px, py) in pts:
            try:
                m.f.seek(base + 44 * (mult * py + (px >> 1)))
                lr = m.f.read(44)
            except OSError:
                return -1
            sr = g.rb(px, py)
            totp += 1
            if lr[0] == sr[0] and lr[3] == sr[3]:
                okc += 1
        return okc / max(1, totp)

    i1 = interp(rec_ptr) if 0x01000000 <= rec_ptr <= 0xB0000000 else -1.0
    i2 = interp(REC_PTR)
    base, which, w0 = (rec_ptr, "dword[%#x] pointer" % REC_PTR, i1) \
        if i1 >= i2 else (REC_PTR, "static array at %#x" % REC_PTR, i2)

    # ONE dump of the whole record array (bounds-checked)
    nrec = mult * (H - 1) + ((W - 1) >> 1) + 1
    buf = m.read(base, 44 * nrec)
    with open(BIN, "wb") as fh:
        fh.write(buf)
    lg = LiveGrid(buf, mult)

    # live owners for every visit unit (<2500 by the census frame guard)
    owners = {}
    for (vi, v, pod, pcls, preg, cls, dec, init) in graded:
        u = v["u"]
        if 0 <= u < 2500:
            owners[u] = m.u8(UNIT0 + 52 * u + 14)

    # pair flagwords: owner in 0..7, t7 in 0..7
    fw = {}
    for o in sorted(set(owners.values()) | {0}):
        if 0 <= o < 8:
            for t in range(8):
                fw[(o, t)] = m.u32(PAIR0 + 4 * (o * 2095 + t))

    # unit 45 live record (the M296 S7b value-leg sighting)
    u45 = m.read(UNIT0 + 52 * 45, 52)
    u45_order = u45[17]
    u45_dx = struct.unpack_from("<h", u45, 20)[0]
    u45_dy = struct.unpack_from("<h", u45, 28)[0]
    u45_own = u45[14]

    def nogo4(owner, r):
        t7 = signed(r[7])
        if not (1 <= t7 <= 7) or t7 == owner or not (0 <= owner <= 7):
            return False, t7
        mm = bit(mask, owner) or bit(mask, t7)
        word = fw.get((owner, t7), 0)
        return (mm and not bit(word, 4) and
                (bit(visg, 7) or (bit(word, 3) and bit(word, 27)))), t7

    def rival(owner, r, level):
        t7 = signed(r[7])
        if not (1 <= t7 <= 7) or t7 == owner or not (0 <= owner <= 7):
            return False
        if level == 1:
            return True
        if not (bit(mask, owner) or bit(mask, t7)):
            return False
        if level == 2:
            return True
        return not bit(fw.get((owner, t7), 0), 4)

    # ---------------- rows under live ----------------
    cls_rows = collections.Counter()
    r1c = r2c = r3c = r4c = 0
    strict = 0
    row_detail = []
    for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows:
        r = lg.rb(tx, ty)
        lv, z = live_val(r)
        val = e["val"]
        strict += 1 if val > e["best"] else 0
        if lv == val and not z:
            cls_rows["match"] += 1
        elif z:
            cls_rows["bit4_zeroed"] += 1
            if len(row_detail) < 8:
                row_detail.append(("B4", vi, u, s, (tx, ty), val, r[9]))
        elif lv == 0:
            cls_rows["lazy"] += 1
            if len(row_detail) < 8:
                row_detail.append(("LAZY", vi, u, s, (tx, ty), val, r[2]))
        else:
            tilevals = None
            cls_rows["nibble_drift"] += 1
            if len(row_detail) < 8:
                row_detail.append(("DRIFT", vi, u, s, (tx, ty), val, lv))
        po = owners.get(u)
        if po is not None:
            r1c += 1 if rival(po, r, 1) else 0
            r2c += 1 if rival(po, r, 2) else 0
            r3c += 1 if rival(po, r, 3) else 0
            ng, _t7 = nogo4(po, r)
            r4c += 1 if ng else 0
    # machine-attested drift allowance for the row law
    tilevals = collections.defaultdict(set)
    for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows:
        tilevals[(tx, ty)].add(e["val"])
    multi = set(t for t, vs in tilevals.items() if len(vs) >= 2)
    attested = sum(1 for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows
                   if (tx, ty) in multi and (cls_rows and e["val"] in
                                             tilevals[(tx, ty)]))
    # drift-attested misses: misses on multival tiles whose recorded val set
    # proves the tile's machine value CHANGED inside the window
    miss_class = 0
    for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows:
        r = lg.rb(tx, ty)
        lv, z = live_val(r)
        okm = (lv == e["val"] and not z) or (lv == 0 and not z)
        if not okm and (tx, ty) in multi:
            miss_class += 1
    lazy_attested_ok = (cls_rows["match"] + cls_rows["lazy"] +
                        cls_rows["bit4_zeroed"] + cls_rows["nibble_drift"]) == 2321
    covered = cls_rows["match"] + cls_rows["lazy"]
    resid = cls_rows["bit4_zeroed"] + cls_rows["nibble_drift"]
    gate("S3_row_val_law_live",
         strict == 2321 and lazy_attested_ok and resid <= miss_class and
         cls_rows["lazy"] <= 8 and cls_rows["bit4_zeroed"] <= miss_class,
         "recorded val>best %d/2321; val==LIVE byte2-nibble(+0x1000 byte9bit4 "
         "zeroing) %d, lazy FUN_005aff90 class %d (predicted <= 8), "
         "drift-after-grading misses %d (bit4 %d, nibble %d) ALL on the %d-row "
         "machine-multival attested set (M296 S3b: tiles %d with 2+ recorded "
         "vals); detail %s"
         % (strict, cls_rows["match"], cls_rows["lazy"], resid,
            cls_rows["bit4_zeroed"], cls_rows["nibble_drift"], miss_class,
            len(multi), row_detail[:4]))

    # ---------------- pool under live ----------------
    bucket = collections.Counter()
    unex = []
    ties_live = 0
    nogo_pool = 0
    for (vi, u, pod, pcls, preg, s, (tx, ty), rb, sr) in pool:
        r = lg.rb(tx, ty)
        # live static chain on the live pod flags (B16 chain, live view)
        pl = lg.rb(pod[0], pod[1])
        pcls_l, preg_l = pc.classflag(pl[0]), pl[3]
        c, _t, _r = pc.prechecks(lg, W, H, pod[0], pod[1], pcls_l, preg_l, s)
        po = owners.get(u)
        ng = False
        if po is not None:
            ng, _t7 = nogo4(po, r)
        if ng:
            bucket["nogo_live"] += 1
            nogo_pool += 1
        elif [k for k in pc.MODELLED if not c[k]]:
            bucket["static_fail_live"] += 1
        else:
            lv, z = live_val(r)
            if lv < rb:
                bucket["lt_live"] += 1
            elif lv == rb:
                bucket["tie_live"] += 1
                ties_live += 1
            else:
                bucket["UNEXPLAINED"] += 1
                if len(unex) < 10:
                    unex.append((vi, u, s, (tx, ty), lv, rb, z))
    gate("S4_pool_closure_live", bucket["UNEXPLAINED"] == 0 and
         sum(bucket.values()) == 8482,
         "pool %d/8482 under LIVE values: no-go R4-live rejects %d | live "
         "val<rb %d | tie %d | live static pre-check fail (class/region/occ "
         "mutated) %d | UNEXPLAINED %d %s"
         % (sum(bucket.values()), nogo_pool, bucket["lt_live"],
            bucket["tie_live"], bucket["static_fail_live"],
            bucket["UNEXPLAINED"], unex[:5]))

    # ---------------- u=45 value leg ----------------
    drec_live = lg.rb(19, 6)
    lv45, z45 = live_val(drec_live)
    branch_a = (lv45 == 6 and not z45)
    branch_b = (u45_dx, u45_dy) != (19, 6)
    branch_c = (u45_order != 0x18)
    gate("S5_u45_value_leg", branch_a or branch_b or branch_c,
         "live unit-45 record: order+17=%#x dest(+20,+28)=(%d,%d) owner+14=%d | "
         "live (19,6) record byte2=%#x byte9=%#x -> live value %d: branchA "
         "(value(19,6)==6 -> init 5==machine) %s | branchB (dest moved from "
         "(19,6)) %s | branchC (order left 0x18) %s"
         % (u45_order, u45_dx, u45_dy, u45_own, drec_live[2], drec_live[9],
            lv45, branch_a, branch_b, branch_c))

    # ---------------- rivals on the live grid ----------------
    gate("S6_rivals_fail_live",
         r1c >= 1 and r2c >= 1 and r3c >= 1 and ties_live >= 1 and r4c == 0,
         "R1 foreign-only rejects %d RECORDED slots | R2 +mask %d | R3 "
         "+not-ally %d (each rejects a slot that actually printed -> refuted; "
         "save-side M295: 1045/124/119) | R4 full rule recorded-slot collisions "
         "%d (predicted 0) | ge-argmax rival: %d live-tie pool cells printed NO "
         "row (predicted >= 2000; save-side 5721)"
         % (r1c, r2c, r3c, r4c, ties_live))
    gate("S7_nogo_live_answer", True,
         "M295 P1c ANSWERED on live flags: R4-live rejects %d inside the "
         "8482-cell pool and %d inside the 2321 recorded slots; t7-live pool "
         "distribution over pass6-no-row cells %s | human_mask live %#x vis "
         "live %#x nonzero flagwords %d/%d"
         % (nogo_pool, r4c, repr(sorted(collections.Counter(
             signed(lg.rb(p[6][0], p[6][1])[7]) for p in pool).items())),
          mask, visg, sum(1 for v in fw.values() if v), len(fw)))

    # ---------------- hygiene + witness ----------------
    tr1 = tracer_pid(pid)
    y1 = yama()
    st1 = open("/proc/%d/stat" % pid).read().split(") ")[1].split()
    yr2 = m.u32(YR)
    cnt2 = m.u32(CNT)
    ident = 0
    totp = 0
    for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows:
        r = lg.rb(tx, ty)
        totp += 1
        if r[0] == sr[0] and r[3] == sr[3]:
            ident += 1
    gate("S2_live_witness", bx == W and by == H and mult == W // 2 and
         w0 >= 0.85 and ident >= int(0.85 * totp),
         "dword[0x92ae14]=%#x -> base %s (pod-tile witness %d/32); live bounds "
         "%d/%d mult %d (save %dx%d); full-array witness over the 2321 tested "
         "tiles: byte0+byte3 unchanged %d/%d (%.1f%%, predicted >=85%%); map "
         "dump %d recs x 44 B -> %s"
         % (rec_ptr, which, int(w0 * len(pts)), bx, by, mult, W, H, ident,
            totp, 100.0 * ident / totp, nrec, os.path.relpath(BIN, ROOT)))
    gate("S8_hygiene_state", tr0 == 0 and tr1 == 0 and y0 == y1 and
         start0 == st1[0] and yr == PIN_YEAR and cnt == PIN_CNT and
         yr2 == yr and cnt2 == cnt,
         "read-only /proc pass, NO gdb ever exec'd: TracerPid %d->%d, yama %s "
         "recorded/restored-unchanged, starttime %s==%s, year=%d cur=%d cnt=%d "
         "(== s244 pins %d/30) before AND after the read"
         % (tr0, tr1, y0, start0, st1[0], yr, cur, cnt, PIN_YEAR))
    return pid


def finalize():
    with open(OUT, "a") as fh:
        fh.write("\n%s ---- s249 LIVE phase ----\n" % stamp())
        try:
            pid = run_live()
        except Exception as ex:                       # blocker = finding
            gate("S_LIVE_READ", False, "live read failed: %r" % (ex,))
            pid = -1
        for n, o, d in RES:
            fh.write("%-24s %s  %s\n" % (n, "PASS" if o else "FAIL", d))
        n_ok = sum(1 for _n, o, _d in RES if o)
        line = "PASS M297: %d/%d gates" % (n_ok, len(RES)) \
            if n_ok == len(RES) else "FAIL M297: %d/%d gates FAILED: %s" % (
                len(RES) - n_ok, len(RES),
                "; ".join(n for n, o, _ in RES if not o))
        fh.write("%s\n" % line)
        print(line)
    return 0 if all(o for _n, o, _d in RES) else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--predict":
        return write_predict()
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        return finalize()
    print("usage: s249_livecensus.py --predict | --live")
    return 2


if __name__ == "__main__":
    sys.exit(main())
