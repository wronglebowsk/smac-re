#!/usr/bin/env python3
"""B16 - the pod-scan loop HEAD PRE-CHECK CHAIN, executable (sim side).

FUN_0055f650 scan loop 0x5638a9-0x563cbd: every slot runs the tests below
BEFORE the B15 price gate; a failing test jumps straight to the loop tail
0x563cb3, so the slot prints a GROW row with tail garbage ($esi = slot/x, the
M294 tail law) and NEVER a decision (GDEEP/GACC) row. NOTE (s246, Greptile #258 P1): passing the whole chain is NOT sufficient to print a row - the value-vs-best skip `cmp esi,eax / jle 0x563cb3` at 0x563c09-0x563c11 runs after the pre-checks and before GDEEP at 0x563c3d (the accept-bypass `jge 0x563ca7` at 0x563c38 prints GACC instead), so pass-and-no-row (BASE 8482) is the UNION of no-go rejects and value<=best skips, never the no-go reject set alone. Parity target: which
slots of each recorded hub visit printed a decision row at all
(evidence/m294_gate_rows_raw.txt, m294 window: m54b_clean lineage y2188+24).

BYTE PINS: evidence/b16_precheck_window.txt (scripts/b16_pin_window.py, objdump
-M intel over terran.exe .text from the function entry 0x55f650). Chain:
  1 bounds   0x5638d2 call 0x469060(owner? no: (X,Y), see 0x56395d-0x563962 for
             the arg push order of 0x4e3c00) returns 0 -> je 0x563cb3 at 0x5638dc.
             0x469060 range-tests BOTH legs: 0 <= arg2 < ds:0x92a37c (H) and
             0 <= arg1 < ds:0x92a378 (W). X arrives pre-wrapped from the
             single-arg helper 0x469010 (call 0x5638b9, mod ds:0x92a378), so in
             practice only Y - never wrapped - can fail it.
  2 class    0x56390b-0x563917: BYTE[tileview] and 0xe0, cmp 0x60, setl -> the
             WATER flag (cat = byte0>>5 < 3) must equal [ebp-0x58].
  3 b8_bit20 0x56391d-0x563928: edx = DWORD[tileview+8]; if bit 0x20 of BYTE 8
             is set the tile needs cat < 2 (cmp eax,0x40 / jge tail).
  4 elev     0x563930-0x56393e: ebx = BYTE[tileview+5] and 0xffffffc0 -> the
             elevation band byte5&0xc0; only when the band is > 0x40 (cmp 0x40 /
             jle 0x563944) does it bite, and then the tile needs cat < 3 (water).
  5 region   0x563944-0x56394e: BYTE[tileview+3] must equal [ebp-0x34].
  6 occ      0x563954-0x563957: dh = BYTE[tileview+9]; bit 0x20 set -> tail.
  7 nogo     0x56395d-0x56396d: call 0x4e3c00(arg1 = [ebp-0xc] = the pod OWNER
             byte BYTE[0x933286+52u], stored 0x55f71d; then X, then Y) and a
             NON-NEGATIVE return skips the slot. UNMODELED here (see UNMODELED).

THE [ebp-0x58] / [ebp-0x34] ORIGIN (the pick's questions 2 and 3):
  tileview(pod) = ds:0x92ae14 + 44*(ds:0x692184*pody + podx>>1), 0x55f768-0x55f77e;
  podx = x16 @0x933278+52u stored [ebp-0x18] at 0x55f72d, pody = x16 @0x93327a+52u
  stored [ebp-0x14] at 0x55f740. ds:0x692184 is the RECORD-ROW multiplier (W/2 for
  the 44-B record view) and the >>1 side is X - so [ebp-0x4] = X, [ebp-0x8] = Y.
  [ebp-0x40] = BYTE[0x92ae81 + 144*BYTE[0x98adac + 52*type]] (0x55f74f-0x55f765:
  the lookup byte scaled by 9 (lea edi,[eax+eax*8]) then 16 (shl edi,4) - stride 0x90):
  the unit TYPE's required-class byte.  [ebp-0x74] = the POD tile's own water flag
  (0x55f783-0x55f79c).  [ebp-0x34] = BYTE[tileview(pod)+3], the POD region, stored
  once at 0x55f7a5 and never written again before the loop -> the gate's region IS
  the pod region (M294).  0x56380c-0x563817: sete al on ([ebp-0x40]==1) ->
  [ebp-0x58] = that flag, and the cmp ecx,eax / jne 0x563f18 right there gates the
  WHOLE SCAN on ([ebp-0x74] == [ebp-0x58]). THEOREM the sim uses: the required
  terrain class equals the POD TILE's own class flag (else there is no scan at all).

LOG READER LAW (B16 finding, gate G2): the m294 census printf at
scripts/m294_gate_row_census.py:76/89 labels the two legs TRANSPOSED - `x=` is
*(int*)($ebp-0x8) (the Y leg, the multiplied side) and `y=` is *(int*)($ebp-0x4)
(the X leg, the >>1 side). Read a GDEEP/GACC tile as (x=row.y, y=row.x).

UNMODELED / DECLARED: 0x4e3c00's no-go predicate; the value>best skip at 0x563c11 (the other no-row producer, see NOTE); the per-slot state drift
between the graded save (y2150) and the recorded window (y2188+24).
"""
import collections
import hashlib
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEF_RAW = os.path.join(REPO, "evidence", "m294_gate_rows_raw.txt")
DEF_WIN = os.path.join(REPO, "evidence", "b16_precheck_window.txt")
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from sim import save as sosave                       # noqa: E402
from sim.podscan import Grid, RING_DX, RING_DY       # noqa: E402

CHAIN = ("bounds", "class", "b8_bit20", "elev", "region", "occ", "nogo")
MODELLED = CHAIN[:6]
PINS = (
    (0x5638d2, "call 0x469060", "bounds-call"),
    (0x5638dc, "je 0x563cb3", "bounds-taken"),
    (0x56390d, "and al,0xe0", "class-mask"),
    (0x56390f, "cmp eax,0x60", "class-cmp"),
    (0x563915, "cmp edx,ebx", "class-cmp-mask"),
    (0x563917, "jne 0x563cb3", "class-taken"),
    (0x56391d, "mov edx,DWORD PTR [ecx+0x8]", "b8-load"),
    (0x563920, "test dl,0x20", "b8-test"),
    (0x563925, "cmp eax,0x40", "b8-cat"),
    (0x563928, "jge 0x563cb3", "b8-taken"),
    (0x563930, "mov bl,BYTE PTR [ecx+0x5]", "elev-load"),
    (0x563933, "and ebx,0xffffffc0", "elev-mask"),
    (0x563936, "cmp ebx,0x40", "elev-band-cmp"),
    (0x56393b, "cmp eax,0x60", "elev-cat"),
    (0x56393e, "jge 0x563cb3", "elev-taken"),
    (0x563944, "mov ebx,DWORD PTR [ebp-0x34]", "region-mask-load"),
    (0x563949, "mov al,BYTE PTR [ecx+0x3]", "region-load"),
    (0x56394c, "cmp eax,ebx", "region-cmp"),
    (0x56394e, "jne 0x563cb3", "region-taken"),
    (0x563954, "test dh,0x20", "occ-test"),
    (0x563957, "jne 0x563cb3", "occ-taken"),
    (0x563963, "call 0x4e3c00", "nogo-call"),
    (0x56396d, "jge 0x563cb3", "nogo-taken"),
    (0x55f72d, "mov DWORD PTR [ebp-0x18],edx", "pod-x-store"),
    (0x55f740, "mov DWORD PTR [ebp-0x14],esi", "pod-y-store"),
    (0x55f71d, "mov DWORD PTR [ebp-0xc],eax", "owner-store"),
    (0x55f7a5, "mov DWORD PTR [ebp-0x34],eax", "pod-region-store"),
    (0x55f79c, "mov DWORD PTR [ebp-0x74],edx", "pod-class-store"),
    (0x55f765, "mov DWORD PTR [ebp-0x40],eax", "type-class-store"),
    (0x563814, "mov DWORD PTR [ebp-0x58],eax", "req-class-store"),
    (0x5638f2, "mov ebx,DWORD PTR [ebp-0x58]", "req-class-read"),
)
# Reproduction baseline, measured by the SHIPPED parser when B16 was authored
# (m54b_clean 64x64 y2150 vs evidence/m294_gate_rows_raw.txt, m294 window).
# If it stops reproducing, the chain model changed: re-derive it, do not re-pin
# it, unless changing the model IS the milestone.
BASE = {
    "conf": {"True,True": 2128, "True,False": 193,
             "False,True": 8482, "False,False": 14847},
    "pods": 1026, "disp": 201, "disp_ok": 201, "rival_pods": 638,
    "rival_disp_ok": 0, "mixed_cls": 0, "mixed_reg": 0,
    "tab": {"bounds": [2321, 0, 23219, 110],
            "class": [2215, 106, 18293, 5036],
            "b8_bit20": [2320, 1, 14018, 9311],
            "elev": [2321, 0, 20025, 3304],
            "region": [2129, 192, 17449, 5880],
            "occ": [2321, 0, 22940, 389]},
    "solo": {"bounds": 0, "class": 0, "b8_bit20": 5775, "elev": 2181,
             "region": 185, "occ": 212},
}


def classflag(b0):
    """(byte0 and 0xe0) < 0x60, i.e. the setl dl the cmp at 0x56390f leaves"""
    return 1 if b0 // 32 < 3 else 0


def band(b5):
    """ebx after `and ebx,0xffffffc0` at 0x563933 (the elevation band)"""
    return (b5 // 64) * 64


def bit20(v):
    """test reg,0x20 at 0x563920 (dl) and 0x563954 (dh)"""
    return (v // 32) % 2


def prechecks(g, W, H, px, py, pcls, preg, s):
    """the 6 modelled loop-head tests for ring slot s of the pod at (px,py)"""
    tx = (px + RING_DX[s]) % W
    ty = py + RING_DY[s]
    inb = 0 <= ty < H
    r = g.rb(tx, ty if inb else (0 if ty < 0 else H - 1))
    cat = r[0] // 32
    out = {}
    out["bounds"] = bool(inb)
    out["class"] = classflag(r[0]) == pcls
    out["b8_bit20"] = not (bit20(r[8]) and cat >= 2)
    out["elev"] = not (band(r[5]) > 0x40 and cat >= 3)
    out["region"] = (r[3] == preg)
    out["occ"] = not bit20(r[9])
    out["nogo"] = True
    return out, (tx, ty), r


def load_visits(path, transposed=True):
    """the m294 raw rows split into hub visits; decision rows carry the TRUE
    tile (x,y) once the B16 transposition law is applied to the printed pair"""
    vis, cur = [], None
    for ln in open(path):
        w = ln.split()
        if not w:
            continue
        k = w[0]
        if k == "HUB":
            cur = {"u": int(w[1][2:]), "disp": None, "dec": [], "ngrow": 0}
            vis.append(cur)
        elif cur is None:
            continue
        else:
            d = {}
            for kv in w[1:]:
                if "=" in kv:
                    a, b = kv.split("=", 1)
                    if a in ("slot", "x", "y"):
                        d[a] = int(b)
            if k in ("GDEEP", "GACC") and len(d) == 3:
                if transposed:
                    cur["dec"].append({"slot": d["slot"], "x": d["y"], "y": d["x"]})
                else:
                    cur["dec"].append({"slot": d["slot"], "x": d["x"], "y": d["y"]})
            elif k == "GROW":
                cur["ngrow"] += 1
            elif k == "DISP" and cur["disp"] is None and len(d) == 2:
                cur["disp"] = (d["x"], d["y"])
    return vis


def recover_pod(v, W):
    """the visit's pod tile from its decision rows; None when they disagree"""
    cand = set()
    for d in v["dec"]:
        s = d["slot"]
        cand.add(((d["x"] - RING_DX[s]) % W, d["y"] - RING_DY[s]))
    if len(cand) != 1:
        return None
    return cand.pop()


def analyse(visits, g, W, H):
    """run the chain over every visit whose pod is recoverable and tabulate"""
    a = {}
    conf = collections.Counter()
    tab = collections.defaultdict(lambda: [0, 0, 0, 0])
    solo = collections.Counter()
    viol = collections.defaultdict(list)
    pods = disp = disp_ok = 0
    mixed_cls = mixed_reg = 0
    agree_cls = disagree_cls = agree_reg = disagree_reg = 0
    drift_all = drift_some = 0
    both_dis = cls_dis_only = reg_dis_only = 0
    for v in visits:
        if v["ngrow"] != 25 or not v["dec"]:
            continue
        p = recover_pod(v, W)
        if p is None:
            continue
        pods += 1
        px, py = p
        if v["disp"] is not None:
            disp += 1
            disp_ok += 1 if v["disp"] == p else 0
        pr = g.rb(px, py)
        pcls, preg = classflag(pr[0]), pr[3]
        dec = set(d["slot"] for d in v["dec"])
        cls_seen = set(classflag(g.rb(d["x"], d["y"])[0]) for d in v["dec"])
        reg_seen = set(g.rb(d["x"], d["y"])[3] for d in v["dec"])
        mixed_cls += 1 if len(cls_seen) > 1 else 0
        mixed_reg += 1 if len(reg_seen) > 1 else 0
        infer_cls = cls_seen.pop()
        infer_reg = reg_seen.pop()
        agree_cls += 1 if infer_cls == pcls else 0
        disagree_cls += 1 if infer_cls != pcls else 0
        agree_reg += 1 if infer_reg == preg else 0
        disagree_reg += 1 if infer_reg != preg else 0
        cd = infer_cls != pcls
        rd = infer_reg != preg
        both_dis += 1 if (cd and rd) else 0
        cls_dis_only += 1 if (cd and not rd) else 0
        reg_dis_only += 1 if (rd and not cd) else 0
        bad_cls = sum(1 for d in v["dec"]
                      if classflag(g.rb(d["x"], d["y"])[0]) != pcls)
        if bad_cls:
            drift_all += 1 if bad_cls == len(v["dec"]) else 0
            drift_some += 1 if bad_cls != len(v["dec"]) else 0
        for s in range(25):
            c, (tx, ty), r = prechecks(g, W, H, px, py, pcls, preg, s)
            rec = s in dec
            fails = [k for k in MODELLED if not c[k]]
            allpass = not fails
            conf[(rec, allpass)] += 1
            for k in MODELLED:
                gg = c[k]
                tab[k][0 if (gg and rec) else 1 if (not gg and rec)
                       else 2 if gg else 3] += 1
                if rec and not gg and len(viol[k]) < 3:
                    viol[k].append((px, py, s, tx, ty, list(r[:10]), pcls, preg))
            if (not rec) and len(fails) == 1:
                solo[fails[0]] += 1
    a.update(conf=conf, tab=tab, solo=solo, viol=viol, pods=pods, disp=disp,
             disp_ok=disp_ok, mixed_cls=mixed_cls, mixed_reg=mixed_reg,
             agree_cls=agree_cls, disagree_cls=disagree_cls,
             agree_reg=agree_reg, disagree_reg=disagree_reg,
             drift_all=drift_all, drift_some=drift_some,
             both_dis=both_dis, cls_dis_only=cls_dis_only,
             reg_dis_only=reg_dis_only)
    return a


def load_pins(path):
    """evidence/b16_precheck_window.txt -> {pc: normalized mnemonic}"""
    pins = {}
    with open(path) as fh:
        for ln in fh:
            if ln.startswith("#") or "\t" not in ln:
                continue
            a, t = ln.rstrip(chr(10)).split("\t", 1)
            pins[int(a, 16)] = " ".join(t.split())
    return pins


def build(sav_path, raw=DEF_RAW, win=DEF_WIN):
    sv = sosave.parse(sav_path)
    g = Grid(sv)
    a_tr = analyse(load_visits(raw, True), g, sv.width, sv.height)
    a_rv = analyse(load_visits(raw, False), g, sv.width, sv.height)
    return {"sv": sv, "g": g, "a": a_tr, "rival": a_rv, "pins": load_pins(win)}


def report_text(sav_path, raw=DEF_RAW, win=DEF_WIN):
    b = build(sav_path, raw, win)
    sv, a = b["sv"], b["a"]
    L = []
    ap = L.append
    ap("B16 pod-scan loop-head PRE-CHECK CHAIN (FUN_0055f650 0x5638a9-0x563cbd)")
    ap("save %s %dx%d year %d; recorded window %s" %
       (os.path.basename(sav_path), sv.width, sv.height, sv.year,
        os.path.basename(raw)))
    matched = sum(1 for pc, want, _ in PINS
                  if b["pins"].get(pc) == " ".join(want.split()))
    ap("chain pins matched %d/%d against the %d-instruction window file %s" %
       (matched, len(PINS), len(b["pins"]), os.path.basename(win)))
    ap("transposition law: pods recovered %d (rival reading %d); DISP cross-check %d/%d"
       % (a["pods"], b["rival"]["pods"], a["disp_ok"], a["disp"]))
    ap("rival DISP cross-check: %d/%d" % (b["rival"]["disp_ok"], b["rival"]["disp"]))
    ap("confusion (decision-slot, passes all 6 modelled checks) -> count")
    for k in sorted(a["conf"]):
        ap("  %s %s -> %d" % (k[0], k[1], a["conf"][k]))
    ap("per-check pass&rec / fail&rec / pass&skip / fail&skip / solo-excludes")
    for k in MODELLED:
        ap("  %-9s %s solo=%d" % (k, a["tab"][k], a["solo"][k]))
    ap("class flag mixed across a visit's decision rows: %d visits; region: %d" %
       (a["mixed_cls"], a["mixed_reg"]))
    ap("pod-flag theorem vs the save: class agrees %d disagrees %d; region agrees %d disagrees %d"
       % (a["agree_cls"], a["disagree_cls"], a["agree_reg"], a["disagree_reg"]))
    ap("class-drift attribution: all-decision-slots %d, some %d" %
       (a["drift_all"], a["drift_some"]))
    ap("pod-flag cross-tab (flag inferred from the rows vs the save pod tile):"
       " class AND region %d, class only %d, region only %d"
       % (a["both_dis"], a["cls_dis_only"], a["reg_dis_only"]))
    ap("violations of a SOUND check by a recorded decision slot (must be 0):")
    for k in ("bounds", "elev", "occ"):
        ap("  %-9s %d" % (k, len(a["viol"][k])))
    for k in MODELLED:
        for t in a["viol"][k][:2]:
            ap("  ex %-9s pod=(%d,%d) slot=%d tile=(%d,%d) rec=%s pcls=%d preg=%d"
               % (k + " ", t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]))
    ap("DECLARED UNMODELED: 0x4e3c00(owner,x,y) no-go (the pass-all-statics-but-no-row"
       " population), and the per-tile state drift between the graded save and the")
    ap("  recorded window (y2188+24): region byte3 / occ byte9 of a live tile move under")
    ap("  settlement, which is what the fail&rec counts of class and region measure.")
    return chr(10).join(L) + chr(10)


def acceptance(sav_path, results, raw=DEF_RAW, win=DEF_WIN):
    """the 7 B16 gates; appends (name, ok) to results and prints detail"""
    def gate(name, ok, detail=""):
        results.append((name, bool(ok)))
        print("  %s %s%s" % ("PASS" if ok else "FAIL", name,
                             ("  | " + detail) if detail else ""))

    b = build(sav_path, raw, win)
    sv, a, rv = b["sv"], b["a"], b["rival"]
    ndec_visits = sum(1 for v in load_visits(raw, True)
                      if v["ngrow"] == 25 and v["dec"])

    missing = [(pc, want) for pc, want, _ in PINS
               if b["pins"].get(pc) != " ".join(want.split())]
    gate("G1 pins: every chain/prologue byte window resolvable in the shipped "
         "window file", not missing,
         "%d/%d matched%s" % (len(PINS) - len(missing), len(PINS),
                              "" if not missing else " missing " + repr(missing[:3])))

    gate("G2 transposition law: pod recovery 100%% of the %d decision-row visits, "
         "DISP cross-check 100%%, both rivals strictly worse" % ndec_visits,
         a["pods"] == ndec_visits and a["disp_ok"] == a["disp"] and a["disp"] > 0
         and rv["pods"] < a["pods"] and rv["disp_ok"] < a["disp_ok"],
         "pods %d/%d (rival %d); DISP %d/%d (rival %d)"
         % (a["pods"], ndec_visits, rv["pods"], a["disp_ok"], a["disp"],
            rv["disp_ok"]))

    snd = [a["tab"][k][1] for k in ("bounds", "elev", "occ")]
    gate("G3 sound: no recorded decision slot fails bounds, elev or occ (the "
         "state-insensitive legs)", not any(snd),
         "fail&rec bounds=%d elev=%d occ=%d" % tuple(snd))

    solo = {k: a["solo"][k] for k in MODELLED}
    fs = {k: a["tab"][k][3] for k in MODELLED}
    never = sorted(k for k in MODELLED if solo[k] == 0)
    gate("G4 effect: every modelled test excludes at least one recorded skip "
         "slot (fail&skip > 0); a test that never excludes ALONE in this window "
         "is named with its numbers, not hidden",
         all(fs[k] > 0 for k in MODELLED),
         "fail&skip " + repr(sorted(fs.items())) + " | never-sole-excluder "
         + repr(never) + " solo " + repr(sorted((k, solo[k]) for k in never)))

    gate("G5 chain consistency: every visit's recorded decision slots share ONE "
         "terrain class flag (the [ebp-0x58] law)", a["mixed_cls"] == 0,
         "mixed-class visits %d; region-mixed %d (state drift, recorded)"
         % (a["mixed_cls"], a["mixed_reg"]))

    got = {("%s,%s" % k): v for k, v in a["conf"].items()}
    tab = dict((k, list(a["tab"][k])) for k in MODELLED)
    sol = dict((k, a["solo"][k]) for k in MODELLED)
    ok6 = (got == BASE["conf"] and tab == BASE["tab"]
           and sol == BASE["solo"] and a["pods"] == BASE["pods"]
           and a["disp"] == BASE["disp"] and a["disp_ok"] == BASE["disp_ok"]
           and rv["pods"] == BASE["rival_pods"]
           and rv["disp_ok"] == BASE["rival_disp_ok"]
           and a["mixed_cls"] == BASE["mixed_cls"]
           and a["mixed_reg"] == BASE["mixed_reg"])
    det6 = ("pinned conf/tab/solo/pods/rivals reproduced" if ok6 else
            "DRIFT conf " + repr(sorted(got.items())) + " tab "
            + repr(sorted(tab.items())) + " solo " + repr(sorted(sol.items()))
            + " pods/disp/ok " + repr((a["pods"], a["disp"], a["disp_ok"]))
            + " rival " + repr((rv["pods"], rv["disp_ok"])))
    gate("G6 reproduction: confusion grid, per-check table, solo set and the "
         "pod/DISP/rival counts all match the pinned B16 baseline", ok6, det6)

    t1 = report_text(sav_path, raw, win)
    t2 = report_text(sav_path, raw, win)
    h1 = hashlib.sha256(t1.encode()).hexdigest()
    gate("G7 determinism: two runs byte-identical", h1 == hashlib.sha256(
        t2.encode()).hexdigest(), "sha256 " + h1[:16])
    return b


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="sim.precheck")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--raw", default=DEF_RAW)
    ap.add_argument("--win", default=DEF_WIN)
    ap.add_argument("--out", help="write the report here")
    args = ap.parse_args(argv)
    res = []
    acceptance(args.sav, res, args.raw, args.win)
    bad = [n for n, ok in res if not ok]
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(report_text(args.sav, args.raw, args.win))
        print("wrote " + args.out)
    if bad:
        print("FAIL B16: %d/%d gates failed: %s" % (len(bad), len(res), "; ".join(bad)))
        return 1
    print("PASS B16: %d/%d gates" % (len(res), len(res)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
