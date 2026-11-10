"""sim.hubfound - rung B13: the pod-driven founding-dispatch leg - M290's
founder-decision law executable, replacing the (x,y) placeholder that M290
REFUTED in sim/basefound (rung B10 kept it only for its curve acceptance).

M290 (merged #242; byte gates scripts/m290_hub_decision.py) settled the hub's
founding decision:
  * DISPATCH IS OWN-TILE-GATED: at 0x563d46 the hub tests the scan's chosen
    target offset (esi).  ZERO (the pod is on its own tile) -> call the
    founder vector FUN_004cca50 (census FOUND ret 0x4ccbe2); NONZERO -> the
    leg pushes msg 0x2408 ("Auto-sending BUILD BASE message") with NO founder
    call - a distant target can NEVER found.  There is NO channel from a
    scanned candidate tile to the founder.
  * The vector prologue loads the founder's args from the POD's own unit
    record (52*u fold): owner cl=[+14], y eax=s16[+10], x edi=s16[+8].  So
    the founding tile IS the pod's tile.  This leg models that LAW by taking
    the pod's fields from its record: the sim composes the pod with rung
    B12's production.create_record and reads it back with the save-view
    fields sim/save.py unit() uses (x u16 +0, y u16 +2, owner u8 +14) - the
    same save-view reads that reproduced the live positions in B5/B7/B12.
    (The live vector's +8/+10 loads are M290's byte facts, gated in
    scripts/m290_hub_decision.py; this module does not re-derive them.)
  * The founder's guard is CAPACITY ONLY (count < 0x200) - rung B10's Ledger
    leg (founder/destroyer with compaction).

Parity ground truth: the M289 golden record - evidence/m289_gdb_raw.log
(7 "FOUND ret=0x4ccbe2 fac=.. x=.. y=.. cnt=.." rows + 2 "DESTROY cnt=.."
rows; cnt is the ledger count BEFORE the op) and the per-turn n_bases curve
evidence/trace_m289_20261110_071759.jsonl (m54b_clean, 30 turns, 18 -> 23).

Site legality is judged in the 44-B RECORD view (the M290 trap: the save's
22-B column byte 0 is NOT the live category): rec = (W/2)*y + (x>>1),
off = grid_off + 44*rec, cat = (byte >> 5) % 8, land = 3..6.

The pod WALK (which pod, which target tile - the scan's score law at
0x563c00-0x563d40) is DECLARED, not modeled: this leg takes the pod and the
target press as INPUT.  The walk is the next ANALYSE frontier.

The DESTROY slot is ASSUMED last (the log rows carry only the pre-op cnt):
destroy(len-1) pops the tail, so no compaction move needs modeling - the
two destroyed foundings are simply ABSENT from the final ledger.

No /proc, no gdb, no Wine.  Deterministic: two runs give identical report
sha256.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile

from . import save as sosave
from . import basefound as sobf
from . import production as sop
from . import savewriter as sow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = os.path.join(ROOT, "evidence", "m289_gdb_raw.log")
DEFAULT_TRACE = os.path.join(ROOT, "evidence",
                             "trace_m289_20261110_071759.jsonl")

MSG_AUTO_BUILD = 0x2408      # the distant-target message (M290 G1/G4)
CAP = sobf.CAP               # 0x200 - the founder's ONLY guard (M290 G3)
UNIT_X, UNIT_Y, UNIT_OWNER = 0, 2, 14   # save-view fields (sim/save.py unit())
FAR_TARGET = (3, 3)          # the gate's distant press: no recorded site is here

FOUND_RE = re.compile(r"FOUND ret=(\S+) fac=(\d+) x=(\d+) y=(\d+) cnt=(\d+)")
DESTROY_RE = re.compile(r"DESTROY cnt=(\d+)")


def pod_record(owner, x, y, utype=0):
    """A 52-B pod unit record (composed with rung B12's create_record)."""
    return sop.create_record(x, y, utype, owner)


def pod_fields(rec):
    """The pod's fields read FROM THE RECORD (the M290 law: the founder's
    args come from the pod record, never from the scan's target)."""
    return {"x": struct.unpack_from("<H", rec, UNIT_X)[0],
            "y": struct.unpack_from("<H", rec, UNIT_Y)[0],
            "owner": rec[UNIT_OWNER]}


def dispatch(rec, target):
    """M290's own-tile-gated founding dispatch.
    target: None      -> the scan chose the pod's OWN tile (esi == 0);
            (tx, ty)  -> a distant target (esi != 0).
    Returns ("found", fac, x, y) (the founder call, args = the pod record)
    or ("msg", MSG_AUTO_BUILD) - with NO founding on that leg, ever."""
    f = pod_fields(rec)
    if target is None or (int(target[0]), int(target[1])) == (f["x"], f["y"]):
        return ("found", f["owner"], f["x"], f["y"])
    return ("msg", MSG_AUTO_BUILD)


def dispatch_ungated(rec, target):
    """RIVAL: an ungated leg - founds regardless of the target, AT the
    target tile.  Must fail the same fit the gated model passes."""
    f = pod_fields(rec)
    return ("found", f["owner"], int(target[0]), int(target[1]))


def events_from_log(path):
    """The recorded events in log order: ("found", ret, fac, x, y, cnt) and
    ("destroy", cnt); cnt is the ledger count BEFORE the op."""
    ev = []
    for line in open(path):
        m = FOUND_RE.match(line)
        if m:
            ev.append(("found", m.group(1), int(m.group(2)), int(m.group(3)),
                       int(m.group(4)), int(m.group(5))))
            continue
        d = DESTROY_RE.match(line)
        if d:
            ev.append(("destroy", int(d.group(1))))
    return ev


def cat_land(sv, x, y):
    """The live byte-0 terrain category via the 44-B RECORD view (M290 trap:
    tile()'s 22-B column view misreads it).  Land is cat 3..6."""
    rec = (sv.width // 2) * y + (x >> 1)
    off = sv.grid_off + sosave.REC_LEN * rec
    return (sv.data[off] >> 5) % 8


def replay(led, ev):
    """Apply the recorded events in log order through B10's leg, checking
    EVERY row's pre-cnt against the model (strict accounting, M289 style);
    the destroy slot is ASSUMED last.  Returns (strict_ok, peak, steps)."""
    steps = []
    ok = True
    peak = len(led)
    for e in ev:
        pre = len(led)
        cnt = e[-1]
        good = pre == cnt
        if e[0] == "found":
            landed = led.found(e[2], e[3], e[4])
        else:
            landed = led.destroy(len(led) - 1) is not None
        peak = max(peak, len(led))
        steps.append((e[0], pre, len(led), good and landed))
        ok = ok and good and landed
    return ok, peak, steps


def placeholder_fit(sv, ev):
    """What B10's ASSUMED placeholder rule (sobf._tile row-major
    first-unoccupied + sobf._ai_faction fewest-bases) would have chosen at
    each recorded founding, replayed against the real event sequence."""
    led = sobf.from_save(sv)
    pairs = []
    for e in ev:
        if e[0] != "found":
            led.destroy(len(led) - 1)
            continue
        _kind, _ret, fac, x, y, _cnt = e
        fx, fy = sobf._tile(led, sv.width, sv.height)
        ff = sobf._ai_faction(led, sv.own_player)
        pairs.append(((fac, x, y), (ff, fx, fy)))
        led.found(fac, x, y)
    return pairs


def run_fit(sav_path, log_path, trace_path):
    """The shared fit: parse, dispatch-press both legs, replay the ledger."""
    sv = sosave.parse(sav_path)
    ev = events_from_log(log_path)
    founds = [e for e in ev if e[0] == "found"]
    pods = [pod_record(f[2], f[3], f[4]) for f in founds]
    own = [dispatch(p, None) for p in pods]
    dist = [dispatch(p, FAR_TARGET) for p in pods]
    led = sobf.from_save(sv)
    strict_ok, peak, steps = replay(led, ev)
    report = {"foundings": [(f[2], f[3], f[4]) for f in founds],
              "pre_cnt_strict": strict_ok,
              "endpoint": len(led), "peak": peak,
              "own_tile_hits": sum(1 for g in own if g[0] == "found"),
              "distant_foundings": sum(1 for g in dist if g[0] == "found"),
              "distant_msgs": sum(1 for g in dist
                                  if g == ("msg", MSG_AUTO_BUILD)),
              "final_records": [(r["fac"], r["x"], r["y"])
                                for r in led.records]}
    return sv, led, report


def acceptance(sav_path, log_path, trace_path, results):
    """The 12 B13 gates; fills `results` with (name, ok) 2-tuples like the
    other rungs.  Returns the summary report dict."""
    sv = sosave.parse(sav_path)
    ev = events_from_log(log_path)
    founds = [e for e in ev if e[0] == "found"]
    destroys = [e for e in ev if e[0] == "destroy"]
    rec_tuples = [(e[2], e[3], e[4]) for e in founds]
    rec_tiles = {(t[1], t[2]) for t in rec_tuples}

    # G1 constants + pod record compose/read round-trip
    pr = pod_record(3, 29, 42)
    results.append(("G1 constants: msg 0x2408, CAP 0x200, strides 52/304; the pod "
                    "record composes via B12's create_record and reads back owner@14 "
                    "x@0 y@2",
                    MSG_AUTO_BUILD == 0x2408 and CAP == 0x200
                    and len(pr) == sosave.UNIT_LEN == 52 and sobf.BASE_LEN == 304
                    and pod_fields(pr) == {"x": 29, "y": 42, "owner": 3}))

    # G2 record: 7+2 rows, all ret 0x4ccbe2, destroy rows ordered
    lines = open(log_path).readlines()
    rows_f = [i for i, l in enumerate(lines) if l.startswith("FOUND")]
    rows_d = [i for i, l in enumerate(lines) if l.startswith("DESTROY")]
    rets = {e[1] for e in founds}
    order_ok = (len(rows_d) == 2 and rows_f[2] < rows_d[0] < rows_f[3]
                and rows_d[1] > rows_f[6])
    results.append(("G2 record: 7 foundings (ret %s) + 2 destroys; DESTROY rows "
                    "strictly between F3/F4 and after F7" % (sorted(rets),),
                    len(founds) == 7 and len(destroys) == 2
                    and rets == {"0x4ccbe2"} and order_ok))

    # G3 dispatch leg: pod-at-own-tile presses == the recorded tuples
    pods = [pod_record(fac, x, y) for (fac, x, y) in rec_tuples]
    own = [dispatch(p, None) for p in pods]
    hit = sum(1 for g, t in zip(own, rec_tuples) if g == ("found",) + t)
    results.append(("G3 dispatch: the 7 pod records pressed at their OWN tiles "
                    "return ('found',fac,x,y) == the recorded tuples (%d/7)" % hit,
                    hit == 7))

    # G4 own-tile gate: distant presses found NOTHING, send msg 0x2408
    dist = [dispatch(p, FAR_TARGET) for p in pods]
    results.append(("G4 own-tile gate: the 7 distant presses yield 0 foundings and "
                    "%d/7 msg 0x2408 sends" % sum(1 for m in dist
                                                  if m == ("msg", MSG_AUTO_BUILD)),
                    sum(1 for m in dist if m[0] == "found") == 0
                    and all(m == ("msg", MSG_AUTO_BUILD) for m in dist)))

    # G5 RIVAL ungated dispatch at the target fails the same fit
    rg = [dispatch_ungated(p, FAR_TARGET) for p in pods]
    in_rec = sum(1 for g in rg if (g[2], g[3]) in rec_tiles)
    results.append(("G5 RIVAL ungated dispatch founds AT THE TARGET on the distant "
                    "leg: 7 invented tuples, %d/7 occur in the record (the record "
                    "has ZERO distant-target foundings)" % in_rec,
                    all(g[0] == "found" for g in rg) and in_rec == 0))

    # G6 legality: every recorded site is land in the 44-B record view
    cats = [cat_land(sv, x, y) for (_f, x, y) in rec_tuples]
    results.append(("G6 legality: all 7 recorded sites are LAND (cat 3-6, 44-B "
                    "record view); cats %s" % cats,
                    all(3 <= c <= 6 for c in cats)))

    # G7 occupancy: no recorded site already carries a base
    base_tiles = {(b["x"], b["y"]) for b in sv.bases}
    hits = [t for t in rec_tiles if t in base_tiles]
    results.append(("G7 occupancy: 0 of the 7 sites are already m54b_clean base "
                    "tiles (save carries %d bases)" % len(base_tiles), hits == []))

    # G8 strict ledger replay through B10's leg
    led = sobf.from_save(sv)
    strict_ok, peak, steps = replay(led, ev)
    results.append(("G8 ledger strict: all 9 rows' pre-cnt agree with the model "
                    "replayed from the save's %d records; endpoint %d peak %d "
                    "(destroy slot ASSUMED last)" % (sv.n_bases, len(led), peak),
                    strict_ok and len(led) == 23 and peak == 24))

    # G9 the jsonl per-turn curve
    curve = []
    for line in open(trace_path):
        d = json.loads(line)
        if "state_before" in d:
            curve.append(d["state_after"]["n_bases"])
    lo, hi = sv.n_bases - len(destroys), sv.n_bases + len(founds)
    results.append(("G9 curve: jsonl ends %d == model %d, peaks %d, all %d "
                    "samples inside the global envelope [%d,%d]"
                    % (curve[-1], len(led), max(curve), len(curve), lo, hi),
                    curve[-1] == len(led) == 23 and max(curve) == 24
                    and all(lo <= n <= hi for n in curve)))

    # G10 RIVAL B10 placeholder rule reproduces none of the 7 tuples
    pairs = placeholder_fit(sv, ev)
    match = sum(1 for (rt, pt) in pairs if rt == pt)
    results.append(("G10 RIVAL B10 placeholder (row-major first-unoccupied + "
                    "fewest-bases faction) reproduces %d/7 recorded tuples - the "
                    "M290 refutation restated as a gate" % match, match == 0))

    # G11 written image: the grown ledger round-trips through savewriter
    grown = len(led) - sv.n_bases
    img = sow.build_image(sv, bases_override=led.records,
                          orig_n_bases=sv.n_bases)
    bo = sv.bases_off
    pre_diffs = [i for i in range(bo) if img[i] != sv.data[i]]
    newrecs_ok = all(
        img[bo + 304 * (sv.n_bases + k):bo + 304 * (sv.n_bases + k + 1)]
        == sobf.record_bytes(led.records[sv.n_bases + k])
        for k in range(grown))
    survivors = [(r["fac"], r["x"], r["y"]) for r in led.records[sv.n_bases:]]
    dead = [t for t in rec_tuples if t not in survivors]
    rp = sosave.Save("written", img)
    results.append(("G11 written image: grown ledger +%d -> %d records (survivors "
                    "%s; destroyed %s ABSENT); prefix diff %s; originals and tail "
                    "byte-identical; re-parses n_bases %d"
                    % (grown, len(led), survivors, dead, pre_diffs, rp.n_bases),
                    len(img) == len(sv.data) + 304 * grown
                    and pre_diffs == [72]
                    and img[bo:bo + 304 * sv.n_bases]
                    == sv.data[bo:bo + 304 * sv.n_bases]
                    and newrecs_ok
                    and img[bo + 304 * len(led):]
                    == sv.data[bo + 304 * sv.n_bases:]
                    and rp.n_bases == len(led) == 23 and len(dead) == 2))

    # G12 determinism + CLI
    outs = []
    shas = []
    rc_all = 0
    for _ in range(2):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            p = fh.name
        outs.append(p)
        r = subprocess.run([sys.executable, "-m", "sim.hubfound",
                            "--sav", sav_path, "--log", log_path,
                            "--trace", trace_path, "--out", p],
                           capture_output=True, text=True, cwd=ROOT)
        rc_all += r.returncode
        if r.returncode == 0:
            with open(p, "rb") as fh:
                shas.append(hashlib.sha256(fh.read()).hexdigest())
    for p in outs:
        os.unlink(p)
    results.append(("G12 determinism + CLI: python3 -m sim.hubfound exits 0 twice, "
                    "report sha256 %s" % (shas[0][:16] if len(shas) == 2
                                          and shas[0] == shas[1] else "n/a"),
                    rc_all == 0 and len(shas) == 2 and shas[0] == shas[1]))

    _, _, rep = run_fit(sav_path, log_path, trace_path)
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.hubfound")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    _sv, _led, report = run_fit(a.sav, a.log, a.trace)
    blob = json.dumps(report, sort_keys=True)
    with open(a.out, "w") as fh:
        fh.write(blob + "\n")
    print("foundings %d | pre-cnt strict %s | end %d peak %d | own-tile hits "
          "%d/7 | distant found %d msg %d | sha256 %s"
          % (len(report["foundings"]), report["pre_cnt_strict"],
             report["endpoint"], report["peak"], report["own_tile_hits"],
             report["distant_foundings"], report["distant_msgs"],
             hashlib.sha256(blob.encode()).hexdigest()[:16]))
    return 0 if report["pre_cnt_strict"] else 1


if __name__ == "__main__":
    sys.exit(main())
