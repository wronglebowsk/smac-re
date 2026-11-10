"""sim.parity - rung B9: the R3 golden-trace pairing (BUILD_SPINE.md).

The golden trace evidence/trace_m54b40b_20261024_212833.jsonl is the ORIGINAL
terran.exe running the SAME save the sim loads (m54b_clean.SAV, 2150, our player 3):
40 TURN-COMPLETE presses, one row per turn with state_before/state_after snapshots of
(year, cur_player, turn_flags, n_bases). B9 presses the B3 engine the trace's OWN turn
count and pairs every recorded snapshot against the emitted state sequence as an
ordered subsequence - zero tolerance on the recorded side (the m30 law: recorded rows
may not be skipped, model rows may be extra).

What the pairing does NOT claim: n_bases (the sim has no AI base-founder - the model
keeps the save's constant while the recorded game grows it; that delta is the rung's
frontier finding, measured and declared, never a gate input), and the press transition
itself ((3,0)->(3,2) is never separately sampled - the B3 NOTE acknowledges this).

NO /proc, NO gdb, NO Wine, NO game binary. Two runs -> identical report sha256.
"""
import argparse
import hashlib
import json
import os
import sys

from . import save as sosave
from . import turn as soturn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TRACE = os.path.join(ROOT, "evidence",
                             "trace_m54b40b_20261024_212833.jsonl")
HUMAN_TF = 2


def tf_cycle(x):
    """The B3 engine models only the tf bit 0x2 (TF_CYCLE); the raw dword may carry
    other flag bits (turn 39 reads 1048578 = 0x100002) - mask to the modeled bit."""
    return ((x // 2) % 2) * HUMAN_TF


def key(d):
    return (d["year"], d["cur_player"], tf_cycle(d["turn_flags"]))


def emitted(engine, n_presses, start_key):
    seq = [start_key]
    for _ in range(n_presses):
        seq += [(s[2], s[0], s[1]) for s in engine.press()]  # (cur,tf,year)->(year,cur,tf)
    return seq


def miss_count(seq, snaps):
    j, miss = 0, []
    for k in snaps:
        while j < len(seq) and seq[j] != k:
            j += 1
        if j < len(seq):
            j += 1
        else:
            miss.append(k)
    return miss


def pair(sav_path, trace_path):
    sv = sosave.parse(sav_path)
    rows = [json.loads(l) for l in open(trace_path, encoding="utf-8")]
    turns = [r for r in rows if "turn" in r]
    n = len(turns)
    start_key = (sv.year, sv.own_player, 0)
    snaps = [key(turns[0]["state_before"])] + [key(t["state_after"]) for t in turns]

    g = {}

    # G1 shape: 40 consecutive turn rows 0..39
    consec = all(turns[i]["turn"] == i for i in range(n)) and n == 40
    g["trace-shape"] = consec

    # G2 the pair chain: before(0)==save start, before(t)==after(t-1) for every t
    chain = key(turns[0]["state_before"]) == start_key and all(
        key(turns[i]["state_before"]) == key(turns[i - 1]["state_after"])
        for i in range(1, n))
    g["pair-chain"] = chain

    # G3 the emission contains every recorded snapshot, in order, 0 missing
    eng = soturn.Engine(sv.year, human=sv.own_player)
    seq = emitted(eng, n, start_key)
    miss = miss_count(seq, snaps)
    g["snapshots-covered"] = not miss

    # G4 the recorded year-before == save year + turn on every row
    g["year-before"] = all(t["state_before"]["year"] == sv.year + t["turn"]
                           for t in turns)

    # G5 rivals FAIL the same fit: reversed order and year_after=0 both miss the
    # (2190,7,2) year-fire witness (year fired while cur still 7 on turn 39)
    r_rev = miss_count(emitted(soturn.Engine(sv.year, human=sv.own_player,
                                             order=[3, 2, 1, 0, 7, 6, 5, 4]), n,
                               start_key), snaps)
    r_ya = miss_count(emitted(soturn.Engine(sv.year, human=sv.own_player,
                                            year_after=0), n, start_key), snaps)
    g["rival-reversed"] = len(r_rev) >= 1
    g["rival-year-edge"] = len(r_ya) >= 1

    # G6 frontier declared and measured: model n_bases constant (save's count) vs the
    # recorded growth - the delta is the finding (no AI founder in the sim), reported
    nb = [t["state_after"]["n_bases"] for t in turns]
    frontier = {"model_const": sv.n_bases, "recorded_first": nb[0],
                "recorded_last": nb[-1], "delta": nb[-1] - nb[0]}
    g["frontier-declared"] = (frontier["model_const"] == nb[0]
                              and frontier["delta"] >= 1)

    report = {"rung": "B9", "sav": os.path.basename(sav_path),
              "trace": os.path.basename(trace_path),
              "turns": n, "snapshots": len(snaps), "missing": [list(m) for m in miss],
              "rival-reversed-miss": len(r_rev), "rival-year-edge-miss": len(r_ya),
              "frontier_n_bases": frontier, "gates": g}
    blob = json.dumps(report, sort_keys=True, separators=(",", ":"))
    return sv, eng, report, blob, g


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sim.parity")
    ap.add_argument("--sav", required=True)
    ap.add_argument("--trace", default=DEFAULT_TRACE)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    sv, eng, report, blob, g = pair(a.sav, a.trace)
    bad = [k for k, ok in g.items() if not ok]
    for k in sorted(g):
        print("  %s %s" % ("ok  " if g[k] else "BAD ", k))
    print("frontier n_bases: model const=%d, recorded %d -> %d (delta +%d, not "
          "modeled - AI base founder)" % (report["frontier_n_bases"]["model_const"],
                                          report["frontier_n_bases"]["recorded_first"],
                                          report["frontier_n_bases"]["recorded_last"],
                                          report["frontier_n_bases"]["delta"]))
    if bad:
        print("FAIL B9: %d/%d gates failed: %s" % (len(bad), len(g), "; ".join(bad)))
        if a.out:
            with open(a.out, "w") as fh:
                fh.write(blob)
        return 1
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(blob)
    print("PASS B9: %d/%d gates - %d-turn golden trace pairs %d/%d snapshots on %s "
          "(final %s, sha256 %s)" % (len(g), len(g), report["turns"],
                                     report["snapshots"] - len(report["missing"]),
                                     report["snapshots"], os.path.basename(a.sav),
                                     list(eng.state()),
                                     hashlib.sha256(blob.encode()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
