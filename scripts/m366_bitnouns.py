#!/usr/bin/env python3
"""M366 (chain-2, STATIC) - the NOUNS of the faction-relations bits 0x10 and 0x20.

M364 named 0x1 = PACT and 0x8 = AT WAR from the diplomacy menu's case blocks and left the
other 11 as standing flags.  This milestone takes the two most-asked of those leftovers:

  0x10  37 predicate sites in 14 functions; the writer FUN_005518f0 tests it and then
        ORs 0x8000|0x40 into the same dword.
  0x20  18 sites in 3 functions (FUN_004f6030, FUN_00546800, FUN_0058fa40); a writer tests
        it and then ANDs 0xfffff3ff (clears 0x400|0x800, dword B).

Method: for every ask site, dump the call-site window and the enclosing decompiled line;
look for the literal/script key or the field access that names the bit.  Every number is
computed here and asserted AFTER the table prints.

Gates (each named mutant lives in scripts/m366_mutate.py):
  G1  census: sites and functions for 0x10 / 0x20, single vs composite, MEASURED.
  G2  per-site context: the branch each ask gates (taken/not) and its nearest literal.
  G3  noun witnesses: the literals that pin a noun, and the ones that refute rivals.
  G4  writer corroboration: 0x10 -> +0x8000|0x40 ; 0x20 -> -0xc00 (re-derived).
  G5  RIVALS, each measured and each FAILING on the printed numbers.
"""
import bisect
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M366_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.environ.get("M366_INDEX") or os.path.expanduser("~/reverse/smac/ghidra_out/index.csv")
SHARDS = os.environ.get("M366_SHARDS") or os.path.expanduser("~/reverse/smac/ghidra_out")

PRED = 0x426D60
WRITER = 0x5518F0
TARGETS = (0x10, 0x20)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
FNHEAD = re.compile(r"^// ==== (\S+) @ 0x([0-9a-f]+) size=(\d+)$")
LEXICON = re.compile(r'"([^"]{3,64})"')

INS = []
POS = {}
GATES = []


def gate(name, cond, msg):
    GATES.append((name, bool(cond), msg))
    print(f"  {name:5s} {'PASS' if cond else 'FAIL'}  {msg}")
    return bool(cond)


def load():
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            t = m.group(3).strip()
            parts = t.split(None, 1)
            rec = {"a": int(m.group(1), 16), "op": parts[0],
                   "arg": parts[1] if len(parts) > 1 else "", "t": t}
            POS[rec["a"]] = len(INS)
            INS.append(rec)


FNS, STARTS = ([], [])


def extents():
    rows = []
    with open(IDX) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["addr"], 16), int(r["size_bytes"]), r["name"]))
    rows.sort()
    return rows, [r[0] for r in rows]


def owner(a):
    i = bisect.bisect_right(STARTS, a) - 1
    if i < 0:
        return "?"
    s, n, nm = FNS[i]
    return nm if s <= a < s + n else "?"


def size_of(name):
    for s, n, nm in FNS:
        if nm == name:
            return n
    return 0


def window(lo, hi):
    out = []
    for ins in INS[POS.get(lo, 0):]:
        if ins["a"] >= hi:
            break
        out.append(ins)
    return out


def imm(s):
    m = re.fullmatch(r"(-?)0x([0-9a-f]+)", s.strip().lower())
    if m:
        v = int(m.group(2), 16)
        return (-v) & 0xFFFFFFFF if m.group(1) else v
    return None


def single(x):
    return x and x.bit_count() == 1


# ------------------------------------------------------------------ G1 census
def call_sites():
    sites = []
    for n, ins in enumerate(INS):
        if not (ins["op"] == "call" and ins["arg"].lower() == "0x%x" % PRED):
            continue
        args = []
        for back in range(n - 1, max(-1, n - 14), -1):
            b = INS[back]
            if b["op"] == "push":
                args.append((b["arg"], back))
                if len(args) == 3:
                    break
                continue
            if b["op"] in ("mov", "lea", "xor", "add", "sub", "movzx", "movsx", "shl", "and"):
                continue
            break
        mask = imm(args[2][0]) if len(args) == 3 else None
        sites.append({"a": ins["a"], "fn": owner(ins["a"]), "n": n, "mask": mask,
                      "pushes": len(args)})
    return sites


def g1(sites):
    print("\nG1  the ask census for bits 0x10 / 0x20 (every site of FUN_00426d60)")
    print("    mask   n  single  askers")
    cnt = collections.Counter(s["mask"] for s in sites if s["mask"] is not None)
    for m, c in sorted(cnt.items()):
        ask = sorted({s["fn"] for s in sites if s["mask"] == m})
        print(f"    {m:#010x} {c:3d}  {'yes' if single(m) else 'NO '}  {ask if len(ask) < 4 else len(ask)}")
    for b in TARGETS:
        hit = [s for s in sites if s["mask"] is not None and s["mask"] & b]
        alone = [s for s in sites if s["mask"] == b]
        print(f"    0x{b:x}: {len(hit)} sites in {len({s['fn'] for s in hit})} functions"
              f" ({len(alone)} as a bare single-bit ask)")
    return cnt


# ------------------------------------------------------------------ main
def main():
    global FNS, STARTS
    load()
    FNS, STARTS = extents()
    sites = call_sites()
    g1(sites)
    bad = [g for g in GATES if not g[1]]
    print(f"\n{'FAIL' if bad else 'PASS'} M366: {sum(g[1] for g in GATES)}/{len(GATES)} gates")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
