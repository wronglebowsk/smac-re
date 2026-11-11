#!/usr/bin/env python3
"""B17 (s248): the pod-scan loop DECISION CORE made executable (R2's "the pod picks
its slot" slice). The first sim rung that COMPOSES B16's head-chain grid
(sim.precheck), the M296 value-vs-best ARGMAX chain, and B15's price_gate
(sim.gatetables) into ONE replay over the recorded gate-row grid:

  best_init law (M296 0x563836-0x56389f, byte pins evidence/m296_init_window.txt):
    best = 0 for EVERY scan; the override fires only for case-8 pods whose unit
    ORDER byte (+17)==0x18 (move-to-base, NAMED 0x4d3770) with wrapped-diff to
    the dest base (+20/+28) > 2 -> best_init = value(dest tile)-1.
  per-slot leg (0x563c02-0x563caa): val = rec byte2 HIGH nibble (0 when byte9
    bit4; nibble 0 with machine val > 0 = the lazy FUN_005aff90 exception);
    price_gate() (B15 closed form) classifies the slot accept-bypass / deep-gate;
    an ACCEPT stores best = val (0x563caa) and moves the winner to this slot;
    the loop advances through all 25 ring slots regardless.
  WHAT THE MODEL SUPPLIES: best_init, the best/win trajectory, the accept set,
    the winner. WHAT IT READS FROM THE RECORD (declared inputs, as in B15's
    parity): per-slot machine val/dist and the gate bytes (mult/gate/verd/
    basecnt/unit24/tiles) printed at 0x563c3d - and the ONE live-init scan
    (u=45, save-stale dest, M296 S7b) whose best_init the y2150 save cannot know.

Parity target = evidence/m294_gate_rows_raw.txt (the m294 window on
programs/saves/m54b_clean.SAV; B16 transposition law via sim.precheck).
DECLARED UNMODELED (unchanged, RESIDUE lines): the 0x4e3c00(owner,X,Y) no-go
(M295, live question OPEN), live byte2 mutation (390 rows / 2434 pool cells),
the u=45 live value leg, the lazy fallback, the dispatch legs downstream of
the winner (B14).  No box, no /proc, no gdb, no game-binary load.
"""
import argparse
import collections
import os
import struct
import sys

from . import precheck as pc
from . import gatetables as gt
from . import save as sosave

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SAV = os.path.join(REPO, "programs", "saves", "m54b_clean.SAV")
DEF_RAW = os.path.join(REPO, "evidence", "m294_gate_rows_raw.txt")

# BASE pins, merged history: m296 S0 (evidence/m296_argmax_fit.txt:2), the m294
# window counts (NAMED.md ## M294: 2321 decision slots, 260 accepts), the 61
# bypass slots (m296 S6) and the S7b buckets (evidence/m296_argmax_fit.txt:7).
# A truncated trace cannot shrink the fit.
PIN_VISITS = 1026
PIN_DEC_ROWS = 2321
PIN_GROW_SLOTS = 25650
PIN_POOL = 8482
PIN_ACCEPTS = 260
PIN_BYPASS = 61
PIN_TIE_POOL = 5721
PIN_DISPT = 201


def score_nib(r):
    """0x46e770 law on a 44-B record: byte2 HIGH nibble, 0 when dword[+8] bit
    0x1000 (byte9 bit4) is set; returns (val, zeroed_by_1000)."""
    z = r[9] % 32 >= 16
    return (0 if z else r[2] // 16), z


def load_visits(path):
    """raw rows split HUB-by-HUB into visits; decision inputs per slot, first
    row wins (m294 instrument law: one event per slot)."""
    vis = []
    cur = None
    for ln in open(path):
        w = ln.split()
        if not w:
            continue
        k = w[0]
        d = {}
        for kv in w[1:]:
            if "=" in kv:
                a, b = kv.split("=", 1)
                d[a] = b
        if k == "HUB":
            cur = {"u": int(d.get("u", "-1")), "disp": None, "grow": {},
                   "deep": {}, "acc": {}}
            vis.append(cur)
        elif cur is None:
            continue
        elif k == "DISP":
            if cur["disp"] is None and {"x", "y", "esi"} <= set(d):
                cur["disp"] = (int(d["x"]), int(d["y"]), int(d["esi"]))
        elif k == "GROW":
            cur["grow"][int(d["slot"])] = (int(d["best"]), int(d["win"]))
        elif k in ("GDEEP", "GACC"):
            s = int(d["slot"])
            e = {"x": int(d["x"]), "y": int(d["y"]), "val": int(d["val"]),
                 "best": int(d["best"]), "dist": int(d["dist"]),
                 "mult": int(d["mult"]), "gate": int(d["gate"]),
                 "verd": int(d["verd"]), "case": int(d["case"]),
                 "basecnt": int(d["basecnt"]), "unit24": int(d["unit24"]),
                 "tiles": int(d["tiles"])}
            tgt = cur["deep"] if k == "GDEEP" else cur["acc"]
            if s not in tgt:
                tgt[s] = e
    return vis


def decide(best_init, events):
    """THE leg, executable. events: slot -> recorded machine inputs (val + gate
    bytes). Returns (accepts [(slot, branch, val)], traj slot->(best_after,
    win_after), final_win, final_best). best/win start at (best_init, -1) as
    the prologue stores them (0x563836-0x56389f); only an ACCEPT moves them,
    at 0x563caa."""
    best, win = best_init, -1
    accepts, traj = [], []
    for s in range(25):
        e = events.get(s)
        if e is not None:
            outcome, branch = gt.price_gate(
                e["val"], best, e["dist"], e["mult"], e["basecnt"],
                e["verd"], e["gate"], e["case"], e["unit24"], e["tiles"])
            if outcome == "accept":
                accepts.append((s, branch, e["val"]))
                best, win = e["val"], s
        traj.append((best, win))
    return accepts, traj, win, best


def _agree(v, g, W):
    """B16/M296 visit classification: pod recovery + save-vs-rows class/region
    (decision-row x/y read TRANSPOSED - the B16 reader law)."""
    dv = [{"slot": s, "x": e["y"], "y": e["x"]}
          for s, e in list(v["deep"].items()) + list(v["acc"].items())]
    pod = pc.recover_pod({"dec": dv}, W)
    if pod is None:
        return None
    px, py = pod
    pr = g.rb(px, py)
    pcls, preg = pc.classflag(pr[0]), pr[3]
    cs = set(pc.classflag(g.rb(d["x"], d["y"])[0]) for d in dv)
    rs = set(g.rb(d["x"], d["y"])[3] for d in dv)
    ok = (len(cs) == 1 and len(rs) == 1 and cs.pop() == pcls and rs.pop() == preg)
    return px, py, pcls, preg, ok


def _save_dest(sav, g, W, H, u):
    """the unit's move-to-base dest record + order byte, from the save array.
    Units founded AFTER the y2150 save have NO save record (the trace names
    u >= len(sav.units)): return (None, 0, 0, None) - unrelated bytes must
    never be graded as unit state (Greptile #261 P2)."""
    if not (0 <= u < len(sav.units)):
        return None, 0, 0, None
    o = sav.units_off + sosave.UNIT_LEN * u
    order = sav.data[o + 17]
    dx = struct.unpack_from("<H", sav.data, o + 20)[0]
    dy = struct.unpack_from("<H", sav.data, o + 28)[0]
    drec = g.rb(dx, dy) if (0 <= dx < W and 0 <= dy < H) else None
    return order, dx, dy, drec


def _law_init(sav, g, W, H, u, case_row, px, py):
    """the save+law best_init PREDICTION (model input): 0 unless case-8 +
    order 0x18 + wrapped-diff>2; then value(save-view dest)-1 - or None when
    the save-view dest value is 0 (lazy nibble or byte9-bit4 zeroed): the live
    dest value is then UNSEEABLE from the y2150 save (the M296 S7b class), so
    the replay takes the machine-recorded init as a DECLARED input."""
    if case_row != 8:
        return 0
    order, dx, dy, drec = _save_dest(sav, g, W, H, u)
    if order is None:
        return None  # unit founded after the save: the law cannot grade it
    if order != 0x18 or drec is None:
        return 0
    wd = max(min(abs(dx - px), W - abs(dx - px)),
             min(abs(dy - py), H - abs(dy - py)))
    if wd <= 2:
        return 0
    sc, z = score_nib(drec)
    if sc == 0:
        return None  # save-view 0: live value ungradeable (lazy OR 0x1000-zero)
    return sc - 1


def _init_buckets(sav, g, W, H, vis):
    """M296 S7b recomputed by the sim, SAME bucket names and semantics as
    scripts/m296_argmax_fit.py (the merged review is the authority)."""
    bk = collections.Counter()
    samples = []
    for vi, v in enumerate(vis):
        if len(v["grow"]) != 25 or not (v["deep"] or v["acc"]):
            continue
        dec = sorted(set(v["deep"]) | set(v["acc"]))
        first = v["deep"].get(dec[0]) or v["acc"][dec[0]]
        ag = _agree(v, g, W)
        if ag is None:
            continue
        px, py = ag[0], ag[1]
        m_init = first["best"]
        order, dx, dy, drec = _save_dest(sav, g, W, H, v["u"])
        nib = drec[2] // 16 if drec is not None else None
        m_calc = None
        if drec is not None and not (nib == 0 and drec[9] % 32 < 16):
            sc, _z = score_nib(drec)
            m_calc = sc - 1
        if m_init != 0:
            bk["nonzero_init"] += 1
            if not (0 <= v["u"] < len(sav.units)):
                # unit founded after the save: case leg still gradeable from
                # the recorded case column; the VALUE leg has no save record
                if first["case"] != 8:
                    bk["gate8_bad"] += 1
                    samples.append(("CASE8", vi, v["u"], (px, py), (dx, dy),
                                    m_init, first["case"]))
                else:
                    bk["drift_pending"] += 1
                    samples.append(("UNGRA", vi, v["u"], (px, py), (dx, dy),
                                    m_init, None))
                continue
            if first["case"] != 8:
                bk["gate8_bad"] += 1
                samples.append(("CASE8", vi, v["u"], (px, py), (dx, dy), m_init,
                                first["case"]))
            elif m_calc is None:
                bk["drift_pending"] += 1
                samples.append(("DRIFT", vi, v["u"], (px, py), (dx, dy), m_init,
                                None))
            elif m_calc == m_init:
                bk["law_hit"] += 1
            else:
                bk["m2b_val_bad"] += 1
                samples.append(("VAL", vi, v["u"], (px, py), (dx, dy), m_init,
                                m_calc))
        elif not (0 <= v["u"] < len(sav.units)):
            bk["not_in_save"] += 1
        elif first["case"] == 8 and order == 0x18 and drec is not None:
            wd = max(min(abs(dx - px), W - abs(dx - px)),
                     min(abs(dy - py), H - abs(dy - py)))
            if wd <= 2:
                bk["m2b_gate_le2"] += 1
            elif nib == 1:
                bk["law_hit"] += 1
            elif nib == 0:
                bk["m2b_lazy_dest"] += 1
            else:
                bk["m2b_zero_drift"] += 1
        else:
            bk["plain_zero_ok"] += 1
    return bk, samples


def report(sav_path, raw_path):
    """run every gate; returns (all_ok, list_of(name, ok, detail))."""
    sav = sosave.parse(sav_path)
    g = pc.Grid(sav)
    W, H = sav.width, sav.height
    vis = load_visits(raw_path)
    R = []

    def gate(name, ok, detail):
        R.append((name, bool(ok), detail))

    # ---- graded set (B16 class law) + model/machine/replay inits -------------
    graded = []
    for vi, v in enumerate(vis):
        if len(v["grow"]) != 25 or not (v["deep"] or v["acc"]):
            continue
        a = _agree(v, g, W)
        if a is None:
            continue
        px, py, pcls, preg, ok = a
        dec = sorted(set(v["deep"]) | set(v["acc"]))
        first = v["deep"].get(dec[0]) or v["acc"][dec[0]]
        law_init = _law_init(sav, g, W, H, v["u"], first["case"], px, py)
        m_init = first["best"]
        # DECLARED-live init class (M296 S7b, both directions): a save-view
        # dest value of 0 (lazy nibble / 0x1000-zero) is ungradeable, AND any
        # nonzero MACHINE init means the override fired live on an order the
        # y2150 save no longer reflects - the machine column is the input.
        if law_init is None or m_init != 0:
            replay_init = m_init
        else:
            replay_init = law_init
        graded.append((vi, v, (px, py), pcls, preg,
                       "AGREED" if ok else "DRIFT", dec, replay_init, law_init))

    nvis = len(graded)
    ndec = sum(len(gr[6]) for gr in graded)
    nacc = sum(len(gr[1]["acc"]) for gr in graded)
    nbyp = sum(1 for gr in graded
               for s in gr[1]["acc"] if s not in gr[1]["deep"])
    model_hit = sum(1 for gr in graded if gr[8] is not None and gr[7] == gr[8])
    declared = sum(1 for gr in graded if gr[8] is None or gr[7] != gr[8])
    gate("G1_coverage_pins",
         nvis == PIN_VISITS and ndec == PIN_DEC_ROWS
         and 25 * nvis == PIN_GROW_SLOTS and nacc == PIN_ACCEPTS
         and nbyp == PIN_BYPASS,
         "graded %d/%d decision-slots %d/%d GROW %d/%d accepts %d/%d bypass %d/%d "
         "(BASE pins m296 S0 + NAMED ## M294)"
         % (nvis, PIN_VISITS, ndec, PIN_DEC_ROWS, 25 * nvis, PIN_GROW_SLOTS,
            nacc, PIN_ACCEPTS, nbyp, PIN_BYPASS))

    # ---- G2 best-init law, buckets per M296 S7b ------------------------------
    bk, samples = _init_buckets(sav, g, W, H, vis)
    gate("G2_best_init_law",
         bk["gate8_bad"] == 0 and bk["nonzero_init"] == 1
         and bk["m2b_val_bad"] == 1 and bk["m2b_lazy_dest"] == 2
         and bk["m2b_gate_le2"] == 0 and bk["m2b_zero_drift"] == 0
         and bk["drift_pending"] == 0
         and bk["plain_zero_ok"] + bk.get("not_in_save", 0) == 1023
         and bk.get("not_in_save", 0) == 362
         and model_hit == 990 and declared == 36
         and model_hit + declared == PIN_VISITS,
         "law-vs-machine on %d/%d scans (the zero-leg `cmp esi,8` needs NO unit "
         "record - 329 of these units postdate the save); the %d case-8 scans are "
         "the m2b gradeability class: 3 save-recorded (u=45 VAL-mismatch machine-5 "
         "vs save-dest -1 = DECLARED save-stale, value leg OPEN; 2 save-invisible "
         "m2b dests) + 33 whose unit postdates the save (machine init 0 for all -> "
         "DECLARED input); not_in_save scans total 362; case-8 leg 1/1; buckets "
         "%s; samples %s"
         % (model_hit, model_hit + declared, 36,
            dict(bk), samples[:2]))

    # ---- G3/G4 best & win trajectories over every graded GROW slot -----------
    best_ok = win_ok = ntot = 0
    b_bad, w_bad, s2_bad = [], [], []
    s2_tot = 0
    replays = []
    for vi, v, pod, pcls, preg, cls, dec, init, law_init in graded:
        events = {s: (v["deep"].get(s) or v["acc"][s])
                  for s in set(v["deep"]) | set(v["acc"])}
        accepts, traj, fwin, fbest = decide(init, events)
        replays.append((vi, v, pod, fwin, cls))
        for s in range(25):
            rb, rw = v["grow"][s]
            ntot += 1
            if traj[s][0] == rb:
                best_ok += 1
            elif len(b_bad) < 6:
                b_bad.append((vi, v["u"], s, rb, traj[s][0]))
            if traj[s][1] == rw:
                win_ok += 1
            elif len(w_bad) < 6:
                w_bad.append((vi, v["u"], s, rw, traj[s][1]))
        # M296 S2 law on the REPLAYED best: every decision row's INCOMING best
        # (recorded column) == the replayed best BEFORE its slot (t<s class).
        for s, e in events.items():
            s2_tot += 1
            want = init if s == 0 else traj[s - 1][0]
            if e["best"] != want and len(s2_bad) < 6:
                s2_bad.append((vi, v["u"], s, e["best"], want))
    gate("G3_best_traj_GROW", best_ok == ntot and not b_bad and not s2_bad,
         "replayed best == recorded GROW best on %d/%d slots AND the M296-S2 "
         "incoming-best check (recorded row best == replayed best-before-slot) "
         "holds on %d/%d decision rows; bad %s %s"
         % (best_ok, ntot, s2_tot - len(s2_bad), s2_tot, b_bad[:4], s2_bad[:4]))
    gate("G4_win_traj_GROW", win_ok == ntot and not w_bad,
         "replayed winner-so-far == recorded GROW win on %d/%d slots; bad %s"
         % (win_ok, ntot, w_bad[:4]))

    # ---- G5 accept set: the composed leg predicts the GACC rows ---------------
    acc_hit = acc_rec = 0
    a_bad = []
    deep_ge_cap = 0
    branches = collections.Counter()
    for vi, v, pod, pcls, preg, cls, dec, init, law_init in graded:
        events = {s: (v["deep"].get(s) or v["acc"][s])
                  for s in set(v["deep"]) | set(v["acc"])}
        accepts, traj, fwin, fbest = decide(init, events)
        pred = set(s for s, br, val in accepts)
        for s, br, val in accepts:
            branches[br] += 1
        rec = set(v["acc"])
        acc_rec += len(rec)
        acc_hit += len(pred & rec)
        if pred != rec and len(a_bad) < 6:
            a_bad.append((vi, v["u"], sorted(pred ^ rec)))
        for s, e in v["deep"].items():
            if e["val"] >= 2 * (8 - e["dist"]):
                deep_ge_cap += 1
    gate("G5_accept_funnel", acc_hit == acc_rec == PIN_ACCEPTS and not a_bad
         and deep_ge_cap == 0,
         "predicted accepts == recorded GACC %d/%d (bypass %d, gate-legs %s); "
         "GDEEP rows at/over cap %d (the 0x563c38 bypass prints NO GDEEP)"
         % (acc_hit, PIN_ACCEPTS, branches["bypass"],
            {k: n for k, n in branches.items() if k != "bypass"}, deep_ge_cap))

    # ---- G6 winner == DISP esi (the row the dispatch consumes) ----------------
    disp_total = sum(1 for v in vis if v["disp"] is not None)
    dw_ok = dw_tot = dw_no = 0
    d_bad = []
    for vi, v, pod, fwin, cls in replays:
        if v["disp"] is None:
            continue
        dw_tot += 1
        if (v["disp"][0], v["disp"][1]) != tuple(pod):
            dw_no += 1     # DISP tile != recovered pod: B16 drift class
        elif fwin == v["disp"][2]:
            dw_ok += 1
        elif len(d_bad) < 6:
            d_bad.append((v["u"], fwin, v["disp"][2]))
    gate("G6_winner_vs_DISP", disp_total == PIN_DISPT and dw_tot == PIN_DISPT
         and dw_no == 0 and dw_ok == dw_tot and not d_bad,
         "DISP rows window-wide MEASURED %d (pin %d); all %d fall inside graded "
         "visits, predicted winner == DISP esi on %d/%d (%d skipped: DISP tile "
         "!= recovered pod, B16 drift class); bad %s"
         % (disp_total, PIN_DISPT, dw_tot, dw_ok, dw_tot, dw_no, d_bad[:4]))

    # ---- G7 val law from the SAVE view + strictness floor ----------------------
    s3 = {"AGREED": [0, 0], "DRIFT": [0, 0]}
    lazy = b1k_row = b1k_pool = tie_rows = strict_bad = 0
    pool = collections.Counter()
    pool_tot = 0
    for vi, v, (px, py), pcls, preg, cls, dec, init, law_init in graded:
        decset = set(dec)
        accv = {s: e["val"] for s, e in v["acc"].items()}
        for s in range(25):
            c, (tx, ty), r = pc.prechecks(g, W, H, px, py, pcls, preg, s)
            sc, z = score_nib(r)
            if z and r[2] // 16 > 0:
                if s in decset:
                    b1k_row += 1
                else:
                    b1k_pool += 1
            rb = max([accv[t] for t in accv if t < s] + [init])
            e = v["deep"].get(s) or v["acc"].get(s)
            if s in decset:
                rv = e["val"]
                if sc == rv:
                    s3[cls][0] += 1
                else:
                    s3[cls][1] += 1
                    if r[2] // 16 == 0 and rv > 0:
                        lazy += 1
                if not rv > e["best"]:
                    strict_bad += 1
                if rv == e["best"]:
                    tie_rows += 1
            elif not [k for k in pc.MODELLED if not c[k]]:
                pool_tot += 1
                pool["tie" if sc == rb else ("lt" if sc < rb else "unexpl")] += 1
    agreed = s3["AGREED"][0] + s3["DRIFT"][0]
    gate("G7_val_law_save", agreed == 1931 and strict_bad == 0 and tie_rows == 0
         and lazy == 1 and b1k_row == 0,
         "machine val == save nibble(+byte9bit4-zero) %d/2321 rows (%s); lazy "
         "rows %d; val<=best rows %d; val==best rows %d; 0x1000-zero tests row-"
         "side %d pool-side %d (M296: pool-side only)"
         % (agreed, {k: "%d/%d" % (d[0], d[0] + d[1]) for k, d in s3.items()},
            lazy, strict_bad, tie_rows, b1k_row, b1k_pool))
    expl = pool["tie"] + pool["lt"]
    gate("G8_pool_static_skips", pool_tot == PIN_POOL and expl == 6048
         and pool["unexpl"] == 2434 and pool["tie"] == PIN_TIE_POOL,
         "pool %d/%d: %d explained as val<=best-at-slot (ties %d), %d unexplained "
         "= live-mutation/no-go residue (DECLARED - the live-map census closer)"
         % (pool_tot, PIN_POOL, expl, pool["tie"], pool["unexpl"]))

    # ---- G9 rivals must FAIL the same grid -------------------------------------
    rival_ties = pool["tie"]
    frozen_div = 0
    init_div = 0
    for vi, v, pod, pcls, preg, cls, dec, init, law_init in graded:
        accs = sorted((s, e["val"]) for s, e in v["acc"].items())
        for s in range(25):
            if any(t <= s for t, _ in accs):
                frozen_div += 1
        first = v["deep"].get(dec[0]) or v["acc"][dec[0]]
        if first["best"] != 0:
            init_div = next((t for t, val in accs if val > first["best"]), 25)
    gate("G9_rivals_fail", rival_ties == PIN_TIE_POOL and frozen_div > 0
         and nbyp == PIN_BYPASS and init_div > 0,
         "rival >=-argmax would accept %d pool tie cells that printed NO row "
         "(0 tie rows among 2321; corroboration class, nogo-unverified per M296 "
         "S5b) | rival frozen-best (no accept store) diverges from the GROW best "
         "column on %d/%d slots | rival no-bypass prints %d extra GDEEP rows "
         "(the 61 GACC-only slots) | rival no-init-law diverges %d GROW slots in "
         "the u=45 visit" % (rival_ties, frozen_div, ntot, nbyp, init_div))

    ok = all(o for _, o, _ in R)
    return ok, R


def acceptance(sav_path, results, raw_path=DEF_RAW):
    """selftest entry (mirrors sim.precheck.acceptance)."""
    ok, R = report(sav_path, raw_path)
    for name, good, detail in R:
        results.append((name, good))
        print("%-24s %s  %s" % (name, "PASS" if good else "FAIL", detail))
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.scanleg")
    ap.add_argument("--sav", default=DEF_SAV)
    ap.add_argument("--raw", default=DEF_RAW)
    ap.add_argument("--out", help="write the report here")
    a = ap.parse_args(argv)
    ok, R = report(a.sav, a.raw)
    lines = ["sim.scanleg B17 report (sav=%s raw=%s)" % (
        os.path.basename(a.sav), os.path.basename(a.raw))]
    lines += ["%-24s %s  %s" % (n, "PASS" if o else "FAIL", d) for n, o, d in R]
    n_pass = sum(1 for _, o, _ in R if o)
    lines.append("RESULT: %s" % (("PASS B17 %d/%d gates (module run; the "
                                  "selftest adds the two-run determinism gate)"
                                  % (n_pass, len(R))) if ok else "FAIL"))
    txt = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt)
    sys.stdout.write(txt)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
