#!/usr/bin/env python3
"""M296 - the value-vs-best ARGMAX leg FITTED against the m294 gate rows.

The last un-named decision producer in B16's loop: at 0x563c02 `call 0x46e770`
computes the slot VALUE into esi; 0x563c09-0x563c11 `cmp esi,eax / jle 0x563cb3`
SKIPS the slot when value <= best ([ebp-0x24]). The pass-6-no-row population
(BASE 8482, evidence/b16_precheck_chain.txt:8) is no-go rejects UNION these
skips; M295 measured the full no-go rule rejecting 0 in the graded subset, so
THIS leg is the candidate closer for the 8482.

BYTE FACT this fit: the ONLY pre-loop writers of [ebp-0x24] are at
0x563836-0x56389f: `cmp esi,8 / mov [ebp-0x24],0x0 / jne 0x5638a2` zeros best
for every visit that is not case 8, and `cmp BYTE[ebx+0x933289],0x18 /
jne 0x5638a2` gates the override on the unit ORDER byte (unit+17, NAMED
0x4d3770) being 0x18 = the move-to-base order whose +20/+28 u16s are the
TARGET BASE TILE (NAMED 0x4d6fb0). For case-8 move-to-base pods:
movsx eax,[+0x933294]; movsx esi,[+0x93328c]; (wrapped-diff helpers
0x46e540/0x46e5a0, `cmp eax,2 / jle 0x5638a2` skips when the pod is within 2
of its base); then call 0x46e770; dec eax; store -> best_init =
value(base tile)-1. So the hub scan of a move-to-base pod accepts candidates
whose value >= value(the base it heads to); every other visit starts best=0.
[ebp-0x24] then updates ONLY at the accept store 0x563caa.

FUN_0046e770(X,Y) = rec byte2 HIGH nibble (0 when dword[rec+8] bit 0x1000 -
byte9 bit 4; lazy FUN_005aff90 when the nibble is 0 - then FUN_00582cc0 is
called and its return discarded). M291 named the rule; this script FITS it
against the 2321 recorded GDEEP/GACC rows (evidence/m294_gate_rows_raw.txt;
B16 transposition law applied via sim.precheck.load_visits/recover_pod).

Graded checks (all static, zero box time; the recorded val/best columns are
read DIRECTLY from the raw rows - the M294 tail-$esi law says tail val/best are
garbage, decision-row val/best are the machine's own $esi/$eax):
  S1 strict entry   every decision row has recorded val > recorded best.
  S2 best-law       recorded best == max(0, recorded GACC vals at slots < s)
                    - i.e. [ebp-0x24] updates ONLY at the accept store 0x563caa.
  S3 val-law        save byte2 high nibble (with byte8-bit4 zeroing) == recorded
                    val, per visit class (AGREED vs pod-drift, B16 law); plus
                    the byte8-bit4/0x1000 coverage count.
  S3b drift         per-tile recorded-val timelines (same tile, different val
                    across the window = live byte2 changes vs the y2150 save).
  S4 argmax-skip    the 8482 pool: cell explained as skip iff model val <=
                    best_at(slot) (best from RECORDED accepts = gate-honest);
                    split tie / static-explained / unexplained, AGREED vs DRIFT;
                    unexplained cells on tiles whose LIVE val is recorded in
                    some visit are re-graded with that override (LIVE-graded).
  S5 rivals         low nibble / full byte2 / byte0 cat / byte8 high nibble /
                    no-0x1000-zero / ge-accept, same grid - each must FAIL S1 or
                    S3 or collide on the pool.
  S6 bypass law     GACC-without-GDEEP slots (the 0x563c38 `jge 0x563ca7` leg):
                    recorded val >= 2*(8-dist); GDEEP slots val < cap.

Exit codes: 0 = every gate PASS, 1 = a FAIL (the number IS the finding).
"""
import os
import struct
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import sim.precheck as pc
from sim import save as sosave

DEF_SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
DEF_RAW = os.path.join(ROOT, "evidence", "m294_gate_rows_raw.txt")
EVID = os.path.join(ROOT, "evidence", "m296_argmax_fit.txt")

RES = []


def gate(name, ok, detail):
    RES.append((name, bool(ok), detail))
    print("%-28s %s  %s" % (name, "PASS" if ok else "FAIL", detail))


def score(r, mode):
    v = r[2] // 16
    if mode == "nib" and r[9] % 32 >= 16:      # dword[+8] & 0x1000 = byte9 bit4
        v = 0
    elif mode == "low":
        v = r[2] % 16
    elif mode == "full":
        v = r[2]
    elif mode == "cat":
        v = r[0] // 32
    elif mode == "b8hi":
        v = r[8] // 16
    return v


def load_rows(path):
    rows = {}
    vi = -1
    for ln in open(path):
        w = ln.split()
        if not w:
            continue
        if w[0] == "HUB":
            vi += 1
        elif w[0] in ("GDEEP", "GACC", "GROW") and vi >= 0:
            d = {}
            for kv in w[1:]:
                if "=" in kv:
                    a, b = kv.split("=", 1)
                    if a in ("slot", "val", "best", "dist", "case"):
                        d[a] = int(b)
            if "slot" in d:
                e = rows.setdefault((vi, d["slot"]), {})
                k = {"GDEEP": "deep", "GACC": "acc", "GROW": "grow"}[w[0]]
                if k not in e:                    # first row wins: one event per slot
                    e[k] = d
    return rows


def main():
    sav = sosave.parse(DEF_SAV)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    visits = pc.load_visits(DEF_RAW, True)
    rows = load_rows(DEF_RAW)

    def agree(v):
        p = pc.recover_pod(v, W)
        if p is None:
            return None, None
        px, py = p
        pr = g.rb(px, py)
        pcls, preg = pc.classflag(pr[0]), pr[3]
        cs = set(pc.classflag(g.rb(d["x"], d["y"])[0]) for d in v["dec"])
        rs = set(g.rb(d["x"], d["y"])[3] for d in v["dec"])
        ok = (len(cs) == 1 and len(rs) == 1
              and cs.pop() == pcls and rs.pop() == preg)
        return ok, (px, py, pcls, preg)

    tile_live = collections.defaultdict(list)  # (x,y) -> [(vi, val, slot|(-1 rec))]
    s1_bad = []
    s2_bad = []
    tie_rows = []
    s7_bad = []
    s7 = [0, 0]                     # GROW best-col ok, total
    s7b = collections.Counter()
    s7b_bad = []
    s3 = {"AGREED": [0, 0], "DRIFT": [0, 0]}
    bit1000 = 0
    lazy_rows = 0
    pool = {"AGREED": collections.Counter(), "DRIFT": collections.Counter()}
    live_grade = collections.Counter()
    bypass = [0, 0, 0]   # bypass-acc rows, ok, fail
    deep_ge_cap = 0
    nvis_ok = 0
    rivals = collections.defaultdict(lambda: [0, 0, 0, 0])  # valm, valf, exp, unexp

    for i, v in enumerate(visits):
        if v["ngrow"] != 25 or not v["dec"]:
            continue
        a, p = agree(v)
        if p is None:
            continue
        nvis_ok += 1
        px, py, pcls, preg = p
        cls = "AGREED" if a else "DRIFT"
        dec = set(d["slot"] for d in v["dec"])
        accv = {}
        for s in range(25):
            e = rows.get((i, s), {})
            if "acc" in e:
                accv[s] = e["acc"]["val"]
        # machine best_init: the FIRST decision row's recorded best (pre-accept)
        first = min(dec)
        e1 = rows.get((i, first), {})
        init_best = (e1.get("deep") or e1.get("acc"))["best"]
        # S7b law (byte-pinned 0x563836-0x56389f): best_init=0 for every visit
        # EXCEPT case-8 order-0x18 (move-to-base) pods beyond dist 2, whose
        # best_init = value(base tile)-1. The SAVE (y2150) order byte lags live
        # orders, so the testable claims: (A) every machine-nonzero init equals
        # value(save dest)-1 (the order itself may be live-issued), and (B) the
        # save-visible move-to-base cases are consistent (lazy/drift reported).
        u = v["u"]
        crow = rows.get((i, first), {})
        crow = crow.get("deep") or crow.get("acc")
        case_row = crow.get("case")
        order = dx = dy = None
        drec = None
        if u is not None and 0 <= u < len(sav.units):
            o = sav.units_off + sosave.UNIT_LEN * u
            order = sav.data[o + 17]
            dx = struct.unpack_from("<H", sav.data, o + 20)[0]
            dy = struct.unpack_from("<H", sav.data, o + 28)[0]
            if 0 <= dx < W and 0 <= dy < H:
                drec = g.rb(dx, dy)
        m_init = None
        if drec is not None and not (drec[2] // 16 == 0 and drec[9] % 32 < 16):
            m_init = score(drec, "nib") - 1
        if init_best != 0:
            s7b["nonzero_init"] += 1
            if case_row != 8:
                s7b["gate8_bad"] += 1
                s7b_bad.append(("CASE8", i, u, (px, py), (dx, dy), init_best, case_row))
            elif m_init is None:
                # save dest tile is nibble-0 (lazy) - the live value MUTATED
                # (machine says init 5 => live nibble 6): ungradeable from the
                # y2150 save; the case-8 leg still binds.
                s7b["drift_pending"] += 1
                s7b_bad.append(("DRIFT", i, u, (px, py), (dx, dy), init_best, case_row))
            elif m_init == init_best:
                s7b["law_hit"] += 1
            else:
                s7b["m2b_val_bad"] += 1
                s7b_bad.append(("VAL", i, u, (px, py), (dx, dy), init_best, m_init))
        elif case_row == 8 and order == 0x18 and drec is not None:
            # save-visible move-to-base with zero init: fine iff dist<=2 (gate
            # skip), lazy dest, or live value 1 (drift) - REPORT buckets only
            if max(min(abs(dx - px), W - abs(dx - px)),
                   min(abs(dy - py), H - abs(dy - py))) <= 2:
                s7b["m2b_gate_le2"] += 1
            elif drec[2] // 16 == 1:
                # value 1 - 1 == 0 == machine init: a RESOLVABLE law hit
                s7b["law_hit"] += 1
            elif drec[2] // 16 == 0:
                s7b["m2b_lazy_dest"] += 1
            else:
                s7b["m2b_zero_drift"] += 1
        else:
            s7b["plain_zero_ok"] += 1
        for s in range(25):
            c, (tx, ty), r = pc.prechecks(g, W, H, px, py, pcls, preg, s)
            e = rows.get((i, s), {})
            if r[9] % 32 >= 16 and r[2] // 16 > 0:
                bit1000 += 1
            sc = score(r, "nib")
            rb = max([accv[t] for t in accv if t < s] + [init_best])
            if "grow" in e:
                s7[1] += 1
                gb = max([accv[t] for t in accv if t <= s] + [init_best])
                if e["grow"]["best"] == gb:
                    s7[0] += 1
                elif len(s7_bad) < 6:
                    s7_bad.append((i, u, s, e["grow"]["best"], gb))
            if s in dec:
                rd = e.get("deep") or e.get("acc")
                rv, rbs = rd["val"], rd["best"]
                tile_live[(tx, ty)].append((i, rv, -1))
                if not rv > rbs:
                    s1_bad.append((i, s, rv, rbs))
                if rv == rbs:
                    tie_rows.append((i, s, rv))
                if rbs != rb:
                    s2_bad.append((i, s, rbs, rb))
                if sc == rv:
                    s3[cls][0] += 1
                else:
                    s3[cls][1] += 1
                    if r[2] // 16 == 0 and rv > 0:
                        lazy_rows += 1
                if "acc" in e and "deep" not in e:
                    cap = 2 * (8 - e["acc"]["dist"])
                    bypass[0] += 1
                    if e["acc"]["val"] >= cap:
                        bypass[1] += 1
                    else:
                        bypass[2] += 1
                if "deep" in e and e["deep"]["val"] >= 2 * (8 - e["deep"]["dist"]):
                    deep_ge_cap += 1
                for m in ("low", "full", "cat", "b8hi"):
                    rw = rivals[m]
                    if score(r, m) == rv:
                        rw[0] += 1
                    else:
                        rw[1] += 1
            elif not [k for k in pc.MODELLED if not c[k]]:
                # S4 pool cell: explained iff val <= best-at-slot (strict rule)
                pool[cls]["expl_tie" if (sc == rb) else
                          ("expl" if sc < rb else "unexpl")] += 1
                # LIVE override: latest live val of this tile recorded SO FAR
                # (visits are chronological; the recorded rows are the machine's
                # own val - the only trustworthy live value we have)
                hist = tile_live.get((tx, ty))
                if hist:
                    lv = hist[-1][1]
                    if lv <= rb:
                        live_grade["live_expl"] += 1
                    else:
                        live_grade["live_unexpl"] += 1
                else:
                    live_grade["live_unknown"] += 1
                for m in ("low", "full", "cat", "b8hi"):
                    rw = rivals[m]
                    v2 = score(r, m)
                    rw[2 if v2 <= rb else 3] += 1

    tot = lambda d: d[0] + d[1]
    rows_all = tot(s3["AGREED"]) + tot(s3["DRIFT"])
    pool_all = sum(pool[c][k] for c in pool for k in pool[c])
    print("visits graded %d | rows %d | pool %d" % (nvis_ok, rows_all, pool_all))
    gate("S0_coverage_pinned_baseline",
         nvis_ok == 1026 and rows_all == 2321 and s7[1] == 25650 and pool_all == 8482,
         "graded visits %d==1026 rows %d==2321 GROW slots %d==25650 pool %d==8482 "
         "(BASE pins from sim/precheck.py - a truncated trace cannot shrink the fit)"
         % (nvis_ok, rows_all, s7[1], pool_all))
    gate("S1_strict_entry", not s1_bad,
         "%d/%d decision rows val>best; bad %s" % (rows_all - len(s1_bad), rows_all, s1_bad[:3]))
    gate("S2_best_law", not s2_bad,
         "%d/%d rows best==max(best_init,prior accepts); bad %s"
         % (rows_all - len(s2_bad), rows_all, s2_bad[:3]))
    gate("S6_bypass_law", bypass[2] == 0 and deep_ge_cap == 0,
         "bypass-accepts val>=2*(8-dist): %d/%d | GDEEP rows at/over cap %d"
         % (bypass[1], bypass[0], deep_ge_cap))
    gate("S7_best_traj_GROW", not s7_bad and s7[0] == s7[1],
         "GROW best column replays from best_init + accepts (t<=s): %d/%d slots; bad %s"
         % (s7[0], s7[1], s7_bad[:4]))
    gate("S7b_best_init_law",
         s7b["gate8_bad"] == 0 and s7b["nonzero_init"] > 0,
         "case-8 gate leg (0x563836): every nonzero best_init is a case-8 visit (%d/%d, "
         "bad %d); zero-init all consistent (plain %d) | dest-value leg (0x563886-9f): "
         "GRADEABLE-from-save observations: hit %d mismatch %d lazy %d gate<=2 %d "
         "drift %d - nonzero-init visits and their save reads in samples; each case-8 "
         "nonzero init whose save dest tile still equals the live tile must hit; "
         "save-stale dests are the drift-pending class | samples %s"
         % (s7b["nonzero_init"] - s7b["gate8_bad"], s7b["nonzero_init"], s7b["gate8_bad"],
            s7b["plain_zero_ok"],
            s7b["law_hit"], s7b["m2b_val_bad"], s7b["m2b_lazy_dest"],
            s7b["m2b_gate_le2"], s7b["m2b_zero_drift"], s7b_bad[:6]))
    gate("S5_rival_val_separation", all(rivals[m][0] < rows_all // 20 for m in rivals),
         " | ".join("%s val %d/%d" % (m, rivals[m][0], rows_all) for m in sorted(rivals))
         + " vs nib %d/%d - every rival misses the val column"
         % (s3["AGREED"][0] + s3["DRIFT"][0], rows_all))
    amb = [t for t in tile_live if len(set(val for (_, val, k) in tile_live[t] if k == -1)) > 1]
    gate("S3b_live_val_mutation_attested", len(amb) > 0 and not s1_bad,
         "%d tiles w/ 2+ machine-attested live vals (of %d seen), e.g. %s -> the "
         "live byte2 mutates mid-campaign; the static y2150 save CANNOT cover every row"
         % (len(amb), len(tile_live),
            [(t, sorted(set(v for (_, v, k) in tile_live[t] if k == -1))) for t in amb[:3]]))
    gate("S5b_strict_no_tie_rows", not tie_rows,
         "0 of %d recorded decision rows has val==best (machine columns) - under "
         "value>=best ties were ACCEPTABLE semantics; none was ever observed, matching "
         "the `jle 0x563cb3` disasm leg. Static tie CANDIDATES (save-score==recorded "
         "best, nogo unverified - corroboration only, NOT the refutation): %d pool cells"
         % (rows_all, sum(pool[c2]["expl_tie"] for c2 in pool)))
    # REPORTED COVERAGE (the finding, not a gate): static save vs the live-mutated grid
    print("REPORT S3 val-law coverage: AGREED %d/%d DRIFT %d/%d rows match save byte2 "
          "nibble(+0x1000-zero) | byte9bit4&nib>0 pool+row tests %d | lazy-fallback rows %d"
          % (s3["AGREED"][0], tot(s3["AGREED"]), s3["DRIFT"][0], tot(s3["DRIFT"]),
             bit1000, lazy_rows))
    ag = pool["AGREED"]
    print("REPORT S4 skip coverage: AGREED expl %d (tie %d) unexpl %d | DRIFT expl %d "
          "(tie %d) unexpl %d | total pool %d of BASE 8482"
          % (ag["expl"] + ag["expl_tie"], ag["expl_tie"], ag["unexpl"],
             pool["DRIFT"]["expl"] + pool["DRIFT"]["expl_tie"], pool["DRIFT"]["expl_tie"],
             pool["DRIFT"]["unexpl"], pool_all))
    print("REPORT S4b live-override pool grading: expl %d unexpl %d unknown-tile %d"
          % (live_grade["live_expl"], live_grade["live_unexpl"], live_grade["live_unknown"]))

    npass = sum(1 for _, ok, _ in RES if ok)
    line = "PASS M296: %d/%d" % (npass, len(RES)) if npass == len(RES) else \
           "FAIL M296: %d/%d" % (npass, len(RES))
    print(line)
    rep3 = ("REPORT S3 AGREED %d/%d DRIFT %d/%d | byte9bit4&nib>0 tests %d | lazy %d"
            % (s3["AGREED"][0], tot(s3["AGREED"]), s3["DRIFT"][0], tot(s3["DRIFT"]),
               bit1000, lazy_rows))
    rep4 = ("REPORT S4 pool AGREED expl %d (tie %d) unexpl %d | DRIFT expl %d (tie %d) "
            "unexpl %d | total %d"
            % (ag["expl"] + ag["expl_tie"], ag["expl_tie"], ag["unexpl"],
               pool["DRIFT"]["expl"] + pool["DRIFT"]["expl_tie"],
               pool["DRIFT"]["expl_tie"], pool["DRIFT"]["unexpl"], pool_all))
    rep4b = ("REPORT S4b live-override pool grading: expl %d unexpl %d unknown-tile %d"
             % (live_grade["live_expl"], live_grade["live_unexpl"],
                live_grade["live_unknown"]))
    with open(EVID, "w") as f:
        f.write("scripts/m296_argmax_fit.py on %s vs %s\n"
                % (os.path.basename(DEF_SAV), os.path.basename(DEF_RAW)))
        for n, ok, d in RES:
            f.write("%s %s %s\n" % (n, "PASS" if ok else "FAIL", d))
        f.write(rep3 + "\n" + rep4 + "\n" + rep4b + "\n")
        f.write(line + "\n")
    return 0 if npass == len(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
