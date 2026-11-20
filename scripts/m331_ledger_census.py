#!/usr/bin/env python3
"""M331 (chain2 s10): block+0x2fc / +0x308 census — the upkeep LEDGER SIBLINGS.

STATIC, zero box. Reuses M326's reviewed resolver (import m326_block224_census,
subreg-aware affine backward evaluator + lea-seed scan), retargeted per offset.
M330's import-patch pattern: M331_PATCH env applies instruction patches to
m326.INS AFTER import; every patched site is LITERAL-read by an exact-address
pin below (review_lint L2b, M328 lesson).

Footing: NAMED ## M330/M326/M325/M324. Upkeep entry 520540 zeroes +3f8/+2fc/
+300/+308 (520561/567/56d/573). Ledger @52081a-841: +310 := +2fc;
+30c := +308 - +300 + +2fc. Hook: 535c60/546800 read (+2fc - +300) as a
x100 credit-like cap (M330 G12: 54b361 loads +2fc, 54b367 loads +300).

Acceptance: python3 -u scripts/m331_ledger_census.py -> table FIRST, then
gates, digest; re-run must be byte-identical. Mutants: scripts/m331_mutate.py.
"""
import hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326

BLKBASE, STRIDE, NBLK = 0x94d430, 0x20bc, 8

def retarget(off):
    m326.OFF = off
    m326.FADDRS = [BLKBASE + off + k * STRIDE for k in range(NBLK)]
    m326.ENERGY_OFF = 0x220
    m326.EADDRS = [BLKBASE + 0x220 + k * STRIDE for k in range(NBLK)]

def apply_patch():
    p = os.environ.get("M331_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in m326.INS:
                raise SystemExit("M331_PATCH address not in .text cache: %s" % addr)
            if m326.INS[a] == (mn, ops.strip()):
                raise SystemExit("M331_PATCH applied to nothing (already equal)")
            m326.INS[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M331_PATCH applied to nothing")
    return n

NPATCH = apply_patch()
ALGO = os.environ.get("M331_ALGO", "0")   # 1 = provenance filter OFF (algorithm mutant)

def ins(a):
    return m326.INS[a]

ROWS = []
GATES = []

def row(s):
    ROWS.append(s)
    print(s)

def gate(name, ok, detail):
    GATES.append((name, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", name, detail))

def digest():
    return hashlib.sha256("\n".join(ROWS).encode()).hexdigest()[:16]

def census_at(off):
    retarget(off)
    hits = m326.census()
    seeds, accesses = m326.seed_scan()
    field, nonfield = [], []
    for h in hits:
        a, w, r, width, tag, mi, src = h
        if mi[0] == "abs":
            prov = ("ABS", None)
        elif ALGO == "1":
            prov = ("STRIDE", None)
        else:
            prov = m326.base_tag(a, mi)
        if prov[0] in ("BLKCONST", "STRIDE", "ABS"):
            field.append((h, prov))
        else:
            nonfield.append((h, prov))
    return field, nonfield, seeds, accesses

def main():
    print("== M331 ledger-siblings census (resolver: M326 import) patches=%d ==" % NPATCH)
    for off in (0x2fc, 0x308):
        field, nonfield, seeds, accesses = census_at(off)
        row("OFF %x: rawhits=%d FIELD=%d nonfield=%d seeds=%d seedacc=%d"
            % (off, len(field) + len(nonfield), len(field), len(nonfield),
               len(seeds), len(accesses)))
        for (a, w, r, width, tag, mi, src), p in field:
            row("  hit %06x %s%s w=%d tag=%s prov=%s src=%s owner=%s"
                % (a, "W" if w else "-", "R" if r else "-", width, tag, p[0], src,
                   m326.owner(a)))
        for (a, w, r, width, tag, mi, src), p in nonfield:
            row("  NONFIELD %06x %s%s tag=%s prov=%s owner=%s"
                % (a, "W" if w else "-", "R" if r else "-", tag, p, m326.owner(a)))
        for a, dest, tgt in seeds:
            if tgt[0] == off:
                row("  seed %06x ->%s tgt=%s" % (a, dest, tgt))
        for a, dest, b, w, width, d, ea, hit_off, src, stag in accesses:
            if hit_off == off:
                row("  seedacc %06x %s[%+d]=%06x w=%d insn=%s" % (a, dest, d, ea, w, ins(b)))
    d = digest()
    npass = sum(1 for _, ok in GATES if ok)
    print("digest %s" % d)
    print("== M331: %d/%d ==" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())