"""sim.composedrun - rung B21: the recorded m289 run executed as ONE state object,
written back as a .SAV and RESUMED from that write.

WHAT IS NEW (every leg used here exists as its own rung; B21 composes them and
grades the composition):
  * the B3 turn engine (sim/turn.py) pressed the recorded m289 turn count;
  * the B10 ledger driven by the B13 recorded op stream (evidence/m289_gdb_raw.log:
    7 FOUND + 2 DESTROY, cnt = ledger count BEFORE the op);
  * the B8 savewriter composing BOTH modeled header fields at once - year@84 AND
    the bases-count dword - plus the grown 304-B base array;
  * a NEW leg: re-load the image we wrote with sim.save and CONTINUE the run from
    it, requiring (write, then press) == (press 31 times, then write) BYTE-FOR-BYTE.

THE MEASUREMENT (computed every run, not prose): the per-turn n_bases curve and
the op-level log are two recordings of the SAME run, and the curve is strictly
coarser.  A curve-matching schedule needs only sum|delta| = 7 ops; the log carries
9, so exactly one turn hides a (+1,-1) pair.  The curve-only schedule reproduces
the curve 30/30 yet matches only 7 of the 9 recorded op (kind, pre-count) pairs,
while the log-driven schedule matches 30/30 AND 9/9 - the rival fails the same fit.

No /proc, no gdb, no Wine, no game binary.  Deterministic: two runs give identical
report text and an identical written image sha256.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import tempfile
from collections import Counter

from . import basefound as sobf
from . import hubfound as soh
from . import save as sosave
from . import savewriter as sow
from . import turn as soturn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SAV = os.path.join(ROOT, "programs", "saves", "m54b_clean.SAV")
DEFAULT_LOG = os.path.join(ROOT, "evidence", "m289_gdb_raw.log")
DEFAULT_TRACE = os.path.join(ROOT, "evidence", "trace_m289_20261110_071759.jsonl")

G_YEAR_FILE = sosave.mem2file(sosave.G_YEAR)
G_BASES_FILE = sosave.mem2file(sosave.G_BASES)


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


# ------------------------------------------------------------- recordings --
def load_curve(trace_path):
    """The recorded per-turn curve: the start snapshot + 30 turn rows."""
    start, rows = None, []
    for line in open(trace_path):
        r = json.loads(line)
        if r.get("type") == "start":
            start = r["state"]
            continue
        b, a = r["state_before"], r["state_after"]
        rows.append({"turn": r["turn"], "yb": b["year"], "ya": a["year"],
                     "cur_b": b["cur_player"], "cur_a": a["cur_player"],
                     "tf_b": b["turn_flags"], "tf_a": a["turn_flags"],
                     "nb_b": b["n_bases"], "nb_a": a["n_bases"]})
    rows.sort(key=lambda d: d["turn"])
    return start, rows


def op_stream(log_path, sv_count):
    """The recorded op stream in log order (hubfound's own regex parser).
    Returns (ops, pref) with pref[k] = ledger length after the first k ops."""
    ops, pref, cnt = [], [sv_count], sv_count
    for e in soh.events_from_log(log_path):
        if e[0] == "found":
            _kind, _ret, fac, x, y, pre = e
            ops.append({"kind": "found", "fac": fac, "x": x, "y": y, "pre": pre})
            cnt += 1
        else:
            ops.append({"kind": "destroy", "fac": None, "x": None, "y": None,
                        "pre": e[1]})
            cnt -= 1
        pref.append(cnt)
    return ops, pref


# -------------------------------------------------------------- scheduling --
def feasible_schedules(pref, after_targets):
    """Assignments of the op stream to turn intervals that reproduce the recorded
    curve: a nondecreasing per-turn prefix index k(t) with pref[k(t)] ==
    after_targets[t] and k(last) == len(ops).  Returns (count, earliest)."""
    T, K = len(after_targets), len(pref)
    C = [[0] * K for _ in range(T + 1)]
    F = [[False] * K for _ in range(T + 1)]
    C[T][K - 1] = 1
    F[T][K - 1] = True
    for t in range(T - 1, -1, -1):
        tgt = after_targets[t]
        for k in range(K):
            acc, any_ = 0, False
            for kk in range(k, K):
                if pref[kk] == tgt and F[t + 1][kk]:
                    acc += C[t + 1][kk]
                    any_ = True
            C[t][k], F[t][k] = acc, any_
    if not F[0][0]:
        return 0, None
    earliest, k = [], 0
    for t in range(T):
        k = next(kk for kk in range(k, K)
                 if pref[kk] == after_targets[t] and F[t + 1][kk])
        earliest.append(k)
    return C[0][0], earliest


# ------------------------------------------------------------------- model --
def press_run(sv, ops, schedule, fifo_destroy=False):
    """Press the B3 engine once per recorded turn; in the interval before turn t
    apply ops[k(t-1)..k(t)] through the B10 ledger.  destroy = LAST slot (B13's
    declared assumption); fifo_destroy is the RIVAL that drops the FIRST founded
    record instead.  Returns the run state."""
    led = sobf.from_save(sv)
    eng = soturn.Engine(sv.year, human=sv.own_player, cur=soturn.HUMAN, tf=0)
    initial = eng.state()
    k, model_after, ops_per_turn, intervals, emission = 0, [], [], [], []
    peak = len(led)
    for upto in schedule:
        batch = []
        for op in ops[k:upto]:
            pre = len(led)
            if op["kind"] == "found":
                landed = led.found(op["fac"], op["x"], op["y"])
                batch.append(("found", op["fac"], op["x"], op["y"], pre, len(led),
                              landed))
            else:
                if fifo_destroy:
                    idx = next((i for i in range(sv.n_bases, len(led))), None)
                    landed = led.destroy(idx) is not None if idx is not None else False
                else:
                    landed = led.destroy(len(led) - 1) is not None
                batch.append(("destroy", None, None, None, pre, len(led), landed))
            peak = max(peak, len(led))
        ops_per_turn.append(upto - k)
        intervals.append(batch)
        k = upto
        emission.extend(eng.press())
        model_after.append(len(led))
    return {"led": led, "eng": eng, "model_after": model_after,
            "ops_per_turn": ops_per_turn, "intervals": intervals, "peak": peak,
            "emission": [initial] + emission}


def curve_matches(run, rows):
    return sum(1 for i, r in enumerate(rows) if run["model_after"][i] == r["nb_a"])


def applied_ops(run):
    """The ops the run actually applied, as (kind, pre-count) rows."""
    return [(t[0], t[4]) for batch in run["intervals"] for t in batch]


def image_of(sv, led, eng):
    return sow.build_image(sv, year=eng.year, cur=eng.cur, tf=eng.tf,
                           bases_override=led.records)


def surviving_stack(ops, fifo=False):
    """Which recorded foundings survive the destroys, walking the op stream:
    destroy-last (LIFO, the model) or destroy-first-founded (FIFO, the rival)."""
    stack = []
    for o in ops:
        if o["kind"] == "found":
            stack.append((o["fac"], o["x"], o["y"]))
        elif stack:
            stack.pop(0 if fifo else -1)
    return stack


# ---------------------------------------------------------------- pipeline --
def pipeline(sav_path, log_path, trace_path, do_print=True):
    out = []
    W = out.append
    sv = sosave.parse(sav_path)
    start, rows = load_curve(trace_path)
    ops, pref = op_stream(log_path, sv.n_bases)
    T = len(rows)
    n_ops = len(ops)
    n_found = sum(1 for o in ops if o["kind"] == "found")
    after_t = [r["nb_a"] for r in rows]
    min_ops = sum(abs(r["nb_a"] - r["nb_b"]) for r in rows)
    K, earliest = feasible_schedules(pref, after_t)
    if earliest is None:
        raise SystemExit("B21: NO schedule of the recorded op log reproduces the "
                         "recorded curve - the two recordings contradict each "
                         "other (pref=%s after=%s)" % (pref, after_t))
    run = press_run(sv, ops, earliest)
    led, eng = run["led"], run["eng"]
    last = rows[-1]

    W("B21 composedrun  save=%s  trace=%s  log=%s"
      % (os.path.basename(sav_path), os.path.basename(trace_path),
         os.path.basename(log_path)))
    W("recorded: %d turn rows; %d ops (%d found + %d destroy)"
      % (T, n_ops, n_found, n_ops - n_found))
    W("save: year %d n_bases %d n_units %d own_player %d size %d B map %dx%d"
      % (sv.year, sv.n_bases, sv.n_units, sv.own_player, sv.size,
         sv.width, sv.height))
    W("trace start: year %d n_bases %d cur %d tf %d"
      % (start["year"], start["n_bases"], start["cur_player"],
         start["turn_flags"]))
    W("")
    W("== op chain (log order; the log's cnt is the ledger count BEFORE the op) ==")
    W("  i kind     fac   x   y   rec_pre  model_pre  model_post  ok")
    chain_hits = 0
    for i, op in enumerate(ops):
        delta = 1 if op["kind"] == "found" else -1
        good = (pref[i] == op["pre"] and pref[i] + delta == pref[i + 1])
        chain_hits += good
        W("%3d %-7s %4s %3s %3s  %7d %10d %11d   %s"
          % (i, op["kind"], op["fac"], op["x"], op["y"], op["pre"], pref[i],
             pref[i + 1], "ok" if good else "BAD"))
    W("closed walk (every rec_pre == model_pre AND every op lands): %d/%d"
      % (chain_hits, n_ops))
    W("")
    W("== the run: ops in the interval, then the B3 press (log schedule, "
      "lexicographically earliest feasible placement) ==")
    W("  t  nb_rec_b nb_rec_a  nb_model  ops_in_interval  match   year_rec_b  year_model")
    curve_match = 0
    year_match = 0
    for i, r in enumerate(rows):
        ym = sv.year + i
        m = run["model_after"][i] == r["nb_a"]
        curve_match += m
        year_match += (ym == r["yb"] == r["ya"] - 1)
        W("%3d %9d %9d %10d %17d %7s %11d %11d"
          % (r["turn"], r["nb_b"], r["nb_a"], run["model_after"][i],
             run["ops_per_turn"][i], "ok" if m else "BAD", r["yb"], ym))
    W("curve match %d/%d | year_before == save_year+turn AND year_after == +1: "
      "%d/%d" % (curve_match, T, year_match, T))
    W("intervals carrying >1 op: %d (max %d) | feasible placement count K = %d"
      % (sum(1 for c in run["ops_per_turn"] if c > 1),
         max(run["ops_per_turn"]), K))
    W("curve-minimal op count sum|delta| = %d  <  recorded ops %d  (the curve "
      "hides %d op(s), a net-zero (+1,-1) pair)"
      % (min_ops, n_ops, n_ops - min_ops))
    # the engine's emission must SUPPLY every recorded (cur, tf, year) row, in order.
    # The recorder samples BOTH sides of a turn boundary, so adjacent identical
    # samples collapse (the m30 "model rows may be extra" law, applied to a
    # two-sampling-point-per-turn recorder).
    # Each retained sample carries the turns it belongs to (a collapsed boundary
    # sample belongs to TWO), so a miss names the turn it came from, not an index.
    rec_rows, rec_owner = [], []
    for r in rows:
        for kind, st in (("before", (r["cur_b"], r["tf_b"], r["yb"])),
                         ("after", (r["cur_a"], r["tf_a"], r["ya"]))):
            if rec_rows and rec_rows[-1] == st:
                rec_owner[-1] += "+t%d.%s" % (r["turn"], kind)
                continue
            rec_rows.append(st)
            rec_owner.append("t%d.%s" % (r["turn"], kind))
    matched, missing, _consumed = soturn.match(run["emission"], rec_rows)
    # the trace's own internal chain: before(t) == after(t-1)
    chain_year = sum(1 for i in range(1, T)
                     if rows[i]["yb"] == rows[i - 1]["ya"])
    chain_nb = sum(1 for i in range(1, T)
                   if rows[i]["nb_b"] == rows[i - 1]["nb_a"])
    chain_cur = sum(1 for i in range(1, T)
                    if (rows[i]["cur_b"], rows[i]["tf_b"])
                    == (rows[i - 1]["cur_a"], rows[i - 1]["tf_a"]))
    W("engine emission %d states; recorded (cur,tf,year) samples %d after "
      "collapsing adjacent duplicates; matched IN ORDER %d/%d (samples that "
      "missed: %s)" % (len(run["emission"]), len(rec_rows), matched, len(rec_rows),
                       [rec_owner[i] for i in missing]))
    W("trace self-chain on 29 turn boundaries: year %d/29, n_bases %d/29, "
      "(cur,tf) %d/29 - the recorder's after-sample of turn t IS its before-sample "
      "of turn t+1, so %d samples are distinct (a few are taken mid-cycle)"
      % (chain_year, chain_nb, chain_cur, len(rec_rows)))
    W("")
    W("== the ledger after the run ==")
    W("endpoint %d (recorded after(%d) %d) | peak %d | save-carried %d | cap %d"
      % (len(led), last["turn"], last["nb_a"], run["peak"], sv.n_bases, sobf.CAP))
    new_recs = [(r["fac"], r["x"], r["y"]) for r in led.records[sv.n_bases:]]
    W("grown slots %d (fac,x,y): %s" % (len(new_recs), new_recs))
    gone_f = _destroyed_foundings(ops, sv)
    W("recorded foundings %d; surviving under destroy-last %d; the %d sites the "
      "destroys removed %s - still a base tile in the model? %s"
      % (n_found, len(new_recs), len(gone_f),
         [(g["fac"], g["x"], g["y"]) for g in gone_f],
         [any(r["x"] == g["x"] and r["y"] == g["y"] for r in led.records)
          for g in gone_f]))
    W("")
    W("== the written image, the reload and the RESUME ==")
    img = image_of(sv, led, eng)
    with tempfile.TemporaryDirectory(prefix="b21_") as tmpd:
        p_img = os.path.join(tmpd, "b21_written.SAV")
        with open(p_img, "wb") as fh:
            fh.write(img)
        sv2 = sosave.parse(p_img)   # the bytes stay in memory after the tmpdir goes
    led2 = sobf.from_save(sv2)
    # THE RESUMED ENGINE IS BUILT ONLY FROM FIELDS READ BACK OUT OF THE IMAGE -
    # cur_player, the modeled turn_flags bit and the year - never from the model.
    saved_cur = _u32(img, sow.OFF_CUR)
    saved_tf = _u32(img, sow.OFF_TF) & sow.TF_MODEL_BIT
    fields_back = (saved_cur == eng.cur and saved_tf == (eng.tf & sow.TF_MODEL_BIT)
                   and sv2.year == eng.year)
    try:
        eng2 = soturn.Engine(sv2.year, human=sv2.own_player, cur=saved_cur,
                             tf=saved_tf)
        eng2.press()
        img2 = image_of(sv2, led2, eng2)
        resume_err = None
    except ValueError as exc:      # a saved state that is not a human phase
        eng2, img2, resume_err = None, None, exc.args[0].split(".")[0]
    run3 = press_run(sv, ops, earliest)
    run3["eng"].press()
    img3 = image_of(sv, run3["led"], run3["eng"])
    grew = len(img) - sv.size
    W("orig %d B -> written %d B (grew %d B == %d records x %d B: %s)"
      % (sv.size, len(img), grew, len(led) - sv.n_bases, sosave.BASE_LEN,
         grew == (len(led) - sv.n_bases) * sosave.BASE_LEN))
    W("written year@%d = %d (recorded after(%d).year %d) | bases dword@%d = %d "
      "(recorded %d) | n_units %d (unchanged: %s)"
      % (G_YEAR_FILE, _u16(img, G_YEAR_FILE), last["turn"], last["ya"],
         G_BASES_FILE, _u32(img, G_BASES_FILE), last["nb_a"], sv2.n_units,
         sv2.n_units == sv.n_units))
    head_diffs = sorted(o for o in sow.diff_offsets(sv.data, img)
                        if o < sv.bases_off)
    spans = sow.modeled_spans()
    in_modeled = [o for o in head_diffs if any(lo <= o < hi for lo, hi in spans)]
    W("header diffs below bases_off(%d): %d byte(s) at %s; inside modeled spans "
      "%d/%d" % (sv.bases_off, len(head_diffs), head_diffs,
                 len(in_modeled), len(head_diffs)))
    tail_new = sv.bases_off + sosave.BASE_LEN * len(led)
    tail_old = sv.bases_off + sosave.BASE_LEN * sv.n_bases
    W("tail after the grown array == tail after the original array: %s (%d B)"
      % (img[tail_new:] == sv.data[tail_old:], len(sv.data) - tail_old))
    reload_eq = ([dict(r) for r in led2.records] == [dict(r) for r in led.records])
    W("RELOAD from the written image: year %d n_bases %d records %d; records == "
      "model records: %s; the SAVED cur %d / tf-bit %d / year %d equal the model's "
      "cur %d / tf-bit %d / year %d: %s"
      % (sv2.year, sv2.n_bases, len(led2), reload_eq, saved_cur, saved_tf, sv2.year,
         eng.cur, eng.tf & sow.TF_MODEL_BIT, eng.year, fields_back))
    if img2 is None:
        W("RESUME REFUSED from the saved state: %s" % resume_err)
        resume_diff, commute = [], False
    else:
        assert eng2 is not None      # the resume only reaches here if the press ran
        resume_diff = sorted(sow.diff_offsets(img, img2))
        commute = img2 == img3
        W("RESUME (the engine is built ONLY from the saved cur/tf/year): reload + 1 "
          "press -> year %d; img2 == img3 (31 presses on the original, then write): "
          "%s" % (eng2.year, commute))
        W("img -> img2 differing bytes: %d at %s (the year word is %d,%d)"
          % (len(resume_diff), resume_diff, G_YEAR_FILE, G_YEAR_FILE + 1))
    W("")
    W("== rivals, graded on the SAME recorded numbers ==")
    noleg = press_run(sv, [], [0] * T)
    W("R1 no founder leg at all: curve %d/%d, endpoint %d (recorded %d)"
      % (curve_matches(noleg, rows), T, len(noleg["led"]), last["nb_a"]))
    batch = press_run(sv, ops, [0] * (T - 1) + [n_ops])
    W("R2 all %d ops in the last interval: curve %d/%d"
      % (n_ops, curve_matches(batch, rows), T))
    curve_ops = []
    for r in rows:
        d = r["nb_a"] - r["nb_b"]
        # the curve carries NO faction/tile input: the rival's foundings are
        # zero-composed (B10's placeholder shape); the metric is (kind, pre-cnt)
        curve_ops += [{"kind": "found" if d > 0 else "destroy", "fac": 0,
                       "x": 0, "y": 0, "pre": None}] * abs(d)
    cpref = [sv.n_bases]
    for o in curve_ops:
        cpref.append(cpref[-1] + (1 if o["kind"] == "found" else -1))
    Kc, earliest_c = feasible_schedules(cpref, after_t)
    # the curve-derived schedule is guaranteed feasible by construction; the
    # guard is here so a broken derivation cannot silently be graded as a rival
    assert earliest_c is not None, "curve-only schedule is not curve-feasible"
    crun = press_run(sv, curve_ops, earliest_c)
    want = Counter((o["kind"], o["pre"]) for o in ops)
    hits_model = sum((Counter(applied_ops(run)) & want).values())
    hits_rival = sum((Counter(applied_ops(crun)) & want).values())
    W("R3 curve-only schedule (%d ops, K=%d): curve %d/%d but recorded op "
      "(kind,pre-cnt) fidelity %d/%d  [model schedule: %d/%d]"
      % (len(curve_ops), Kc, curve_matches(crun, rows), T, hits_rival, n_ops,
         hits_model, n_ops))
    fifo_run = press_run(sv, ops, earliest, fifo_destroy=True)
    fifo_surv = [(r["fac"], r["x"], r["y"]) for r in fifo_run["led"].records[sv.n_bases:]]
    W("R4 destroy drops the FIRST founded record (FIFO) instead of compacting the "
      "LAST: grown slots %s == model's? %s (endpoint still %d)"
      % (fifo_surv, fifo_surv == new_recs, len(fifo_run["led"])))
    W("R5 lift_all writer (count dwords pass-through): re-parses bases %d "
      "(recorded %d) year %d"
      % (_u32(sow.build_image(sv, year=eng.year, cur=eng.cur, tf=eng.tf,
                              bases_override=led.records, lift_all=True),
              G_BASES_FILE), last["nb_a"],
         _u16(sow.build_image(sv, year=eng.year, cur=eng.cur, tf=eng.tf,
                              bases_override=led.records, lift_all=True),
              G_YEAR_FILE)))
    img6 = sow.build_image(sv, year=sv.year, cur=eng.cur, tf=eng.tf,
                           bases_override=led.records)
    W("R6 year pass-through: writes year %d (a resumed run needs %d), so the "
      "reload leg breaks: %s"
      % (_u16(img6, G_YEAR_FILE), eng.year + 1,
         _u16(img6, G_YEAR_FILE) != sv2.year))
    # R7: a writer that leaves cur_player in an AI slot.  The resumed engine is
    # built from the SAVED fields, so this must be REFUSED - the proof that the
    # resume leg can actually see a broken turn-field write.
    r7_cur = (eng.cur + 1) % soturn.SLOTS
    img7 = sow.build_image(sv, year=eng.year, cur=r7_cur, tf=eng.tf,
                           bases_override=led.records)
    try:
        soturn.Engine(_u16(img7, G_YEAR_FILE), human=sv.own_player,
                      cur=_u32(img7, sow.OFF_CUR),
                      tf=_u32(img7, sow.OFF_TF) & sow.TF_MODEL_BIT).press()
        r7 = "press ACCEPTED - the resume leg has no teeth"
        r7_refused = False
    except ValueError as exc:
        r7 = "press REFUSED: %s" % exc.args[0].split(".")[0]
        r7_refused = True
    W("R7 writer leaves cur_player=%d (an AI slot) in the image: a resume from the "
      "saved fields -> %s" % (r7_cur, r7))
    W("")
    table = "\n".join(out) + "\n"
    digest = hashlib.sha256(table.encode()).hexdigest()
    table += ("table sha256 %s | written-image sha256 %s\n"
              % (digest[:16], hashlib.sha256(img).hexdigest()[:16]))
    if do_print:
        print(table, end="")
    return {"sv": sv, "rows": rows, "ops": ops, "pref": pref, "K": K, "run": run,
            "led": led, "eng": eng, "img": img, "img2": img2, "img3": img3,
            "sv2": sv2, "led2": led2, "chain_hits": chain_hits, "n_ops": n_ops,
            "curve_match": curve_match, "year_match": year_match, "T": T,
            "matched": matched, "rec_rows": len(rec_rows), "n_rec_rows": len(rec_rows),
            "chain_year": chain_year, "chain_nb": chain_nb, "chain_cur": chain_cur,
            "min_ops": min_ops, "hits_model": hits_model, "hits_rival": hits_rival,
            "noleg": curve_matches(noleg, rows), "batch": curve_matches(batch, rows),
            "crun": curve_matches(crun, rows),
            "fifo_same": fifo_surv == new_recs,
            "fifo_surv": fifo_surv, "new_recs": new_recs,
            "surviving": surviving_stack(ops), "surviving_fifo": surviving_stack(ops, True),
            "destroyed_tiles_gone": destroyed_check(led, ops, sv),
            "head_diffs": head_diffs, "all_modeled": len(in_modeled) == len(head_diffs)
            and bool(head_diffs),
            "growth_ok": grew == (len(led) - sv.n_bases) * sosave.BASE_LEN,
            "tail_ok": img[tail_new:] == sv.data[tail_old:],
            "reload_eq": reload_eq, "commute": commute, "fields_back": fields_back,
            "r7_refused": r7_refused, "saved_cur": saved_cur,
            "saved_tf": saved_tf, "resume_err": resume_err,
            "resume_diff": resume_diff, "year_written": _u16(img, G_YEAR_FILE),
            "bases_written": _u32(img, G_BASES_FILE), "last": last,
            "peak": run["peak"], "table": table, "digest": digest,
            "img_sha": hashlib.sha256(img).hexdigest(),
            "max_interval": max(run["ops_per_turn"]),
            "intervals_multi": sum(1 for c in run["ops_per_turn"] if c > 1)}


def _destroyed_foundings(ops, sv):
    """The foundings a destroy removed (LIFO order over the recorded stream)."""
    stack = []
    gone = []
    for o in ops:
        if o["kind"] == "found":
            stack.append(o)
        elif stack:
            gone.append(stack.pop())
    return gone


def destroyed_check(led, ops, sv):
    return [any(r["x"] == g["x"] and r["y"] == g["y"] for r in led.records)
            for g in _destroyed_foundings(ops, sv)]


# ------------------------------------------------------------------ gates --
def acceptance(sav_path, log_path, trace_path, results, tables=None):
    """Table FIRST (printed), then the gates.  `tables` optionally captures the
    table text for a caller that wants to persist it."""
    f = pipeline(sav_path, log_path, trace_path, do_print=True)
    if tables is not None:
        tables.append(f["table"])
    a = results.append
    sv, led, last = f["sv"], f["led"], f["last"]
    a(("G1 anchors recomputed, not asserted: save year %d == trace year_before(0); "
       "save n_bases %d == trace n_bases(0); op chain closed walk %d/%d"
       % (sv.year, sv.n_bases, f["chain_hits"], f["n_ops"]),
       sv.year == f["rows"][0]["yb"] and
       sv.n_bases == load_curve(trace_path)[0]["n_bases"] and
       f["chain_hits"] == f["n_ops"]))
    a(("G2 turn law on the recorded rows: year_before == save_year+turn AND "
       "year_after == +1 on %d/%d; the trace self-chains on %d/%d boundaries for "
       "year and %d/%d for n_bases; the emission supplies %d/%d recorded "
       "(cur,tf,year) samples IN ORDER"
       % (f["year_match"], f["T"], f["chain_year"], f["T"] - 1,
          f["chain_nb"], f["T"] - 1, f["matched"], f["n_rec_rows"]),
       f["year_match"] == f["T"] and f["matched"] == f["n_rec_rows"]
       and f["chain_year"] == f["T"] - 1 and f["chain_nb"] == f["T"] - 1))
    a(("G3 the log-driven schedule reproduces the recorded n_bases curve %d/%d; "
       "ledger endpoint %d == recorded %d; peak %d"
       % (f["curve_match"], f["T"], len(led), last["nb_a"], f["peak"]),
       f["curve_match"] == f["T"] and len(led) == last["nb_a"] == 23
       and f["peak"] == 24))
    a(("G4 the curve is STRICTLY COARSER than the op log: sum|delta| = %d ops "
       "suffices to match it but the log carries %d; feasible placements K=%d > 1"
       % (f["min_ops"], f["n_ops"], f["K"]),
       f["min_ops"] < f["n_ops"] and f["K"] > 1 and f["min_ops"] == 7
       and f["n_ops"] == 9))
    a(("G5 op fidelity: the log schedule hits %d/%d recorded (kind,pre-cnt) rows; "
       "the curve-only schedule %d/%d" % (f["hits_model"], f["n_ops"],
                                          f["hits_rival"], f["n_ops"]),
       f["hits_model"] == f["n_ops"] and f["hits_rival"] == 7))
    a(("G6 grown slots == the surviving recorded foundings %s; the 2 destroyed "
       "sites are NOT bases any more (present-flags %s)"
       % (f["new_recs"], f["destroyed_tiles_gone"]),
       f["new_recs"] == f["surviving"] and not any(f["destroyed_tiles_gone"])))
    a(("G7 the image grew by exactly %d B == %d x %d and the tail after the grown "
       "array is byte-identical" % (len(f["img"]) - sv.size, len(led) - sv.n_bases,
                                    sosave.BASE_LEN),
       f["growth_ok"] and f["tail_ok"]))
    a(("G8 header diffs %d byte(s) all inside modeled spans; year dword %d == "
       "recorded after(%d).year; bases dword %d == recorded %d"
       % (len(f["head_diffs"]), f["year_written"], last["turn"],
          f["bases_written"], last["nb_a"]),
       f["all_modeled"] and f["year_written"] == last["ya"]
       and f["bases_written"] == last["nb_a"]))
    a(("G9 RELOAD: the image re-parses (year %d n_bases %d), its %d records equal "
       "the model's %d, and the SAVED cur %d / tf-bit %d / year %d equal the "
       "model's (the resume input is read back, not assumed)"
       % (f["sv2"].year, f["sv2"].n_bases, len(f["led2"]), len(led),
          f["saved_cur"], f["saved_tf"], f["sv2"].year),
       f["reload_eq"] and f["sv2"].n_bases == len(led) == last["nb_a"]
       and f["fields_back"]))
    a(("G10 RESUME COMMUTES (engine built from the SAVED cur/tf/year): "
       "write-then-press == press-31-then-write byte-for-byte (%s); the img->img2 "
       "diff is %d byte(s) at %s (the year word only)"
       % (f["commute"], len(f["resume_diff"]), f["resume_diff"][:6]),
       f["commute"] and f["resume_diff"]
       and all(o in (G_YEAR_FILE, G_YEAR_FILE + 1) for o in f["resume_diff"])))
    a(("G11 rivals fail the same fit: no-leg curve %d/%d, all-ops-at-end %d/%d, "
       "curve-only %d/%d curve but %d/%d ops, FIFO-destroy reproduces the grown "
       "slots: %s, corrupted saved cur_player refused by the resume: %s"
       % (f["noleg"], f["T"], f["batch"], f["T"], f["crun"], f["T"],
          f["hits_rival"], f["n_ops"], f["fifo_same"], f["r7_refused"]),
       f["noleg"] < f["T"] and f["batch"] < f["T"] and f["crun"] == f["T"]
       and f["hits_rival"] < f["n_ops"] and not f["fifo_same"]
       and f["r7_refused"]))
    g = pipeline(sav_path, log_path, trace_path, do_print=False)
    a(("G12 two runs: report text sha256 identical and written-image sha256 "
       "identical (%s)" % f["digest"][:16],
       g["digest"] == f["digest"] and g["img_sha"] == f["img_sha"]))
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.composedrun")
    ap.add_argument("--sav", default=DEFAULT_SAV)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    results, tables = [], []
    acceptance(a.sav, a.log, a.trace, results, tables=tables)
    with open(a.out, "w") as fh:
        fh.write(tables[0])
        for name, ok in results:
            fh.write(("  ok   " if ok else "  BAD  ") + name + "\n")
    for name, ok in results:
        print(("  ok   " if ok else "  BAD  ") + name)
    bad = [n for n, ok in results if not ok]
    if bad:
        print("FAIL B21: %d/%d gates failed: %s" % (len(bad), len(results),
                                                    "; ".join(bad)))
        return 1
    print("PASS B21: %d/%d gates - the recorded m289 run executes as ONE state "
          "object (30 B3 presses + the 9-op founder/destroyer ledger), writes "
          "year AND the bases count into a .SAV that reloads and RESUMES "
          "byte-identically, and the curve/log pairing (7 vs 9 ops) is measured "
          "on both schedules (no box time, no /proc, no gdb)"
          % (len(results), len(results)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
