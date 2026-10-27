#!/usr/bin/env python3
"""M71 tests: the pop's shift composition, the log parser, and the acceptance gates.

The REAL run (evidence/m71pop.gdblog, evidence/m71pop_seq.jsonl, 2026-10-27, University
Base idx 0, round 51 -> 53) is the positive fixture; every negative fixture is a real
shape with ONE number changed, and must FAIL.

    python3 scripts/test_m71_pop.py
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import m71_pop_watch as X    # noqa: E402

REAL_LOG = os.path.join(ROOT, "evidence", "m71pop.gdblog")

# ---- the real run, read back from memory before/after (see SESSION_NOTES session 111)
BEFORE = dict(i=0, addr=0x95DA10, name="University Base", fac=3, pending=2,
              slots=[2, 193, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0], minerals=9, income=0,
              year=2151, round=51, cursor=0, n_units=68, counts={2: 1, 193: 1, 192: 1})
AFTER = dict(i=0, addr=0x95DA10, name="University Base", fac=3, pending=1,
             slots=[193, 192, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0], minerals=0, income=0,
             year=2153, round=53, cursor=0, n_units=74,
             counts={2: 0, 193: 1, 192: 1})   # the SAME id set as before, read back after

REAL_LOG_TEXT = """ARMED base=0x95da10 cursor=0 pending=2 s0=2 s1=193 s2=192 s3=0
VISIT idx=0 pend=2 s0=2 s1=193 s2=192 s3=0 min=9
PAYA base=0x95da10 storage=9 edi=9
CREATE id=2 arg3=3 storage=0
POPIN idx=0 pend=2 own=197379 s0=2 s1=193 s2=192 s3=0 min=0
POPDEC count=0x9540ba byte=1 head=2 pend=2
POPAFT count=0x9540ba byte=0 head=2
SLOT1WRITE pc=0x4ef62e now=192
POPCNT newpend=1 s0=193 s1=192 s2=192 s3=0
POPRES head=193 r=1 pend=1
POPEXIT head=193 pend=1
VISIT idx=0 pend=1 s0=193 s1=192 s2=192 s3=0 min=0
"""

results = []


def check(name, got, want):
    ok = got == want
    results.append((name, ok, "" if ok else f"got {got!r} want {want!r}"))


def check_true(name, cond, detail=""):
    results.append((name, bool(cond), detail))


# ---------------------------------------------------------------- shift composition
# The pop's loop shifts only 0..pending_j-1 and pending shrinks, so K iterations do NOT
# mean "shift left by K": index k is written (pending-k) times.
check("shift K=0 is identity", X.shift_predict([2, 193, 192, 0], 2, 0), [2, 193, 192, 0])
check("shift K=1 pending 2", X.shift_predict([2, 193, 192, 0], 2, 1), [193, 192, 192, 0])
check("shift K=2 pending 2 (drain)", X.shift_predict([2, 193, 192, 0], 2, 2), [192, 192, 192, 0])
check("shift K=1 pending 3", X.shift_predict([9, 10, 11, 12, 0], 3, 1), [10, 11, 12, 12, 0])
check("shift K=2 pending 3", X.shift_predict([9, 10, 11, 12, 0], 3, 2), [11, 12, 12, 12, 0])
check("shift K=3 pending 3 (drain)", X.shift_predict([9, 10, 11, 12, 0], 3, 3), [12, 12, 12, 12, 0])

# ---------------------------------------------------------------- attribution
check("pop shift store maps from the next instruction",
      X.attribute_queue_store(0x4EF62E), (0x4EF62C, True))
check("enqueue store maps from the next instruction",
      X.attribute_queue_store(0x417E08), (0x417E04, True))
check("an unrelated pc stays unmapped",
      X.attribute_queue_store(0x412340), (0x412340, False))

# ---------------------------------------------------------------- parser
ev = X.parse(REAL_LOG_TEXT)
tags = [e["tag"] for e in ev]
check("parser sees the whole real stream", tags,
      ["ARMED", "VISIT", "PAYA", "CREATE", "POPIN", "POPDEC", "POPAFT", "SLOT1WRITE",
       "POPCNT", "POPRES", "POPEXIT", "VISIT"])
sw = [e for e in ev if e["tag"] == "SLOT1WRITE"][0]
check("slot write maps to the pop shift store", (sw["store_pc"], sw["mapped"]),
      (0x4EF62C, True))
check("POPCNT carries the post-shift slots",
      [e for e in ev if e["tag"] == "POPCNT"][0]["s1"], 192)
check("POPAFT reads the byte at the address the GAME computed",
      [e for e in ev if e["tag"] == "POPAFT"][0]["count"], 0x9540BA)

# ---------------------------------------------------------------- the real acceptance
ok, gates, find = X.score(BEFORE, AFTER, ev, BEFORE["addr"])
check_true("the REAL run passes every gate", ok,
           "; ".join(g[2] for g in gates if not g[1]))
check_true("the real run names 1 pop iteration", "K (pop iterations) = 1" in find[0], find[0])
check_true("SINGLE and DRAIN predicted different regions (non-vacuous)",
           "the read-back matches SINGLE" in find[0], find[0])
check_true("the run reports the pay it saw with edi = the price",
           "PAYA storage 9 edi 9" in find[1], find[1])
check_true("no cursor write happened at the completion",
           not [e for e in ev if e["tag"] == "CURSORWRITE"], str(tags))

# ---------------------------------------------------------------- negative fixtures
def mutate(fn):
    b, a, e = copy.deepcopy(BEFORE), copy.deepcopy(AFTER), copy.deepcopy(ev)
    fn(b, a, e)
    return X.score(b, a, e, b["addr"])


def fails(name, fn, want_sub=""):
    ok, gates, _ = mutate(fn)
    bad = [g[0] for g in gates if not g[1]]
    check_true(name, (not ok) and (want_sub in "".join(bad) if want_sub else not ok),
               f"gates that fired: {bad}")


# a base that just PRODUCED left the head shifted: if the engine had re-sorted the region
# instead of shifting, the read-back would be this, and gate 5 must refuse it.
fails("region rewritten (sorted) instead of shifted",
      lambda b, a, e: a.__setitem__("slots", [193, 192, 0, 0, 0, 0, 0, 0, 0, 0, 9225, 0]),
      "5 region")
fails("pending decremented twice for one logged iteration",
      lambda b, a, e: a.__setitem__("pending", 0), "4 pending")
fails("no pop in the window (the completion never ran)",
      lambda b, a, e: [e.pop(i) for i in sorted(
          (i for i, x in enumerate(e) if x["tag"] in ("POPIN", "POPDEC", "POPAFT",
                                                      "POPCNT", "POPRES", "POPEXIT")),
          reverse=True)],
      "2 window")
fails("a slot write from an unmapped pc is named, not waved through",
      lambda b, a, e: e.insert(8, dict(tag="SLOT2WRITE", slot=2, pc=0x412340, now=7,
                                      store_pc=0x412340, mapped=False, store_name="UNMAPPED")),
      "7 every queue-slot write")
fails("a cursor write from an unmapped pc fails",
      lambda b, a, e: e.insert(8, dict(tag="CURSORWRITE", pc=0x412340, now=4,
                                      store_pc=0x412340, mapped=False,
                                      store_name="UNMAPPED")),
      "7 every cursor write")
fails("the queued-count byte did not move",
      lambda b, a, e: a.__setitem__("counts", {2: 1, 193: 1, 192: 1}),
      "6 queued-count bytes")
fails("the armed record moved out from under the watchpoints",
      lambda b, a, e: a.__setitem__("addr", 0x95DB30), "8 armed record")
fails("no round boundary crossed",
      lambda b, a, e: a.__setitem__("round", b["round"]), "2 window")
fails("the walk stopped with pending left over and no logged refusal",
      lambda b, a, e: (e.pop(next(i for i, x in enumerate(e) if x["tag"] == "POPEXIT")),
                       e.pop(next(i for i, x in enumerate(e) if x["tag"] == "POPRES"))),
      "3 walk")

# a shape the two candidates cannot separate must not be allowed to claim anything
b, a, e = copy.deepcopy(BEFORE), copy.deepcopy(AFTER), copy.deepcopy(ev)
b["pending"], b["slots"] = 1, [2, 193, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0]
ok, gates, _ = X.score(b, a, e, b["addr"])
check_true("pending 1 cannot discriminate SINGLE from DRAIN",
           not ok and any("1 shape" in g[0] and not g[1] for g in gates))

# ---------------------------------------------------------------- the committed real logs
# run #3 (tag m71pop3) is the reproduction: same shape, same result, one difference —
# the round's income add put storage at 10 before the pay (minerals read back 9 -> 1).
AFTER3 = dict(AFTER, minerals=1, n_units=76)
for tag, log, seqf, aft in (("run m71pop", "m71pop.gdblog", "m71pop_seq.jsonl", AFTER),
                           ("run m71pop3 (reproduction)", "m71pop3.gdblog",
                            "m71pop3_seq.jsonl", AFTER3)):
    p = os.path.join(ROOT, "evidence", log)
    if not os.path.isfile(p):
        results.append((f"{tag}: gdblog present", False, p + " missing"))
        continue
    rev = X.parse(open(p, "r", errors="replace").read())
    seq = [json.loads(l) for l in
           open(os.path.join(ROOT, "evidence", seqf))]
    check(f"{tag}: gdblog parses to the committed seq rows", rev, seq)
    ok, gates, find = X.score(BEFORE, aft, rev, BEFORE["addr"])
    check_true(f"{tag}: passes the acceptance", ok,
               "; ".join(g[2] for g in gates if not g[1]))
    check_true(f"{tag}: names 1 pop iteration and matches SINGLE",
               "K (pop iterations) = 1" in find[0] and "matches SINGLE" in find[0], find[0])

n_ok = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{'' if ok else ': ' + detail}")
print(f"{n_ok}/{len(results)}")
print("PASS" if n_ok == len(results) else "FAIL")
sys.exit(0 if n_ok == len(results) else 1)
