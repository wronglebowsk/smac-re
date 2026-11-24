#!/usr/bin/env python3
"""scripts/b33_mutate.py - every B33 gate must redden under a named mutation.

Each mutant perturbs ONE measured quantity of the B33 model - a census operand, a branch
target, the Virgin Soil anchor, the score's leg classification, the rival bookkeeping - and
asserts that the named gate FLIPS to FAIL.  A gate that survives its own mutant was never
measuring anything.

    python3 -u scripts/b33_mutate.py            # writes evidence/b33_mutate.txt
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from sim import facilityleg as F  # noqa: E402

EVID = os.path.join(ROOT, "evidence", "b33_mutate.txt")


def fresh():
    return dict(census=F.load_census(), keys=F.load_keys(), samples=F.fa.load_trace())


def setop(raw, addr, op=None, mnem=None):
    rows = raw["census"]
    for i, (a, ln, m, o) in enumerate(rows):
        if a == addr:
            rows[i] = (a, ln, mnem or m, o if op is None else op)
            return
    raise KeyError("0x%06x not in census" % addr)


def mu1(raw):                      # the gate local renamed -> no write site is left
    setop(raw, 0x4EF8A4, op="w[ebp-0x34]")


def mu2(raw):                      # the stamp's only entry edge re-pointed past the OR
    setop(raw, 0x4F0D94, op="0x4f0ec2")


def mu3(raw):                      # the facility path made to jump into the unit spend+stamp block
    setop(raw, 0x4EFE44, op="0x4f0ca1")


def mu4(m):                        # a unit completion relabelled a facility completion
    unit = [r for r in m["rows"] if r["kind"] == "UNIT"][0]
    unit["kind"] = "FACILITY"


def mu5(m):                        # the Virgin Soil window doctored to look stamped
    m["vs"]["win_a"] = "0400000800000000"


def mu6(m):                        # the facility gain set given the head's own bit
    m["vs"]["gain"] = {2, 4}


def mu7(m):                        # Virgin Soil's mapper byte pushed off the eight-byte map
    m["vs"]["by"] = 40


def mu8(m):                        # the after-pop head made to equal the before head (a hit)
    unit = [r for r in m["rows"] if r["kind"] == "UNIT"][0]
    unit["head_after"] = unit["head"]


def mu9(raw):                      # the census loses its last instruction (truncated dump)
    raw["census"] = raw["census"][:-1]


def mu10(raw):                     # a branch target outside the span (an open CFG)
    setop(raw, 0x4EF7D6, op="0x4f3000")


def mu11(raw):                     # the facility spend's `sub` relabelled `add` (same addresses)
    setop(raw, 0x4EFEDB, mnem="add")


# (id, gate that must redden, description, pre-build mutator, post-build mutator)
MUTANTS = [
    ("MU1", "G5", "the single write of [ebp-0x30] renamed to [ebp-0x34]", mu1, None),
    ("MU2", "G4", "0x4f0d94 re-pointed past the stamp block (a second door)", mu2, None),
    ("MU3", "G3", "the facility path re-pointed into the unit spend+stamp block", mu3, None),
    ("MU4", "G7", "one unit completion relabelled FACILITY (the score's premise)", None, mu4),
    ("MU5", "G8", "the Virgin Soil after-window doctored to the stamp prediction", None, mu5),
    ("MU6", "G7", "the Virgin Soil gain set given the head's own bit", None, mu6),
    ("MU7", "G9", "Virgin Soil's mapper byte moved off the eight-byte map", None, mu7),
    ("MU8", "G9", "the after-pop head counted as a hit", None, mu8),
    ("MU9", "G1", "the census truncated by one instruction", mu9, None),
    ("MU10", "G2", "a branch target outside the function span (open CFG)", mu10, None),
    ("MU11", "G6", "the facility spend's `sub` relabelled `add`", mu11, None),
]


def main():
    base = F.build()
    base_st = {g[0]: g[2] for g in F.gates(base)}
    lines = ["B33 MUTANT HARNESS (baseline gates: %d, all green=%s)"
             % (len(base_st), all(base_st.values()))]
    rows = 0
    for mid, gate, desc, pre, post in MUTANTS:
        raw = fresh()
        if pre:
            pre(raw)
        m = F.build(**raw)
        if post:
            post(m)
        st = {g[0]: g[2] for g in F.gates(m)}
        red = not st[gate]
        also = [g for g in st if not st[g] and g != gate]
        rows += int(red)
        lines.append("%s %-4s %-38s reddens %-3s also=%s" %
                     ("ok  " if red else "FAIL", mid, desc, gate, ",".join(also) or "-"))
    lines.append("MUTANTS %d/%d" % (rows, len(MUTANTS)))
    text = "\n".join(lines) + "\n"
    with open(EVID, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text, end="")
    print("baseline all-green=%s  mutants=%d/%d" % (all(base_st.values()), rows, len(MUTANTS)))
    return 0 if (all(base_st.values()) and rows == len(MUTANTS)) else 1


if __name__ == "__main__":
    sys.exit(main())
