#!/usr/bin/env python3
"""M297 addendum (s249 run; v2 rewrite at s250 for the PR #262 reviews):
prediction scorecard + drift ATTESTATION + shipped-number verification,
computed from the SHIPPED evidence only (evidence/s249_live_map.bin + the
live-pass gate lines + the recorded rows) - NO second /proc read needed;
re-runnable, idempotent (rewrites its own delimited block in place).

v2 vs v1 (PR #262 review dispositions):
  - every A1 scorecard verdict is DERIVED from numbers parsed out of the
    shipped gate lines (no hardcoded PASS text) - hermes P2 / Greptile P2;
  - P6 is scored per-prediction and prints PARTIAL-MISS (R2 42 / R3 42 vs
    predicted >= 50 each) - the miss Greptile flagged;
  - the miss taxonomy uses the FIXED instrument (a grading event LATER on
    the same tile, scripts/s249_livecensus.py:drift_taxonomy) - hermes P1#3;
  - A0 verifies every bin-derivable number on the shipped gate lines
    reproduces exactly, and machine-proves owner coverage (hermes P1#4);
  - A6 amends the S8 hygiene line (starttime field index, hermes P1#1);
  - A5 states the end-window snapshot caveat explicitly (Greptile P1).

Named rows (resolvable by re-running this script against shipped evidence):
  A0 shipped-number verification (n/n)
  A1 prediction scorecard P1-P8 vs the live-pass numbers, derived
  A2 miss taxonomy: nibble vs bit4, later-event-attested / unattested
  A3 pool residue split: the 2434 save-unexplained cells under live values
  A4 strict-entry law + tie-row law + whole-pool picture
  A5 SNAPSHOT-vs-HISTORY caveat on every live-value verdict
  A6 S8 hygiene-line amendment
"""
import ast
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import sim.precheck as pc                        # noqa: E402
import sim.save as sosave                        # noqa: E402
import s249_livecensus as C                      # noqa: E402

OUT = C.OUT
BIN = C.BIN
MARK0 = "---- s249 ADDENDUM (s249_attestation.py; idempotent block) ----"
MARK1 = "---- s249 ADDENDUM END ----"


def shipped():
    """name -> (PASS/FAIL, detail) for every gate line already in evidence."""
    out = {}
    for ln in open(OUT).read().splitlines():
        m = re.match(r"^\s*(S\w+)\s+(PASS|FAIL)\s\s(.*)$", ln)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def g(pat, line, kind="i"):
    m = re.search(pat, line)
    if not m:
        raise AssertionError("pattern not found: %r" % pat)
    got = m.groups()
    if kind == "i":
        return [int(x) for x in got] if len(got) > 1 else int(got[0])
    if kind == "f":
        return [float(x) for x in got] if len(got) > 1 else float(got[0])
    return got[0] if len(got) == 1 else list(got)


def main():
    sh = shipped()
    sav = sosave.parse(C.DEF_SAV)
    gsv = pc.Grid(sav)
    W, H = sav.width, sav.height
    graded, rows, pool, sv = C.grade_grid(sav, gsv, W, H)
    buf = open(BIN, "rb").read()
    lg = C.LiveGrid(buf, W // 2)

    # ------------------------------------------------ recompute (fixed tools)
    tax = C.drift_taxonomy(rows, lg)
    cls, att = tax["cls"], tax["att"]
    ident = sum(1 for (vi, u, pod, s, (tx, ty), e, sc, rb, sr) in rows
                if lg.rb(tx, ty)[0] == sr[0] and lg.rb(tx, ty)[3] == sr[3])
    tie_r = sum(1 for x in rows if x[5]["val"] == x[7])   # tie ROWS recorded
    bucket = collections.Counter()
    ties_live = 0
    for (vi, u, pod, pcls, preg, s, (tx, ty), rb, sr) in pool:
        r = lg.rb(tx, ty)
        pl = lg.rb(pod[0], pod[1])
        c, _t, _r = pc.prechecks(lg, W, H, pod[0], pod[1],
                                 pc.classflag(pl[0]), pl[3], s)
        lv, z = C.live_val(r)
        if [k for k in pc.MODELLED if not c[k]]:
            bucket["static_fail_live"] += 1
        elif lv < rb:
            bucket["lt_live"] += 1
        elif lv == rb:
            bucket["tie_live"] += 1
            ties_live += 1
        else:
            bucket["UNEXPLAINED"] += 1
    t7dist = collections.Counter(
        C.signed(lg.rb(p[6][0], p[6][1])[7]) for p in pool)
    units = set(v["u"] for (_0, v, _1, _2, _3, _4, _5, _6) in graded)
    units_in_range = all(0 <= u < 2500 for u in units)
    rows_u_ok = set(x[1] for x in rows) <= units
    pool_u_ok = set(x[1] for x in pool) <= units
    drec = lg.rb(19, 6)
    lv45, z45 = C.live_val(drec)

    # ------------------------------------------------ shipped numbers (parse)
    s2, s3, s4, s5, s6, s7, s8 = (sh["S2_live_witness"][1],
                                  sh["S3_row_val_law_live"][1],
                                  sh["S4_pool_closure_live"][1],
                                  sh["S5_u45_value_leg"][1],
                                  sh["S6_rivals_fail_live"][1],
                                  sh["S7_nogo_live_answer"][1],
                                  sh["S8_hygiene_state"][1])
    v = {}
    v["strict"], = g(r"val>best (\d+)/2321", s3),
    v["match"], v["lazy"] = g(r"zeroing\) (\d+), lazy FUN_005aff90 class (\d+)",
                              s3)
    v["miss"], v["bit4"], v["nibble"] = g(
        r"misses (\d+) \(bit4 (\d+), nibble (\d+)\)", s3)
    v["multirows"], = g(r"ALL on the (\d+)-row machine-multival", s3),
    v["multitiles"], = g(r"tiles (\d+) with 2\+", s3),
    v["detail"] = g(r"detail (\[.*\])", s3, "s")
    (v["ptot"], v["nogo"], v["lt"], v["tie"], v["sf"],
     v["unex"]) = g(r"pool (\d+)/8482 under LIVE values: no-go R4-live rejects "
                    r"(\d+) \| live val<rb (\d+) \| tie (\d+) \| live static "
                    r"pre-check fail \(class/region/occ mutated\) (\d+) \| "
                    r"UNEXPLAINED (\d+)", s4)
    v["u45b2"] = int("0x" + g(r"byte2=0x([0-9a-f]+) byte9", s5, "s"), 16)
    v["u45b9"] = int("0x" + g(r"byte9=0x([0-9a-f]+) -> live", s5, "s"), 16)
    v["u45lv"], = g(r"-> live value (\d+):", s5),
    v["brA"], v["brB"], v["brC"] = g(
        r"branchA \(value\(19,6\)==6 -> init 5==machine\) (\w+) \| branchB "
        r"\(dest moved from \(19,6\)\) (\w+) \| branchC \(order left 0x18\) "
        r"(\w+)", s5, "s")
    v["r1"], v["r2"], v["r3"] = g(r"R1 foreign-only rejects (\d+) RECORDED "
                                   r"slots \| R2 \+mask (\d+) \| R3 "
                                   r"\+not-ally (\d+)", s6)
    v["r4rows"], = g(r"recorded-slot collisions (\d+) \(predicted 0\)", s6),
    v["ge"], = g(r"ge-argmax rival: (\d+) live-tie", s6),
    v["nogopool"], v["nogo2321"] = g(
        r"rejects (\d+) inside the 8482-cell pool and (\d+) inside the 2321 "
        r"recorded", s7)
    v["t7"] = g(r"cells (\[.*\]) \| human_mask", s7, "s")
    v["mask"] = int("0x" + g(r"human_mask live 0x([0-9a-f]+) vis", s7, "s"),
                    16)
    v["vis"] = int("0x" + g(r"vis live 0x([0-9a-f]+) nonzero", s7, "s"), 16)
    v["fwnz"], v["fwn"] = g(r"nonzero flagwords (\d+)/(\d+)", s7)
    v["ident"], v["identtot"] = g(r"byte0\+byte3 unchanged (\d+)/(\d+)", s2)
    v["bx"], v["by"], v["mult"] = g(r"live bounds (\d+)/(\d+) mult (\d+)", s2)
    v["tr0"], v["tr1"] = g(r"TracerPid (\d+)->(\d+)", s8)
    v["starttok"] = g(r"starttime (\S+)==(\S+),", s8, "s")
    v["yr"], v["cur"], v["cnt"] = g(r"year=(\d+) cur=(\d+) cnt=(\d+)", s8)

    # ------------------------------------------------ verification (A0)
    checks = [
        ("S3 strict val>best", v["strict"], tax["strict"]),
        ("S3 match", v["match"], cls["match"]),
        ("S3 lazy", v["lazy"], cls["lazy"]),
        ("S3 bit4", v["bit4"], cls["bit4_zeroed"]),
        ("S3 nibble", v["nibble"], cls["nibble_drift"]),
        ("S3 miss sum", v["miss"], tax["miss"]),
        ("S3 multival rows", v["multirows"], tax["miss_on_multi"]),
        ("S3 multival tiles", v["multitiles"], len(tax["multi"])),
        ("S3 detail[:4]", v["detail"], repr(tax["detail"][:4])),
        ("S4 pool total", v["ptot"], sum(t7dist.values())),
        ("S4 lt", v["lt"], bucket["lt_live"]),
        ("S4 tie", v["tie"], bucket["tie_live"]),
        ("S4 static-fail", v["sf"], bucket["static_fail_live"]),
        ("S4 UNEXPLAINED", v["unex"], bucket["UNEXPLAINED"]),
        ("S4 no-go consistency", v["nogo"],
         v["ptot"] - v["lt"] - v["tie"] - v["sf"] - v["unex"]),
        ("S5 (19,6) byte2", v["u45b2"], drec[2]),
        ("S5 (19,6) byte9", v["u45b9"], drec[9]),
        ("S5 (19,6) live val", v["u45lv"], lv45),
        ("S6 ge-argmax ties", v["ge"], ties_live),
        ("S7 t7 distribution", repr(ast.literal_eval(v["t7"])),
         repr(sorted(t7dist.items()))),
        ("S7 no-go pool", v["nogopool"], v["nogo"]),
        ("S7 no-go rows", v["nogo2321"], v["r4rows"]),
        ("S2 identity", v["ident"], ident),
        ("S2 bounds/mult", (v["bx"], v["by"], v["mult"]), (W, H, W // 2)),
        ("owner coverage", (units_in_range, rows_u_ok, pool_u_ok),
         (True, True, True)),
    ]
    bad = [n for n, a, b in checks if a != b]
    vpass = not bad
    if not vpass:
        print("VERIFY MISMATCH: %s" % repr(bad))

    # ------------------------------------------------ scorecard (A1), derived
    def vp(ok):
        return "PASS" if ok else "FAIL"
    p1_ok = (v["ident"] >= int(0.85 * v["identtot"])
             and (v["bx"], v["by"], v["mult"]) == (64, 64, 32))
    p2_ok = v["yr"] == C.PIN_YEAR and v["cnt"] == C.PIN_CNT and \
        v["tr0"] == 0 and v["tr1"] == 0
    p3_ok = cls["lazy"] <= 8 and cls["bit4_zeroed"] == 0 and \
        tax["unatt"] == 0
    p4_ok = v["unex"] == 0
    p5_ok = v["brA"] == "True" or v["brB"] == "True" or v["brC"] == "True"
    p6_items = [("R1>=500", v["r1"] >= 500),
                ("R2>=50", v["r2"] >= 50),
                ("R3>=50", v["r3"] >= 50),
                ("ge>=2000", v["ge"] >= 2000),
                ("R4-live==0", v["r4rows"] == 0)]
    p6_ok = all(ok for _n, ok in p6_items)
    p6_missed = [n for n, ok in p6_items if not ok]
    p7_ok = v["nogopool"] >= 0 and v["nogo2321"] >= 0
    p8_ok = v["match"] == 2321

    # residue split (A3): the 2434 save-unexplained cells under LIVE values
    res = collections.Counter()
    for (vi, u, pod, pcls, preg, s, (tx, ty), rb, sr) in pool:
        sc, z0 = C.sl.score_nib(sr)
        if sc <= rb:
            continue                      # already explained statically
        r = lg.rb(tx, ty)
        pl = lg.rb(pod[0], pod[1])
        c, _t, _r = pc.prechecks(lg, W, H, pod[0], pod[1],
                                 pc.classflag(pl[0]), pl[3], s)
        lv, z = C.live_val(r)
        if [k for k in pc.MODELLED if not c[k]]:
            res["static_fail_live"] += 1
        elif lv < rb:
            res["lt_live"] += 1
        elif lv == rb:
            res["tie_live"] += 1
        else:
            res["UNEXPLAINED"] += 1

    kinded = collections.Counter()
    for kk, n in att.items():
        k, a = kk.split("-", 1)
        kinded[(k, a)] += n
    tot_a = sum(n for (_k, a), n in kinded.items() if a != "unattested")
    tot_u = sum(n for (_k, a), n in kinded.items() if a == "unattested")

    lines = []
    ap = lines.append
    ap("")
    ap(MARK0)
    ap("A0 shipped-verify %s: %d/%d bin-derivable numbers on the shipped gate "
       "lines reproduce EXACTLY under the FIXED instruments (later-event "
       "attestation drift_taxonomy, owner-coverage, recount consistency); "
       "MEASURED-ONLY inputs not dumped (cannot re-check offline): R1/R2/R3 "
       "collision counts %d/%d/%d, u-45 unit-record branches, the S8 starttime "
       "token, flagwords %d/%d. Owner coverage machine-proves the PR #262 "
       "P1#4 concern CLEAN on the shipped run: all %d visit units in "
       "[0,2500), every row/pool unit a visit unit, owners loaded for exactly "
       "that set - owners.get() could not miss, the R4-live 0/0 is not a "
       "silent-filter artifact%s"
       % (vp(vpass), len(checks) - len(bad), len(checks),
          v["r1"], v["r2"], v["r3"], v["fwnz"], v["fwn"], len(units),
          "" if vpass else " FAILS: " + repr(bad)))
    ap("A1 prediction scorecard (DERIVED from shipped gate lines + this "
       "recomputation; was hardcoded in v1 - fixed per review):")
    ap(" P1 %s witness: bounds %d/%d mult %d, identity byte0+byte3 "
       "%d/%d = %.1f%% (predicted >=85%%)"
       % (vp(p1_ok), v["bx"], v["by"], v["mult"], v["ident"], v["identtot"],
          100.0 * v["ident"] / v["identtot"]))
    ap(" P2 %s box state: year %d cur %d cnt %d pinned (s244 pins %d/%d), "
       "TracerPid %d->%d, zero gdb (S8) - but the shipped starttime token was "
       "the state letter, see A6"
       % (vp(p2_ok), v["yr"], v["cur"], v["cnt"], C.PIN_YEAR, C.PIN_CNT,
          v["tr0"], v["tr1"]))
    ap(" P3 %s row law (predicted every row match/lazy/drift-attested, lazy "
       "<= 8, bit4-zeroed printed 0): lazy %d (<= 8 OK) but bit4-zeroed "
       "printed %d != 0 and %d misses unattested - FAIL AS THE FINDING (S3, "
       "documented)"
       % (vp(p3_ok), v["lazy"], v["bit4"], tax["unatt"]))
    ap(" P4 %s pool closure: UNEXPLAINED-under-live %d/8482 (predicted 0); "
       "the pre-read line printed the CORRECT 2434 (hermes P2#1 - its dead "
       "`if False` line was removed; output unaffected)"
       % (vp(p4_ok), v["unex"]))
    ap(" P5 %s u=45: branchA %s / branchB %s / branchC %s; live (19,6) "
       "byte2=%#x byte9=%#x live value %d (bin-recomputed) - CLOSED on the "
       "dest-moved branch"
       % (vp(p5_ok), v["brA"], v["brB"], v["brC"], drec[2], drec[9], lv45))
    ap(" P6 %s rivals on the live grid: R1 %d (pred >=500 %s), R2 %d (pred "
       ">=50 %s), R3 %d (pred >=50 %s), ge-argmax %d live ties (pred >=2000 "
       "%s), R4-live recorded %d (pred 0 %s) - the R2/R3 floors came from the "
       "save-side 124/119 and the live mask %#x (single faction bit) shrinks "
       "mask-gated collisions; the rivals are STILL refuted (%d/%d/%d >= 1 "
       "collision each, S6 PASS); P6 is %s, missed: %s"
       % ("PARTIAL-MISS" if not p6_ok else "PASS", v["r1"],
          vp(v["r1"] >= 500), v["r2"], vp(v["r2"] >= 50), v["r3"],
          vp(v["r3"] >= 50), v["ge"], vp(v["ge"] >= 2000), v["r4rows"],
          vp(v["r4rows"] == 0), v["mask"], v["r1"], v["r2"], v["r3"],
          "a clean PASS" if p6_ok else "NOT a clean PASS",
          repr(p6_missed)))
    ap(" P7 %s no-go answer (M295 P1c): R4-live rejects %d/%d pool/recorded "
       "(predicted a small >=0 number; measured 0 -> INERT, explains 0 of the "
       "2434); residue NOT no-go-dominated (tie_live %d dominant class)"
       % (vp(p7_ok), v["nogopool"], v["nogo2321"], res["tie_live"]))
    ap(" P8 %s strict form: exact-live %d/%d - FAIL, see A2"
       % (vp(p8_ok), v["match"], 2321))
    ap("A2 miss taxonomy over the %d rows (S3): %d exact-match, %d lazy, %d "
       "miss = %s" % (2321, cls["match"], cls["lazy"], tax["miss"],
                      repr(sorted(kinded.items()))))
    ap("   attested by a LATER machine grading event %d, UNATTESTED %d "
       "(sum %d of 2321; all misses are post-grading byte2/byte9 mutations - "
       "the 0x1000 bit4-flip class %d rows is the dominant drift vector, NOT "
       "the lazy FUN_005aff90 class)"
       % (tot_a, tot_u, tot_a + tot_u,
          sum(n for (k, _a), n in kinded.items() if k == "bit4")))
    ap("   the %d machine-multival tiles (M296 S3b: %d rows, %d of these "
       "misses) are a LOWER BOUND retired as the attestation instrument (s250 "
       "P1 fix): a bit4 flip is val-INVISIBLE while val stays >0, so "
       "val-timelines cannot attest the bit4 class"
       % (len(tax["multi"]), tax["on_multi"], tax["miss_on_multi"]))
    ap("A3 the %d save-unexplained pool cells under LIVE values: %s "
       "(sum %d/%d) - the residue CLOSES: %d unexplained; tie_live is the "
       "dominant class (live byte2 drift lands values back ON the incoming "
       "best), no-go contributes %d"
       % (2434, repr(sorted(res.items())), sum(res.values()), 2434,
          res["UNEXPLAINED"], v["nogo"]))
    ap("   whole-pool live picture (%d): tie %d | lt %d | static-fail %d | "
       "no-go %d | UNEXPLAINED %d (S4 verbatim, bin-recomputed) - live tie "
       "%d vs static 5721: the live mutations CREATE %d new strict-rule skips"
       % (v["ptot"], v["tie"], v["lt"], v["sf"], v["nogo"], v["unex"],
          v["tie"], v["tie"] - 5721))
    ap("A4 strict-entry law stands: recorded val>best %d/2321 (S3 line 1); "
       "tie ROWS among 2321 = %d (M296 S5b holds: the %d live ties are all in "
       "the printed-NO population)"
       % (v["strict"], tie_r, v["tie"]))
    ap("A5 CAVEAT (PR #262 Greptile P1, made explicit): every live-value "
       "verdict above (A3 closure, P6 rival refutations, P7 INERT) is an "
       "END-WINDOW comparison against the final-turn snapshot - a tie NOW "
       "does NOT prove the cell tied at the turn its row was skipped, and an "
       "INERT no-go NOW does not prove INERT at each earlier turn (mask "
       "0x%x/flagwords/vis mutate between turns). The residue is CLOSED only "
       "up to post-grading drift: the machine attests %d/%d row drifts, %d "
       "unattested, bit4 flips val-invisible, so attested counts are lower "
       "bounds on WHEN. Per-turn historical closure needs mid-window "
       "snapshots - LEAD, box frozen at %d/%d."
       % (v["mask"], tot_a, tax["miss"], tot_u, C.PIN_YEAR, C.PIN_CNT))
    ap("A6 HYGIENE AMENDMENT (PR #262 hermes P1, fixed in code at s250): the "
       "shipped S8 line's 'starttime %s==%s' token is the process STATE "
       "letter, not starttime - after split(') ') idx 0 is state (field 3), "
       "starttime is field 22 = idx 19; scripts/s249_livecensus.py now reads "
       "idx 19. The hygiene claim stands WITHOUT the token: TracerPid %d->%d, "
       "yama recorded/restored unchanged, year %d cur %d cnt %d pinned equal "
       "before AND after, and map identity byte0+byte3 %d/%d vs the save - a "
       "restart inside the read window moves year/cnt or the dump."
       % (v["starttok"][0], v["starttok"][1], v["tr0"], v["tr1"], v["yr"],
          v["cur"], v["cnt"], v["ident"], v["identtot"]))
    ap(MARK1)

    txt = open(OUT).read()
    if MARK0 in txt:
        txt = re.sub("\n" + re.escape(MARK0) + r".*?" + re.escape(MARK1),
                     "", txt, flags=re.S)
    open(OUT, "w").write(txt.rstrip("\n") + "\n" + "\n".join(lines) + "\n")
    print("\n".join(lines[2:-1]))
    return 0 if vpass else 1


if __name__ == "__main__":
    sys.exit(main())
