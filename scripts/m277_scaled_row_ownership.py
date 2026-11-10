#!/usr/bin/env python3
"""M277 - whose row owns the SCALED (0x5584aa) vs UNSCALED (0x558452) read of
0x94eaa8, and does M274's "regions 94..127 spill into the sibling verdict array"
survive for the unfactioned (scaled) one?

Static only - zero box time. Reuses scripts/m276_fold_stride.py's evaluator
(skill law: do not re-derive the fold; evaluate).

ANSWER: the unscaled site indexes 0x94eaa8 by the fold slot [ebp-0x18] =
2*region + 8380*arg -> faction block `arg`'s row. The scaled site indexes the
same base by [ebp-0x10]*2 = 2*region, NO block term -> always block 0. The
image-wide referrer census says exactly 4 sites touch +0x94eaa8; the only two
WRITERS both carry the 8380*block fold, so the row is per-block live data and
the scaled read is the image's unique block-0 (faction-0) view of it.
M274 G2's landing claim dies arithmetically: the loop's max index is 127, so
the scaled byte offset maxes at 2*127 = 254 - 68 B SHORT of the sibling base
at +256 (0x94eba8). Regions 94..127 never read the verdict array; they stay
inside block 0's 256-B cell. (What survives of M274: G1 single bound, G4
verdict skip, G5 verdict stores - different array.)
"""
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
LOG = os.path.join(ROOT, "evidence", "m273w3.gdblog")
M276 = os.path.join(ROOT, "scripts", "m276_fold_stride.py")
FUN_END = 0x556690 + 14349
BASE, SIBLING = 0x94EAA8, 0x94EBA8
STRIDE = 8380

# reuse m276's evaluator WITHOUT running its main(): exec defs only
_src = open(M276).read()
_ns = {"__file__": M276}
exec(_src[:_src.index("def main(")], _ns)
m276_body, m276_eval = _ns["body"], _ns["evaluate"]


def load(lo, hi):
    ins, addr, pat = [], {}, re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if not m or not m.group(3):
                continue
            a = int(m.group(1), 16)
            if a < lo:
                continue
            if a >= hi:
                break
            ins.append((a, m.group(3), m.group(4).split("#")[0].strip()))
            addr[a] = (m.group(3), m.group(4).split("#")[0].strip())
    return ins, addr


def neuter(addr, sites, why):
    """A memory-load insn feeding an atom of origin: neuter it so the seeded
    atom survives evaluate() (the load's own provenance is not a mul chain)."""
    for a in sites:
        op, ar = addr[a]
        assert op == "mov" and "[" in ar, "site %#x is not a load (%s %s)" % (a, op, ar)
        addr[a] = ("nop", "nop")


def chain_eval(addr, lo, hi, atoms):
    _ns["ATOMS"].clear()
    _ns["ATOMS"].update(atoms)
    order = sorted(addr)
    ins = [(a,) + addr[a] for a in order if lo <= a <= hi]
    st, trace, unk = m276_eval(ins, addr, lo, hi)
    return st, unk


def ecx_writers(addr, lo, hi):
    out, dst = [], _ns["dst_regs"]
    for a in sorted(addr):
        if lo <= a <= hi:
            op, ar = addr[a]
            if "ecx" in dst(op, ar):
                out.append(hex(a))
    return out


def main():
    g, res = [], []

    def gate(n, ok, text):
        res.append(ok)
        print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", text))

    # ---- G1: the two sites' OWN encoding: different frame slots feed them
    ins, addr = load(0x556690, FUN_END)
    assert addr[0x558452] == ("mov", "ax,WORD PTR [edi+0x94eaa8]"), "cache drift 0x558452"
    assert addr[0x5584aa] == ("mov", "cx,WORD PTR [edi*2+0x94eaa8]"), "cache drift 0x5584aa"
    f_uns = addr[0x55844b]
    f_scl = addr[0x5584a5]
    ok = (f_uns == ("mov", "edi,DWORD PTR [ebp-0x18]")
          and f_scl == ("mov", "edi,DWORD PTR [ebp-0x10]"))
    gate(1, ok, "UNSCALED feeder %#x = %s %s (fold slot); SCALED feeder %#x = %s %s "
         "(region counter) - DIFFERENT slots, the two read sites do not share a row; "
         "rival model 'one index feeds both' is refuted by the bytes"
         % (0x55844b, *f_uns, 0x5584a5, *f_scl))

    # ---- G2: reuse m276's evaluator: the fold at the store; ecx is the LIVE
    # loop counter at every iteration (back-edge carries the incremented reg)
    ins76, addr76 = m276_body()
    st, _, unk = m276_eval(ins76, addr76, 0x557FFD, 0x558038)
    form = st.get("esi")
    fold_ok = form == (STRIDE, 2, 0)
    # ecx freshness: head..chain and nothing between the tail store and the head
    w_head = ecx_writers(addr, 0x557FB8, 0x557FFC)
    # tail: 0x558b1b inc ecx IS the refresh; between the tail jump and loop head
    # there is no code path (back edge only)
    gate(2, fold_ok and not w_head, "fold reused from m276 evaluator: esi = %s (2*region + "
         "8380*arg); unknown-atom writes in chain: %d; ecx redefinitions in [head, chain): "
         "%s -> the tail's `inc ecx` flows through the back edge, region term is LIVE per "
         "iteration" % (form, len(unk), w_head))

    # ---- G3: index domain: ONE init, ONE in-loop store, inc-then-cmp tail
    tail = [addr[a] for a in (0x558B18, 0x558B1B, 0x558B1C, 0x558B22, 0x558B25)]
    tail_ok = tail == [("mov", "ecx,DWORD PTR [ebp-0x10]"), ("inc", "ecx"),
                       ("cmp", "ecx,0x80"), ("mov", "DWORD PTR [ebp-0x10],ecx"),
                       ("jl", "0x557fb8")]
    init = addr[0x557F9E] == ("mov", "DWORD PTR [ebp-0x10],0x1")
    stores = [hex(a) for a in sorted(addr)
              if 0x557FB8 <= a <= 0x558B25 and addr[a] == ("mov", "DWORD PTR [ebp-0x10],ecx")]
    lo, hi = 1, 127
    gate(3, tail_ok and init and stores == ["0x558b22"],
         "loop: init [ebp-0x10]=1 (%s); in-loop stores %s; tail %s -> body domain i in "
         "[%d,%d], scaled byte offset 2*i in [2,%d]"
         % (init, stores, tail, lo, hi, 2 * hi))

    # ---- G4: the spill verdict: max scaled SLOT vs the sibling base
    gap = SIBLING - BASE
    maxslot = 2 * hi + 1          # last byte touched by the WORD at slot 2*i
    sib = addr[0x558459] == ("mov", "cx,WORD PTR [edi+0x94eba8]")
    band_lo, band_hi = gap, gap + 66
    gate(4, sib and maxslot < gap, "sibling verdict array %#x starts +%d B past %#x (%s) = "
         "slot index 128; this loop's last touched byte is +%d (WORD at slot %d) - regions "
         "94..127 land in +%d..%d, the 68 B of row 94..127, NEVER the sibling: M274 G2 claimed "
         "they read the sibling's band %d..%d and the loop is SHORT of it by %d B (its own "
         "printed max 254 < 256) - the landing claim does NOT survive"
         % (SIBLING, gap, BASE, addr[0x558459], maxslot, 2 * hi, 2 * 94, maxslot,
            band_lo, band_hi, gap - 1 - maxslot))

    # ---- G5: live replay (recorded log, no box): scaled offset stays in block 0
    # while the unscaled slot walks the 8380 blocks
    ev = []
    for line in open(LOG, errors="replace"):
        if not line.startswith("M273S SCALED"):
            continue
        d = {k: int(v, 0) for k, v in re.findall(r"(\w+)=(-?\w+)", line)}
        ev.append(d)
    fit = all(d["s18"] == 2 * d["s10"] + STRIDE * d["cp"] for d in ev)
    blk0 = all(2 * d["edi"] < STRIDE and d["s18"] >= STRIDE for d in ev)
    dif = all(2 * d["edi"] != d["s18"] for d in ev)
    gate(5, len(ev) == 7 and fit and blk0 and dif,
         "%d recorded SCALED events: 2*edi (scaled byte offset) in [%d,%d] = block 0 for ALL; "
         "unscaled s18 = 2*s10+8380*cp fit %d/7, s18 values %s = cp blocks %s while cp walks "
         "1..7 -> two different rows in live data too; rival 'scaled carries 8380*cp' refuted "
         "7/7" % (len(ev), 2 * ev[0]["edi"], 2 * max(d["edi"] for d in ev),
                  sum(d["s18"] == 2 * d["s10"] + STRIDE * d["cp"] for d in ev),
                  sorted({d["s18"] for d in ev}), sorted({d["cp"] for d in ev})))

    # ---- G6: image-wide referrer census of +0x94eaa8: 4 sites; the ONLY two
    # writers BOTH evaluate to the block fold (8380, 2, 0) -> per-block live row
    refs = []
    pat = re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s?(.*)")
    with open(TEXT, errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if m and "0x94eaa8" in m.group(4):
                refs.append((int(m.group(1), 16), m.group(3), m.group(4).split("#")[0].strip()))
    # writer 1: FUN_0051dcb0 0x51df26..0x51df3b (atoms: ebx=block, ecx=region idx)
    a1, d1 = load(0x51DF26, 0x51DF3D)
    neuter(d1, [0x51DF28], "ecx load is the atom of origin")
    s1, _ = chain_eval(d1, 0x51DF26, 0x51DF3B, {"ebx": (1, 0, 0), "ecx": (0, 1, 0)})
    w1 = s1.get("eax")
    # writer 2: FUN_0055f650 0x564a9a..0x564aaf (esi=block, ecx=region idx)
    a2, d2 = load(0x564A9A, 0x564AB8)
    neuter(d2, [0x564A9C], "ecx load is the atom of origin")
    s2, _ = chain_eval(d2, 0x564A9A, 0x564AAF, {"esi": (1, 0, 0), "ecx": (0, 1, 0)})
    w2 = s2.get("eax")
    sites = sorted(hex(a) for a, _, _ in refs)
    kinds = {a: op + " " + ar for a, op, ar in refs}
    gate(6, sites == ["0x51df61", "0x558452", "0x5584aa", "0x564ab1"]
         and w1 == (STRIDE, 2, 0) and w2 == (STRIDE, 2, 0),
         "image-wide referrers of +0x94eaa8: %s; writers %#x (%s) and %#x (%s) fold to "
         "eax = %s and %s -> BOTH carry 8380*block + 2*slot: the row is per-faction-block "
         "live data; the auto-manager SCALED read is the image's ONLY referrer with no "
         "block term = the permanent faction-0 (block 0) view"
         % (sites, 0x51df61, kinds[0x51df61], 0x564ab1, kinds[0x564ab1], w1, w2))

    n, tot = sum(res), len(res)
    print("SUMMARY M277: %d/%d gates %s" % (n, tot, "PASS" if n == tot else "FAIL"))
    return 0 if n == tot else 1


if __name__ == "__main__":
    sys.exit(main())
