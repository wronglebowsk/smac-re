#!/usr/bin/env python3
"""M250-M252: who generates the map's region labels, in what order, and who consumes them.

Pick (NEXT_PROMPT, new from M248/M249): who calls the generators FUN_0058d120 / FUN_0058d390
and in what order at NEW GAME (that is where region ids are assigned, and FUN_0058ce00 must run
after them); what the per-faction 0x20bc-byte block at DAT_0094eda8 indexed by region id holds;
what FUN_00556690's coarse-label search is FOR.

Static only: file image + ghidra_out. No box time, no /proc, no gdb.
Acceptance: ONE invocation must print PASS on every gate; a gate that cannot be decided
prints FAIL with its numbers.

Gates:
  G1  image-wide call census of FUN_0058d390 (sites, owning functions)
  G2  call census of FUN_0058d120 and FUN_0058ce00 (sites, owning functions)
  G3  ORDER inside FUN_0058d390: every d120 call pc vs the ce00 call pc, loop membership
  G4  what FUN_0058d120 writes (record +3 via FUN_00582d00) and where its value comes from
  G5  DAT_0094eda8 reference census classified by addressing shape (block field vs region index)
  G6  FUN_00556690's region-map loop: bounds, the label test, and what it accumulates
  G7  the two consumers of FUN_00556690 (callers, arg provenance)
"""
import csv
import re
import struct
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "programs" / "terran.exe"
INDEX = ROOT / "ghidra_out" / "index.csv"
SHARD_DIR = ROOT / "ghidra_out"
TEXT_BASE = 0x400000

FUNCS = []   # (start, end, name) from ghidra_out/index.csv
INSN = re.compile(r'^\s+([0-9a-f]{6,8}):\s+(?:[0-9a-f]{2} )*\s*(\S+)\s+(.*)$')


def load_index():
    with INDEX.open() as f:
        for r in csv.DictReader(f):
            a = int(r['addr'], 16)
            FUNCS.append((a, a + int(r['size_bytes']), r['name']))
    FUNCS.sort()


def fn_of(pc):
    lo, hi = 0, len(FUNCS)
    while lo < hi:
        mid = (lo + hi) // 2
        if FUNCS[mid][0] <= pc:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    if i >= 0 and FUNCS[i][1] > pc:
        return FUNCS[i][2]
    return None


def disasm():
    """Whole-image .text disassembly -> [(pc, mnemonic, operands)] (regenerated, not cached)."""
    out = subprocess.run(['objdump', '-d', '-M', 'intel', '--section=.text', str(EXE)],
                         capture_output=True, text=True).stdout
    ins = []
    for ln in out.replace('\\t', '\t').splitlines():
        m = INSN.match(ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2), m.group(3).strip()))
    return ins


IMM = re.compile(r'0x([0-9a-f]+)')
RMW = ('inc', 'dec', 'add', 'sub', 'and', 'or', 'xor')


def immediates(ops):
    return [int(t, 16) for t in IMM.findall(ops)]


def calls_to(ins, target):
    """All `call <target>` in the whole image -> [(pc, containing function)]."""
    return [(pc, fn_of(pc)) for pc, mn, ops in ins
            if mn == 'call' and immediates(ops)[:1] == [target]]


def body(ins, addr):
    st = next(s for s, e, n in FUNCS if n == addr)
    en = next(e for s, e, n in FUNCS if n == addr)
    return st, en, [(pc, mn, ops) for pc, mn, ops in ins if st <= pc < en]


def backward_edges(bd):
    """(src, target) for every conditional/unconditional jump whose target is BELOW it."""
    edges = []
    for pc, mn, ops in bd:
        if not mn.startswith('j'):
            continue
        t = immediates(ops)
        if len(t) == 1 and t[0] < pc:
            edges.append((pc, t[0]))
    return edges



_INS = None


def ins():
    global _INS
    if _INS is None:
        load_index()
        _INS = disasm()
    return _INS


def g1():
    """FUN_0058d390 (the region generator) — its callers, image-wide."""
    want = [(0x5add8f, 'FUN_005add30'), (0x5af0c7, 'FUN_005af0c0'), (0x5b09e3, 'FUN_005b09b0')]
    got = calls_to(ins(), 0x58d390)
    drv = calls_to(ins(), 0x5b2970)
    return got == want, ("3 sites %s; the driver FUN_005b2970 has %d call site(s) %s"
                         % (got, len(drv), drv))


def g2():
    """FUN_0058d120 / FUN_0058ce00 / the +3 setter FUN_00582d00 — their callers."""
    i = ins()
    a, b, c = calls_to(i, 0x58d120), calls_to(i, 0x58ce00), calls_to(i, 0x582d00)
    ok = (a == [(0x58d47e, 'FUN_0058d390')] and b == [(0x58d88c, 'FUN_0058d390')]
          and [pc for pc, _ in c] == [0x58d171, 0x58d298, 0x58d649, 0x58d6c3]
          and sorted({n for _, n in c}) == ['FUN_0058d120', 'FUN_0058d390'])
    return ok, "d120 %s | ce00 %s | +3 setter %s" % (a, b, c)


def g3():
    """ORDER inside FUN_0058d390: the flood-fill is loop-nested, the coarse builder is last."""
    st, en, bd = body(ins(), 'FUN_0058d390')
    edges = backward_edges(bd)
    calls = [(pc, immediates(ops)[0]) for pc, mn, ops in bd
             if mn == 'call' and immediates(ops)]
    D120, CE00 = 0x58d47e, 0x58d88c
    cover = lambda pc: [(s, t) for s, t in edges if t <= pc <= s]
    gen_loops, ce00_loops = cover(D120), cover(CE00)
    gen_calls = [pc for pc, t in calls if t in (0x58d120, 0x582d00)]
    ok = (len(gen_loops) >= 2 and ce00_loops == [] and calls[-2:] == [(CE00, 0x58ce00),
          (0x58d891, 0x5e9e0d)] and max(gen_calls) < CE00)
    return ok, ("d120 call %#x inside %d back-edge loop(s) %s; ce00 call %#x inside %d; "
                "last two calls %s; max generator call %#x"
                % (D120, len(gen_loops), gen_loops, CE00, len(ce00_loops),
                   [hex(p) + '/' + hex(t) for p, t in calls[-2:]], max(gen_calls)))


def g4():
    """What FUN_0058d390 does before the flood-fill: clear +3, the two id bands, the region table."""
    st, en, bd = body(ins(), 'FUN_0058d390')
    st2, en2, bd2 = body(ins(), 'FUN_0058d120')
    edges = backward_edges(bd)
    store = [pc for pc, mn, ops in bd if mn == 'mov' and ops == 'BYTE PTR [ecx],0x0']
    step = [pc for pc, mn, ops in bd if mn == 'add' and ops == 'ecx,0x2c']
    loop = [(s, t) for s, t in edges if store and t <= store[0] <= s]
    def cnt(bdys, v):
        return len([1 for pc, mn, ops in bdys if v in immediates(ops)])
    folds = len([1 for pc, mn, ops in bd if mn == 'lea' and re.search(r'\*\d*\s*8\+0x0\]$', ops)])
    ok = (store == [0x58d3b8] and len(step) == 3 and len(loop) == 1
          and cnt(bd, 0x3e) == 1 and cnt(bd, 0x7e) == 1 and cnt(bd, 0x3f) == 2
          and cnt(bd, 0x989ce0) == 13 and cnt(bd2, 0x989ce0) == 4 and folds >= 3)
    return ok, ("clear +3 store %s step %s loop %s; band imms 0x3e/0x7e/0x3f = %d/%d/%d; "
                "region-table refs d390 %d d120 %d; x7 folds %d"
                % (store, step, loop, cnt(bd, 0x3e), cnt(bd, 0x7e), cnt(bd, 0x3f),
                   cnt(bd, 0x989ce0), cnt(bd2, 0x989ce0), folds))

def g5():
    """DAT_0094eda8 = the per-faction, per-REGION byte array: who writes it, with what."""
    i = ins()
    refs = [(pc, mn, ops) for pc, mn, ops in i if '94eda8' in ops]
    per_fn, stores, vals = defaultdict(int), [], set()
    for pc, mn, ops in refs:
        fn = fn_of(pc); per_fn[fn] += 1
        dest = ops.split(',')[0] if ',' in ops else ops
        if (mn in ('mov', 'movzx', 'movsx') and '94eda8' in dest) or mn in RMW:
            stores.append((pc, fn, mn, ops))
            vals.update(v for v in immediates(ops) if v != 0x94EDA8)
    writers = defaultdict(int)
    for _, fn, _, _ in stores:
        writers[fn] += 1
    bound = [pc for pc, mn, ops in body(i, 'FUN_00556690')[2]
             if mn == 'cmp' and ops.endswith(',0x80')]
    ok = (len(refs) == 79 and len(stores) == 6 and len(per_fn) == 18
          and dict(writers) == {'FUN_00556690': 5, 'FUN_0055f650': 1}
          and vals == {0, 2, 7, 8} and len(bound) >= 1)
    return ok, ("%d refs in %d functions; %d store sites %s; values written %s; "
                "region-loop bound cmp reg,0x80 at %s"
                % (len(refs), len(per_fn), len(stores),
                   [(hex(p), f, o) for p, f, _, o in stores], sorted(vals),
                   [hex(p) for p in bound]))


def g6():
    """FUN_00556690's coarse-label search: the coarse map is the index, the output is a goal site."""
    st, en, bd = body(ins(), 'FUN_00556690')
    def calls(t):
        return [pc for pc, mn, ops in bd if mn == 'call' and immediates(ops) == [t]]
    acc, goal, cost = calls(0x582340), calls(0x56d350), calls(0x4cc7b0)
    coarse = [pc for pc, mn, ops in bd if '0x92ad9c' in ops or '0x92ada0' in ops]
    p29 = [pc for pc, mn, ops in bd if mn == 'push' and immediates(ops) == [0x29]]
    paired = []
    for pc in p29:
        k = next(n for n, (p, _, _) in enumerate(bd) if p == pc)
        nxt = [(p, immediates(o)) for p, m, o in bd[k + 1:k + 12] if m == 'call']
        paired.append((hex(pc), bool(nxt) and nxt[0][1] == [0x56d350], hex(nxt[0][0]) if nxt else '-'))
    ok = (len(acc) == 2 and len(coarse) == 7 and len(goal) == 7 and len(cost) == 2
          and len(p29) == 2 and all(p[1] for p in paired))
    return ok, ("coarse accessor FUN_00582340 %s; coarse dims 0x92ad9c/0x92ada0 refs %d; "
                "goal requests FUN_0056d350 %d; terraform cost FUN_004cc7b0 %d; push 0x29 %s"
                % ([hex(p) for p in acc], len(coarse), len(goal), len(cost), paired))


def g7():
    """Who runs the stage, and who else reads the coarse region map at all."""
    i = ins()
    s = calls_to(i, 0x556690)
    acc = calls_to(i, 0x582340)
    fns = sorted({n for _, n in acc})
    ok = s == [(0x52094f, 'FUN_005208f0'), (0x59dd43, 'FUN_0059ce10')]
    return ok, ("callers of FUN_00556690: %s; coarse accessor FUN_00582340 called at %d site(s) "
                "in %d function(s): %s" % (s, len(acc), len(fns), fns))



def main():
    gates = []
    for name, fn in [("G1", g1), ("G2", g2), ("G3", g3), ("G4", g4),
                     ("G5", g5), ("G6", g6), ("G7", g7)]:
        try:
            ok, detail = fn()
        except Exception as exc:  # a broken gate is a FAIL, never a crash
            ok, detail = False, "EXC %s: %s" % (type(exc).__name__, exc)
        gates.append((name, ok, detail))
        print("%s %s: %s" % (name, "PASS" if ok else "FAIL", detail))
    n_ok = sum(1 for _, ok, _ in gates if ok)
    print("SUMMARY %s: %d/%d gates on terran.exe (%s)"
          % ("PASS" if n_ok == len(gates) else "FAIL", n_ok, len(gates),
             "static image, no box"))
    return 0 if n_ok == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
