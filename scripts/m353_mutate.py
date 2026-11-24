#!/usr/bin/env python3
"""m353_mutate.py - every M353 gate must redden under a named mutation.

Each mutant perturbs ONE measured quantity (a ref kind, a store, a band bound, a token radix, a
caller's literal k, a rival's premise) and asserts the gate that claims it FLIPS to FAIL.  A gate
that survives its own mutant was never measuring anything.

    python3 -u scripts/m353_mutate.py
"""
import copy
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m353_numeric_band as M  # noqa: E402

EVID = os.path.join(M.ROOT, "evidence/m353_mutate.txt")


def gate_state(m):
    return {name.split(":")[0].split(" ")[0]: ok for name, ok, _ in M.gates(m)}


def find(m, addr):
    return next(r for r in m["refs"] if r["addr"] == addr)


def mu1(m):  # drop one absolute read -> the census stops adding up
    m["refs"] = [r for r in m["refs"] if r["addr"] != 0x41A4E0]


def mu2(m):  # call the one indexed store absolute (M325's absolute-only view)
    find(m, 0x626597)["kind"] = "abs"


def mu3(m):  # move the payload band by one dword -> geometry no longer tiles
    m["geometry"]["pay"] = m["geometry"]["pay"] + 4


def mu4(m):  # setter bound 8 instead of 9 -> the last slot becomes unaddressable
    m["setter"]["bound"] = (m["setter"]["bound"][0], 8)


def mu5(m):  # a caller that passes an out-of-band literal k
    m["calls"] = m["calls"] + [dict(addr=0xDEAD00, fn="MUTANT", k=10, kind="imm")]


def mu6(m):  # $HEX folded into $NUM (the pre-M199 reading)
    find(m, 0x625E4B)["token"] = (0x699128, "$NUM")


def mu7(m):  # $HEX really converts to base 16
    find(m, 0x625E4B)["radix"] = 16


def mu8(m):  # the `$#` path is bounded after all
    m["pred"]["bound10"] = [(0x62608C, "cmp    eax,0xa")]


def mu9(m):  # the numeric band starts one dword late -> k=10 no longer lands on owner[0]
    m["geometry"]["num"] = 0x999FA8


def mu10(m):  # the indexed store counted as an absolute writer (rival R1 restored)
    m["abs_writers"] = m["abs_writers"] + [0x626597]
    m["scaled_writers"] = []


def mu11(m):  # the publisher does touch the numeric band
    m["publisher"]["refs"] = [dict(addr=0x6266AA)]


def mu12(m):  # permute the address->token attribution (a set check would miss this)
    a, b = find(m, 0x625C2C), find(m, 0x625E4B)
    a["token"], b["token"] = b["token"], a["token"]


def mu13(m):  # the radix push is not arg3 any more (one extra push between)
    find(m, 0x625E4B)["push_between"] = 3


def mu14(m):  # text stride read as the raw shift 8, not 1<<8
    m["geometry"]["txt_stride"] = 8


MUTANTS = [
    ("MU1", "G1", "drop absolute read 0x41a4e0", mu1),
    ("MU2", "G2", "626597 reclassified abs", mu2),
    ("MU3", "G3", "payload band moved +4", mu3),
    ("MU4", "G4", "setter bound 9->8", mu4),
    ("MU5", "G5", "caller with literal k=10", mu5),
    ("MU6", "G6", "625e4b token folded to $NUM", mu6),
    ("MU7", "G7", "$HEX radix 10->16", mu7),
    ("MU8", "G8", "bound added on the `$#` path", mu8),
    ("MU9", "G9", "numeric base +4", mu9),
    ("MU10", "R1", "scaled store counted absolute", mu10),
    ("MU11", "R2", "publisher gains a ref", mu11),
    ("MU12", "G6", "token attribution permuted", mu12),
    ("MU13", "G7", "radix push not 3rd arg", mu13),
    ("MU14", "G3", "text stride = raw shift", mu14),
]


def main():
    base_m = M.measure(M.DUMP, M.EXE)
    base = gate_state(base_m)
    lines = ["M353 MUTANT HARNESS (baseline gates: %d, all green=%s)"
             % (len(base), all(base.values()))]
    rows = []
    for mid, gate, desc, fn in MUTANTS:
        m = copy.deepcopy(base_m)
        fn(m)
        st = gate_state(m)
        red = [g for g, ok in st.items() if not ok]
        rows.append((mid, gate, desc, st.get(gate, None), red))
        lines.append("  %-4s -> %-3s %-34s target=%s reddened=%s"
                     % (mid, gate, desc, "FAIL" if st.get(gate) is False else "STILL PASS",
                        ",".join(sorted(red)) or "-"))
    ok = all(r[3] is False and r[1] in r[4] for r in rows) and all(base.values())
    d = hashlib.sha1("\n".join(lines).encode()).hexdigest()[:16]
    lines.append("")
    if ok:
        lines.append("HARNESS PASS %d/%d mutants redden their named gate  digest %s"
                     % (len(rows), len(MUTANTS), d))
    else:
        lines.append("HARNESS FAIL %d/%d mutants redden their named gate  digest %s"
                     % (len(rows), len(MUTANTS), d))
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if ok:
        with open(EVID, "w") as f:
            f.write(text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
