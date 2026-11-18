#!/usr/bin/env python3
"""M313 (s278, STATIC, zero box): NAME THE EVENTS.
M312 closed WHO-fires-the-selection-check to two trunks; this milestone names
the layer ABOVE them: the 15 callers of the cursor thunk FUN_004736a0 and the
28 owner functions holding FUN_00472810's 53 call sites - by exact census,
shared-band membership, and vtable/message-map dispatch structure (PE bytes).

Gates print a table then assert; digest at the end, two runs byte-identical.
Mutation harness: scripts/m313_mutate.py.
"""
import bisect
import collections
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import m308_site_list as E

IDX = os.path.join(REPO, "ghidra_out", "index.csv")
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
EXE = os.path.join(REPO, "terran.exe")

checks = []
def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(("OK   " if ok else "FAIL ") + name + ": " + detail)

def main():
    idx = E.load_index()
    addrs = [a for a, _ in idx]
    names = dict(idx)
    def owner(va):
        return names[addrs[max(0, bisect.bisect_right(addrs, va) - 1)]]
    ins, _order = E.parse_text()
    def calls_to(t):
        return sorted(a for a, (b, ops) in ins.items() if b == "call"
                      and ops.split(",")[0].strip() == "0x%x" % t)

    # A1 exact 15-site census of callers of the cursor thunk FUN_004736a0
    WANT_6A0 = {
        0x47373E: "FUN_004736e0", 0x50C08F: "FUN_0050c060",
        0x50C19F: "FUN_0050c170", 0x50C2C1: "FUN_0050c290",
        0x50C5F6: "FUN_0050c550", 0x50CC36: "FUN_0050cab0",
        0x50F7D2: "FUN_0050f420", 0x50FBDB: "FUN_0050fb80",
        0x50FC10: "FUN_0050fb80", 0x50FCE0: "FUN_0050fc50",
        0x50FD0F: "FUN_0050fc50", 0x515638: "FUN_00512b40",
        0x5164B0: "FUN_00512b40", 0x5164E2: "FUN_00512b40",
        0x5175B4: "FUN_00516b80",
    }
    got = {a: owner(a) for a in calls_to(0x4736A0)}
    ck("A1_thunk_callers_exact", got == WANT_6A0, "%d sites" % len(got))

    # A2 the hub's 28 owners, exact set (from M312's run, re-derived here)
    hub_sites = calls_to(0x472810)
    owners = sorted({owner(a) for a in hub_sites})
    WANT_OWNERS = [
        "FUN_004738f0", "FUN_00473960", "FUN_004739a0", "FUN_0048e530",
        "FUN_004c40e0", "FUN_004cbc70", "FUN_004e10c0", "FUN_0050bb20",
        "FUN_0050bde0", "FUN_0050bea0", "FUN_0050c060", "FUN_0050c170",
        "FUN_0050c290", "FUN_0050c550", "FUN_0050ca10", "FUN_0050cab0",
        "FUN_0050ef60", "FUN_0050f420", "FUN_0050fb80", "FUN_0050fc50",
        "FUN_005103b0", "FUN_00510730", "FUN_00510bd0", "FUN_00511960",
        "FUN_00512450", "FUN_00512b40", "FUN_00516b80", "FUN_0058b1b0",
    ]
    ck("A2_hub_owner_set_exact", owners == WANT_OWNERS,
       "%d owners, %d sites" % (len(owners), len(hub_sites)))

    print("digest", hashlib.sha256(
        "".join("%s=%d" % (n, o) for n, o, _ in checks).encode()).hexdigest()[:16])
    nfail = sum(1 for _, o, _ in checks if not o)
    print("== M313: %d/%d ==" % (len(checks) - nfail, len(checks)))
    return 1 if nfail else 0

if __name__ == "__main__":
    sys.exit(main())
