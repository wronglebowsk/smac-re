"""sim.podscan - rung B14: the hub founding SCAN (M291) and the esi ring-index
dispatch with the pod WALK leg (M292, s240-corrected) as ONE executable - the
piece B13 DECLARED and the two ANALYSE fires after it settled.

B13 (sim/hubfound.py) made the founding dispatch executable but took the
scan's choice as INPUT ("the walk is the next ANALYSE frontier"). M291 settled
the scan: FUN_0055f650 0x5638a9-0x563cb3 is a STRICT site-value argmax over a
25-entry even-manhattan ring (tables .rdata 0x67850c dx / 0x678990 dy: entry
0 own tile, 1-8 the manhattan-2 diamond, 9-24 the manhattan-4 diamond), score
= rec byte2 high nibble (FUN_0046e770), eligibility = same water/land cat flag,
rec byte3 owner-equality, rec+9 bit 0x20 clear, not already occupied; ties
keep the closer entry (strict cmp/jle). M292 settled the dispatch keys on the
scan's RING ENTRY INDEX esi: 0 -> the founder (or msg 0x2408 with the second
gate [ebp-0xa4], s240), 1..8 -> continue with NO order, >=9 -> issue order
0x62 at the wrapped ring tile (FUN_00469010) = the pod WALK.

This module lifts that law from scripts/m291_pod_scan.py +
scripts/m292_pod_movement.py into the sim and pairs it with RECORDED evidence
only:
  * the ring literals vs the recorded file-image dump
    evidence/b14_ring_table.txt (provenance scripts/b14_ring_dump.py);
  * the M289 golden: all 7 recorded m289 foundings are self-argmax (esi == 0)
    under this scan on the grown occupancy - rivals fail the SAME fit
    (no owner-gate loses exactly fac1 (27,29); B10's placeholder 0/7);
  * the M292 live census log (26 turns, 29 DISP rows): the model's dispatch
    table partitions them 9 found / 9 continue / 11 walk / 0 msg, every ISS
    row's recorded target-X equals walk_target(x, esi)[0] (11/11), and the
    table-swap rival reproduces 0 of 11.
  * the SELECTION property (s241 review): scan_esi equals a brute-forced
    argmax on a fixed sample, whose tiles provably discriminate argmax from
    a first-better rule; scan candidates are X-wrapped (0x469010) but Y are
    bounds-checked (0x469060) - Y never wraps.

DECLARED UNMODELED (the fits passed without them, exactly as in M291): the
0x94e5a8/0x94eca8 per-site gate tables (bypassed when value >= 2*(8-nearest)),
the 0x4e3c00 no-go, the rec+8 bit-0x1000 zero-leg and lazy FUN_005aff90 value
fallback (every recorded fit tile carries a nonzero nibble), and the ISS
instrument printf's only the target X at 0x563e3b (scripts/m292_pod_movement.
py bp list) - the target Y law is the same table byte-read, static-gated only.

No /proc, no gdb, no Wine, no game-binary load (the ring provenance is the
recorded dump). Deterministic: two runs give identical report sha256.
"""
import argparse
import hashlib
import os
import subprocess
import sys

from . import save as sosave
from . import hubfound as soh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_LOG = os.path.join(ROOT, "evidence", "m292_gdb_raw.log")
DEF_GOLDEN = os.path.join(ROOT, "evidence", "m289_gdb_raw.log")
DEF_RING = os.path.join(ROOT, "evidence", "b14_ring_table.txt")
DEF_CENSUS = os.path.join(ROOT, "evidence", "m292_pod_movement.txt")
DEF_SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")

# The game's own ring tables, transcribed from the recorded file-image dump
# evidence/b14_ring_table.txt (gate 1 re-checks literals against the dump;
# sim/ never reads terran.exe).
RING_DX = (0, 1, 2, 1, 0, -1, -2, -1, 0,
           2, 2, -2, -2, 1, 3, 3, 1, -1, -3, -3, -1, 4, -4, 0, 0)
RING_DY = (0, -1, 0, 1, 2, 1, 0, -1, -2,
           -2, 2, 2, -2, -3, -1, 1, 3, 3, 1, -1, -3, 0, 0, 4, -4)

M2_DIAMOND = set((a, b) for a in range(-2, 3) for b in range(-2, 3)
                 if abs(a) + abs(b) == 2)
M4_DIAMOND = set((a, b) for a in range(-4, 5) for b in range(-4, 5)
                 if abs(a) + abs(b) == 4)


def load_ring_dump(path):
    """The recorded dump -> (dx tuple, dy tuple), the provenance side of G1."""
    dx, dy = [], []
    for ln in open(path):
        if ln.startswith("#"):
            continue
        w = ln.split()
        if len(w) == 3:
            dx.append(int(w[1]))
            dy.append(int(w[2]))
    return tuple(dx), tuple(dy)


class Grid:
    """The 44-B tile-RECORD view of a save's grid (the M290 trap: the 22-B
    column view is NOT the live category). Fields exactly as M291's fit read
    them: cat flag = byte0 // 32 < 3, value = byte2 // 16 (high nibble),
    owner gate = byte3, blocked = rec+9 bit 0x20."""

    def __init__(self, sv):
        self.sv = sv
        self.W = sv.width
        self.H = sv.height

    def rb(self, x, y):
        rec = (self.W // 2) * y + (x >> 1)
        off = self.sv.grid_off + sosave.REC_LEN * rec
        return self.sv.data[off:off + sosave.REC_LEN]

    def catflag(self, x, y):
        return 1 if self.rb(x, y)[0] // 32 < 3 else 0

    def val(self, x, y):
        return self.rb(x, y)[2] // 16

    def own3(self, x, y):
        return self.rb(x, y)[3]

    def blocked(self, x, y):
        return (self.rb(x, y)[9] // 32) % 2


def scan_esi(g, x, y, occ, own_gate=True):
    """M291's selection executable: the ring ENTRY INDEX of the STRICT
    site-value argmax over ALL eligible entries, ties keeping the closer
    entry. The loop keeps the best VALUE in [ebp-0x24] (init 0) and the best
    INDEX in [ebp-0x84], updating only on strictly greater (0x563c0f cmp +
    0x563c11 jle + 0x563caa store), and 0x563cc3/0x563d0a BAIL on
    best_val==0 or best_idx<0 - so returns None when the game never reaches
    the dispatch, and NO first-better shortcut (s241 Greptile P1#1: the
    game is a full argmax, not first-better).
    X is map-WRAPPED (single-arg wrap helper 0x469010, call at 0x5638b9);
    Y is NEVER wrapped - the raw sum goes to the validity helper 0x469060
    (call at 0x5638d2), whose zero return skips the entry (s241 Greptile
    P1#2, bytes scratch/m574/text.txt 0x5638af-0x5638dc).
    A site is self-argmax exactly when this returns 0."""
    cf, ob = g.catflag(x, y), g.own3(x, y)
    best_val, best_i = 0, None
    for i in range(25):
        nx, ny = (x + RING_DX[i]) % g.W, y + RING_DY[i]
        if not (0 <= ny < g.H):
            continue
        if g.catflag(nx, ny) != cf:
            continue
        if own_gate and g.own3(nx, ny) != ob:
            continue
        if g.blocked(nx, ny):
            continue
        if (nx, ny) in occ:
            continue
        v = g.val(nx, ny)
        if v > best_val:
            best_val, best_i = v, i
    return best_i


def msg_gate(global_flag, owner, human_fac):
    """The s240 second gate [ebp-0xa4] = (ds:0x920434 != 0) AND
    (owner == ds:0x91b5b4) - modeled from its two named inputs."""
    return bool(global_flag != 0 and owner == human_fac)


def dispatch_leg(esi, flag):
    """M292's dispatch table at 0x563d46 (with the M293 correction): the leg
    the hub takes for the scan's ring entry, keyed ONLY on esi."""
    if esi == 0:
        return ("msg", soh.MSG_AUTO_BUILD) if flag else ("found",)
    if 1 <= esi < 9:
        return ("continue",)
    if 9 <= esi <= 24:
        return ("walk",)
    raise ValueError("ring index out of range: " + repr(esi))


def walk_target(x, y, esi, W, H):
    """The ISS leg's target: pod tile + ring entry, map-wrapped
    (FUN_00469010 semantics). The live log records the X field (G6)."""
    return ((x + RING_DX[esi]) % W, (y + RING_DY[esi]) % H)


def golden_founds(path):
    """(fac, x, y, cnt) tuples of the recorded FOUND rows, log order."""
    out = []
    for ln in open(path):
        w = ln.split()
        if len(w) >= 6 and w[0] == "FOUND" and w[1] == "ret=0x4ccbe2":
            d = dict(kv.split("=", 1) for kv in w[2:])
            out.append((int(d["fac"]), int(d["x"]), int(d["y"]),
                        int(d["cnt"])))
    return out


def parse_census(path):
    """The m292 census rows, log order preserved (adjacency is part of the
    law: G5 pairs each ISS/HUBFOUND with its DISP row)."""
    ev = []
    for ln in open(path):
        w = ln.split()
        if not w or w[0] == "CTRL" or w[0] == "HUB":
            continue
        if w[0] in ("DISP", "ISS", "HUBFOUND", "FOUND", "DESTROY", "MSG"):
            d = {}
            bad = False
            for kv in w[1:]:
                if "=" not in kv:
                    bad = True
                    break
                k, v = kv.split("=", 1)
                d[k] = v
            if not bad:
                ev.append((w[0], d))
    return ev


def acceptance(sav_path, results, log_path=DEF_LOG, golden_path=DEF_GOLDEN,
               ring_path=DEF_RING, census_txt=DEF_CENSUS):
    """Run the ten B14 gates, appending (name, ok) to results; print detail."""
    def gate(name, ok, detail):
        results.append((name, bool(ok)))
        print("  %s %s" % ("PASS" if ok else "FAIL", name) +
              ("  | " + detail if detail else ""))

    def self_argmax_sites(path, g, bases, own_gate=True):
        occ = set(bases)
        hits, loses = [], []
        for (fac, x, y, cnt) in golden_founds(path):
            if scan_esi(g, x, y, occ, own_gate=own_gate) == 0:
                hits.append((fac, x, y))
            else:
                loses.append("fac%d(%d,%d)" % (fac, x, y))
            occ.add((x, y))
        return hits, loses

    # G1: ring literals == the recorded file-image dump, and the dump itself
    # satisfies the laws M291 G5 verified (center, exact diamonds, ascending).
    ddx, ddy = load_ring_dump(ring_path)
    mono = all(abs(RING_DX[i]) + abs(RING_DY[i]) <=
               abs(RING_DX[i + 1]) + abs(RING_DY[i + 1]) for i in range(24))
    g1 = (RING_DX == ddx and RING_DY == ddy and len(ddx) == 25 and
          (RING_DX[0], RING_DY[0]) == (0, 0) and
          set(zip(RING_DX[1:9], RING_DY[1:9])) == M2_DIAMOND and
          set(zip(RING_DX[9:], RING_DY[9:])) == M4_DIAMOND and mono)
    gate("G1 ring literals == recorded dump + diamond laws", g1,
         "25 entries, center(0,0), m2/m4 diamonds exact, ascending")

    # Shared state: the save grid (record view) + the save's base tiles.
    sv = sosave.parse(sav_path)
    g = Grid(sv)
    bases = set()
    for i in range(sv.found_bases):
        b = sv.base(i)
        if b:
            bases.add((b["x"], b["y"]))

    # G2: the M289 golden - every recorded founding is self-argmax (esi == 0)
    # of THIS scan on the grown occupancy.
    hits, _ = self_argmax_sites(golden_path, g, bases)
    golden = golden_founds(golden_path)
    gate("G2 m289 golden self-argmax via sim scan",
         len(hits) == 7 and len(golden) == 7, "%d/7" % len(hits))

    # G2b: the SELECTION itself, brute-forced (s241 Greptile P1#1: the
    # founding tests only ever saw esi==0, so a first-better bug would
    # pass them). Over a fixed sample of save tiles: scan_esi must equal
    # an independently computed max-value/lowest-index argmax over the
    # eligible positive entries, and the sample MUST contain discriminating
    # tiles - >0 where two better candidates carry different values, so a
    # first-better rule and the argmax differ there.
    n_multi, g2b = 0, True
    for yy in range(0, g.H, 3):
        for xx in range(0, g.W, 2):
            cf, ob, v0 = g.catflag(xx, yy), g.own3(xx, yy), g.val(xx, yy)
            cands = []
            for i in range(25):
                nx, ny = (xx + RING_DX[i]) % g.W, yy + RING_DY[i]
                if not (0 <= ny < g.H):
                    continue
                if g.catflag(nx, ny) != cf or g.own3(nx, ny) != ob:
                    continue
                if g.blocked(nx, ny) or (nx, ny) in bases:
                    continue
                cands.append((i, g.val(nx, ny)))
            pos = [(i, v) for (i, v) in cands if v > 0]
            want = None
            if pos:
                mv = max(v for (_, v) in pos)
                want = min(i for (i, v) in pos if v == mv)
            if scan_esi(g, xx, yy, bases) != want:
                g2b = False
            better = [v for (_, v) in cands if v > v0]
            if len(better) >= 2 and max(better) != better[0]:
                n_multi += 1
    gate("G2b argmax property vs brute force + discriminating sample",
         g2b and n_multi > 0,
         "scan==brute-force on sample; %d tiles discriminate "
         "first-better from argmax" % n_multi)

    # G3: the rivals FAIL THE SAME FIT (M291 G7): dropping the rec byte3
    # owner gate loses exactly fac1 (27,29); B10's row-major first-unoccupied
    # placeholder reproduces 0 of 7.
    hno, lno = self_argmax_sites(golden_path, g, bases, own_gate=False)
    g3a = len(hno) == 6 and lno == ["fac1(27,29)"]
    occ = set(bases)
    ph = 0
    for (fac, x, y, cnt) in golden:
        first = None
        for yy in range(g.H):
            for xx in range(g.W):
                if g.catflag(xx, yy) == 0 and (xx, yy) not in occ:
                    first = (xx, yy)
                    break
            if first:
                break
        if first == (x, y):
            ph += 1
        occ.add((x, y))
    gate("G3 rivals fail the fit", g3a and ph == 0,
         "no-owngate %d/7 loses%s | B10-placeholder %d/7" %
         (len(hno), lno, ph))

    ev = parse_census(log_path)
    disp = [d for t, d in ev if t == "DISP"]
    iss = [d for t, d in ev if t == "ISS"]
    hub = [d for t, d in ev if t == "HUBFOUND"]
    fnd = [d for t, d in ev if t == "FOUND"]
    msg = [d for t, d in ev if t == "MSG"]

    # G4: census shape as the instrument recorded it (26-turn window):
    # row counts, st==8 on every DISP, own == (ownrec == curfac) on every
    # DISP (the 52*u+14 owner-address law), esi in [0, 24] everywhere.
    g4 = (len(disp) == 29 and len(iss) == 11 and len(hub) == 9 and
          len(fnd) == 9 and len(msg) == 0 and
          all(int(d["st"]) == 8 for d in disp) and
          all(int(d["own"]) == (1 if int(d["ownrec"]) == int(d["curfac"])
                                else 0) for d in disp) and
          all(0 <= int(d["esi"]) <= 24 for d in disp))
    gate("G4 census shape (29 DISP/11 ISS/9 HUBFOUND/9 FOUND/0 MSG)", g4,
         "rows DISP=%d ISS=%d HUB=%d FOUND=%d MSG=%d st==8 %s own-law %s" %
         (len(disp), len(iss), len(hub), len(fnd), len(msg),
          all(int(d["st"]) == 8 for d in disp),
          all(int(d["own"]) == (1 if int(d["ownrec"]) == int(d["curfac"])
                                else 0) for d in disp)))

    # G5: the dispatch TABLE as classifier: legs partition the 29 DISP rows
    # 9 found / 9 continue / 11 walk / 0 msg; pairing law - every ISS row's
    # (u, esi) equals its immediately-preceding DISP row's and that esi >= 9;
    # every HUBFOUND follows its esi==0 DISP with equal u AND tile; every
    # FOUND equals the immediately-preceding HUBFOUND's tile; no continue row
    # is ever followed by an ISS or HUBFOUND for its u.
    legs = {"found": 0, "continue": 0, "walk": 0, "msg": 0}
    last_disp = {}
    prev_ev = None
    g5 = True
    for t, d in ev:
        if t == "DISP":
            legs[dispatch_leg(int(d["esi"]), False)[0]] += 1
            last_disp[int(d["u"])] = d
        elif t == "ISS":
            u = int(d["u"])
            pd = last_disp.get(u)
            if (pd is None or int(pd["esi"]) != int(d["esi"]) or
                    dispatch_leg(int(d["esi"]), False)[0] != "walk"):
                g5 = False
            last_disp[u] = None  # CONSUME: an outcome may pair once (P2)
        elif t == "HUBFOUND":
            u = int(d["u"])
            pd = last_disp.get(u)
            if (pd is None or int(pd["esi"]) != 0 or
                    int(pd["x"]) != int(d["x"]) or int(pd["y"]) != int(d["y"])):
                g5 = False
            last_disp[u] = None  # CONSUME
        elif t == "FOUND":
            if (prev_ev is None or prev_ev[0] != "HUBFOUND" or
                    prev_ev[1]["x"] != d["x"] or prev_ev[1]["y"] != d["y"]):
                g5 = False
        prev_ev = (t, d)
    g5 = (g5 and legs["found"] == 9 and legs["continue"] == 9 and
          legs["walk"] == 11 and legs["msg"] == 0)
    gate("G5 dispatch legs partition + pair the live rows", g5,
         "model %s vs recorded ISS=%d HUB=%d FOUND=%d" %
         (legs, len(iss), len(hub), len(fnd)))

    # G6: the WALK target: for every ISS row, the model's wrapped ring sum
    # X equals the recorded target-X, 11/11 (Y is static-gated only, declared).
    ok6, det6 = True, []
    last_disp = {}
    for t, d in ev:
        if t == "DISP":
            last_disp[int(d["u"])] = d
        elif t == "ISS":
            pd = last_disp[int(d["u"])]
            tx, ty = walk_target(int(pd["x"]), int(pd["y"]), int(d["esi"]),
                                 g.W, g.H)
            if tx != int(d["tile"]):
                ok6 = False
                det6.append("u=%s got %d want %d" % (d["u"], tx, d["tile"]))
    gate("G6 walk target-X == wrapped ring sum (11 rows)",
         ok6 and len(iss) == 11, "; ".join(det6) or "11/11")

    # G7: the rival SWAP fails the same fit: read the Y table as the X delta
    # (0x678990 into eax instead of 0x67850c).
    ok7 = 0
    last_disp = {}
    for t, d in ev:
        if t == "DISP":
            last_disp[int(d["u"])] = d
        elif t == "ISS":
            pd = last_disp[int(d["u"])]
            rx = (int(pd["x"]) + RING_DY[int(d["esi"])]) % g.W
            if rx == int(d["tile"]):
                ok7 += 1
    gate("G7 table-swap rival fails the fit", ok7 == 0 and len(iss) == 11,
         "rival reproduces %d of 11" % ok7)

    # G8: the census window's OWN ledger (m292 rows): count-strict replay -
    # every op row's pre-cnt equals the running count, endpoint == the POST
    # count the census recorded in its summary file.
    pre_txt = open(census_txt).read()
    post = None
    for wtok in pre_txt.split():
        if wtok.startswith("POST"):
            pass
    import re as _re
    mpost = _re.search(r"POST count=(\d+)", pre_txt)
    post = int(mpost.group(1)) if mpost else -1
    run = int(fnd[0]["cnt"]) if fnd else -1
    g8 = True
    steps = []
    for t, d in ev:
        if t == "FOUND":
            if int(d["cnt"]) != run:
                g8 = False
            steps.append((t, run))
            run += 1
        elif t == "DESTROY":
            if int(d["cnt"]) != run:
                g8 = False
            steps.append((t, run))
            run -= 1
    g8 = g8 and run == post == 27 and len(steps) == 10
    gate("G8 m292 ledger count-strict 19->27", g8,
         "start %d ops %d end %d (POST %d)" %
         (int(fnd[0]["cnt"]) if fnd else -1, len(steps), run, post))

    # G9: the msg-leg law with BOTH inputs named (s240): flag = global AND
    # owner==human. ds:0x920434 = 0 in solo (M293 read-only /proc probe,
    # evidence recorded in NAMED.md M290/M293): every row is msg-inert
    # structurally, and the live log indeed carries MSG=0. Synthetic shapes
    # model the leg itself (declared: shapes, not recorded events).
    inert = all(not msg_gate(0, int(d["ownrec"]), int(d["curfac"]))
                for d in disp) and len(msg) == 0
    shapes = (msg_gate(1, 3, 3) and not msg_gate(1, 6, 3) and
              not msg_gate(0, 3, 3) and
              dispatch_leg(0, True) == ("msg", soh.MSG_AUTO_BUILD) and
              dispatch_leg(0, False) == ("found",) and
              dispatch_leg(4, False) == ("continue",) and
              dispatch_leg(9, False) == ("walk",) and
              dispatch_leg(24, False) == ("walk",))
    gate("G9 msg-gate law + solo inertness", inert and shapes,
         "ds:0x920434=0 -> inert on all 29 rows; leg table complete")

    # G10: the module is runnable and deterministic: two `python3 -m
    # sim.podscan` runs write byte-identical reports and exit 0. Reports go
    # to a unique temp dir, never beside the input save (s241 Greptile P2).
    import shutil
    import tempfile
    outs = []
    rc0 = True
    tmpd = tempfile.mkdtemp(prefix="b14det")
    try:
        for k in (0, 1):
            fp = os.path.join(tmpd, "det%d.txt" % k)
            r = subprocess.run([sys.executable, "-m", "sim.podscan",
                                "--sav", os.path.relpath(sav_path, ROOT),
                                "--out", fp], cwd=ROOT,
                               capture_output=True, text=True)
            rc0 = rc0 and r.returncode == 0
            if os.path.exists(fp):
                outs.append(hashlib.sha256(open(fp, "rb").read()).hexdigest()[:16])
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    gate("G10 module run twice, identical sha256",
         rc0 and len(outs) == 2 and outs[0] == outs[1], ",".join(outs))


def report_text(sav_path):
    """The deterministic report for the module run (no timestamps)."""
    lines = ["B14 podscan report (sim.podscan, s241)"]
    sv = sosave.parse(sav_path)
    g = Grid(sv)
    lines.append("save %s %dx%d bases %d" %
                 (os.path.basename(sav_path), g.W, g.H, sv.found_bases))
    lines.append("ring entries: " + " ".join(
        "%d:(%d,%d)" % (i, RING_DX[i], RING_DY[i]) for i in range(25)))
    for t, d in parse_census(DEF_LOG):
        if t == "DISP":
            leg = dispatch_leg(int(d["esi"]),
                               msg_gate(0, int(d["ownrec"]),
                                        int(d["curfac"])))[0]
            extra = ""
            if leg == "walk":
                tx, ty = walk_target(int(d["x"]), int(d["y"]),
                                     int(d["esi"]), g.W, g.H)
                extra = " target(%d,%d)" % (tx, ty)
            lines.append("DISP u=%s esi=%s x=%s y=%s -> %s%s" %
                         (d["u"], d["esi"], d["x"], d["y"], leg, extra))
    return chr(10).join(lines) + chr(10)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.podscan")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--out", help="write this report here")
    a = ap.parse_args(argv)
    txt = report_text(a.sav)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt)
        print("wrote " + a.out)
    else:
        sys.stdout.write(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
