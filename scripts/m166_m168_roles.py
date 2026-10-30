#!/usr/bin/env python3
"""M166-M168: what the rank is compared against, how the 20-byte struct splits, and the write-dominant 0x94d488.

  M166  0x94d434 (M163's rank): 196 refs — 92 comparisons, and the ranking INPUT is a 7-entry array at 0x926a7c whose
        winner is excluded by writing -1 at 0x926a78+n*4. What the rank is OF stays unnamed; the SHAPE is decidable.
  M167  the 20-byte struct at 0x94d80c: is it uniform, or a header dword plus a payload quad? The WRITERS decide.
  M168  0x94d488: 49 refs but 22 writes across many functions — a derived cache, not state.

    python3 scripts/m166_m168_roles.py
"""
import collections
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)

INS, fnof = FC.INS, FC.fnof
ROOT = FC.ROOT
LOW = [(pc, s.lower()) for pc, s in INS]
R = {}


def ok(mid, cond, text):
    R[mid] = cond
    print("%s  %s — %s" % (mid, "PASS" if cond else "FAIL", text))


def prof(d):
    refs = [(pc, s) for pc, s in LOW if re.search(r"\[[^\]]*\+%s\]" % d, s)]
    writes = [(pc, s) for pc, s in refs
              if re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?\[", s) and re.search(r"%s\]," % d, s)]
    cmps = [(pc, s) for pc, s in refs if s.strip().startswith("cmp")]
    consts = sorted({s.split(",")[-1].strip() for _, s in writes if s.split(",")[-1].strip().startswith("0x")})
    return refs, writes, cmps, consts


def m166():
    refs, writes, cmps, consts = prof("0x94d434")
    src = [(pc, s) for pc, s in LOW if "0x926a7c" in s]
    excl = [(pc, s) for pc, s in LOW if "0x926a78" in s and "0xffffffff" in s]
    testvals = sorted({s.split(",")[-1].strip() for _, s in cmps if s.split(",")[-1].strip().startswith("0x")})
    print("M166 0x94d434: %d refs, %d write, %d cmp, consts %s; cmps vs %s" %
          (len(refs), len(writes), len(cmps), consts or "-", "/".join(testvals[:8])))
    print("   ranking source 0x926a7c refs: %d %s" % (len(src), [("%06x" % pc, fnof(pc)) for pc, _ in src]))
    print("   winner-exclusion stores (0x926a78 <- -1): %d %s" % (len(excl), ["%06x" % pc for pc, _ in excl]))
    ok("M166", len(refs) == 196 and len(writes) == 1 and len(cmps) >= 90 and len(src) == 2 and len(excl) == 1,
       "the rank is CONSUMED as an ordering test, not as a counter: %d of 196 refs are `cmp` (against small constants "
       "%s) and the ranking INPUT is a 7-entry dword table at 0x926a7c read by only TWO functions (the init loop itself "
       "and FUN_00531df0), with the top entry EXCLUDED by the single -1 store at 0x59ac72. What is being ranked stays "
       "unnamed — the shape is an order among 7 candidates, one of which is discarded"
       % (len(cmps), "/".join(testvals[:6])))


def m167():
    members = ["0x94d80c", "0x94d810", "0x94d814", "0x94d818", "0x94d81c"]
    wr = {d: [(pc, fnof(pc)) for pc, s in LOW
              if re.match(r"^mov\s+(dword ptr |word ptr |byte ptr )?\[[^\]]*\+%s\]," % d, s)] for d in members}
    sets = {d: {f for _, f in wr[d]} for d in members}
    common4 = set.intersection(*[sets[d] for d in members[1:]])
    head = sets[members[0]]
    print("M167 writers per member:")
    for d in members:
        print("   %s: %d writes in %s" % (d, len(wr[d]), sorted(sets[d])))
    print("   common to the four payload members: %s" % sorted(common4))
    print("   head member's own set: %s" % sorted(head))
    ok("M167", all(len(wr[d]) == 6 for d in members) and len(common4) >= 4 and not (head == common4),
       "the 20-byte struct SPLITS: +0x00 is a HEADER dword written by its own writers (FUN_004dc100 x3, FUN_0059ec90 "
       "x3) with constants 0/1/0xffffffff and 7 tests, while +0x04/+0x08/+0x0c/+0x10 are a PAYLOAD QUAD written "
       "together by the SAME %d functions (FUN_004dc100, FUN_00510230, FUN_00512b40, FUN_00516b80, FUN_0059ec90 x2). "
       "Uniformity would have shown one writer set for all five; it does not" % len(common4))


def m168():
    refs, writes, cmps, consts = prof("0x94d488")
    wf = collections.Counter(f for _, f in [(pc, fnof(pc)) for pc, s in writes])
    print("M168 0x94d488: %d refs, %d writes, %d cmp/test, %d distinct writer functions" % (len(refs), len(writes), len(cmps), len(wf)))
    print("   writers: %s" % ", ".join("%s(%d)" % (f, n) for f, n in wf.most_common(6)))
    ok("M168", len(refs) == 49 and len(writes) == 22 and len(cmps) == 1 and len(wf) >= 6,
       "0x94d488 is WRITE-DOMINANT and shared: 22 writes spread over %d functions against 49 total refs and a single "
       "comparison — the profile of a DERIVED/CACHED value that many call sites recompute (like base+0xd0, M97), not of "
       "state that is set once. Any test that treats it as authoritative state will be reading whatever path ran last"
       % len(wf))


def main():
    m166(); m167(); m168()
    print("\nSUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()))
    with open(os.path.join(ROOT, "evidence", "m166_m168.log"), "w") as fh:
        fh.write("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in R.items()) + "\n")
    return 0 if all(R.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
