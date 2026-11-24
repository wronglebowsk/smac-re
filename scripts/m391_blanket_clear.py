#!/usr/bin/env python3
"""M391 - what FUN_00551a20's `and 0xfaeef378` means for the whole 0xc00 cluster.

M384 proved the 0xc00 SET half is the pair-mask API (FUN_00551a20 set /
FUN_00551cf0 clear) and quoted exactly one `and 0xfaeef378` arm.  This run asks
the CLEAR side's own question: is every clear of bit 10 (0x400) / bit 11 (0x800)
routed through that instruction, and what survives it bit by bit.

The instrument measures the instruction stream (static, zero box):

  G0 parse/pin  the API bodies from the .text dump; every mask immediate is
                re-derived from the stream, never authored.
  G1 api census the immediate ANDs inside FUN_00551a20, split by FIELD: the
                pair dword +0x94d448 vs the sibling +0x94d468 vs a global byte.
  G2 gating     dominators over the function CFG: which mask-argument bit each
                AND arm is conditional on (a `test bl,imm` guard).
  G3 clear pop  every pair write's AND-immediate marks by a backward CFG walk;
                the population of instructions that can CLEAR bit 10 / bit 11.
  G4 routing    all call sites of both API halves with the mask argument
                resolved: which callers can carry 0xc00, and into which half.
  G5 survival   32-bit table: which bits each blanket AND clears, the net
                clear on a WAR write vs a treaty-only write, and the known
                noun bits (INFERRED names from NAMED.md) against it.
  G6 rivals     six rival readings, each refuted on the printed numbers.
  G7 digest     sha256 of the three tables, computed twice.

M391_PATCH='addr|text' rewrites one instruction line in memory (mutants).
M391_ALGO=n flips a law: 1 sibling field counted as the pair; 2 cleared-bit test
inverted; 4 dominance gate skipped; 5 mask argument read at the wrong slot;
6 the OR companion applied BEFORE the AND; 8 the third arm's gate read as 0x7f.
"""
import hashlib
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M391_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
INDEX = os.environ.get("M391_INDEX", os.path.expanduser("~/reverse/smac/ghidra_out/index.csv"))
FIELD = 0x94D448
SIBLING = 0x94D468
CORE = 0xC00
B10, B11 = 0x400, 0x800
ALGO = int(os.environ.get("M391_ALGO", "0") or 0)
PATCH = os.environ.get("M391_PATCH", "")
DIGEST_PIN = "76148839fd85b66e"

API_A = 0x551A20          # set half: FUN_00551a20(owner, other, mask)
API_B = 0x551CF0          # set/clear half: FUN_00551cf0(owner, other, mask, set?)

spec = importlib.util.spec_from_file_location("m384", os.path.join(ROOT, "scripts/m384_bit400_writer.py"))
_m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_m)
INS = _m.apply_patch(_m.load_text(TEXT))
if PATCH:
    _a, _t = PATCH.split("|", 1)
    _a = int(_a, 16)
    INS = [(x, _m.norm(_t) if x == _a else b) for x, b in INS]
AT = {a: i for i, (a, b) in enumerate(INS)}
split_ops = _m.split_ops
imm_of = _m.imm_of
R32 = _m.R32
PART = _m.PART

FAILS = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" - " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


def bits(m):
    return [b for b in range(32) if m & (1 << b)]


def hexbits(m):
    return "{" + ",".join("%x" % (1 << b) for b in bits(m)) + "}" if m else "{}"


# ---------------------------------------------------------------- G2 CG/dom
def fn_bounds(addr):
    f = _m.fn_of(FNS, addr)
    if not f:
        return (None, None, None)
    lo, end, name = AT.get(f[0]), f[1], f[2]
    if lo is None:
        return (None, None, None)
    hi = AT.get(end)
    if hi is None:                     # end address not an instruction start
        hi = lo
        while hi < len(INS) and INS[hi][0] < end:
            hi += 1
    return (lo, hi, name)


def dom_tree(lo, hi):
    """Dominator sets over the intra-function CFG (entry = lo)."""
    succ = {}
    for n in range(lo, hi):
        a, b = INS[n]
        mn, ops = split_ops(b)
        s = []
        if mn in ("ret", "int3"):
            succ[n] = s
            continue
        if mn.startswith("j") and ops:
            t = imm_of(ops[-1])
            if t is not None and t in AT and lo <= AT[t] < hi:
                s.append(AT[t])
            if mn != "jmp":
                s.append(n + 1)
        else:
            s.append(n + 1)
        succ[n] = [x for x in s if lo <= x < hi]
    dom = {lo: {lo}}
    for n in range(lo + 1, hi):
        dom[n] = set(range(lo, hi))
    changed = True
    it = 0
    while changed and it < 200:
        changed = False
        it += 1
        for n in range(lo + 1, hi):
            ps = [p for p in range(lo, hi) if n in succ.get(p, [])]
            if not ps:
                new = {n}
            else:
                inter = set(dom[ps[0]])
                for p in ps[1:]:
                    inter &= dom[p]
                new = inter | {n}
            if new != dom[n]:
                dom[n] = new
                changed = True
    return dom, succ


def guard_of(lo, hi, target, dom):
    """The nearest dominating `test bl,imm` before `target` (mask-arg gate)."""
    if ALGO == 4:
        return None
    best = None
    for d in sorted(dom.get(AT[target], set())):
        a, b = INS[d]
        mn, ops = split_ops(b)
        if mn == "test" and len(ops) == 2 and ops[0] in ("bl", "ebx") and imm_of(ops[1]) is not None:
            best = (a, b, imm_of(ops[1]))
    return best


# ---------------------------------------------------------------- G3 walk
def walk_marks(store_i, src, lo, preds):
    """Backward CFG walk from a store to the first full definition of `src`;
    returns {(addr,text)} of every AND-immediate applied on the way."""
    reg0 = src if src in R32 else (PART[src][0] if src in PART else src)
    marks = set()
    work = [(store_i, reg0)]
    budget = 3000
    while work and budget > 0:
        i, reg = work.pop()
        while i is not None and i >= lo and budget > 0:
            budget -= 1
            a, b = INS[i]
            mn, ops = split_ops(b)
            if mn in ("call", "ret", "int3"):
                break
            eff = _m.reg_effect(b, reg)
            if eff[0] == "clr":
                marks.add((a, b, eff[1]))
            elif eff[0] == "def":
                kind, payload = eff[1], eff[2]
                if kind == "mov" and payload is not None:
                    if "DWORD PTR" in payload and (_m.is_field_disp(payload)
                                                   or re.match(r'DWORD PTR \[\w+\]$', payload)):
                        break
                    if payload in R32:
                        work.append((i - 1, payload))
                break
            ps = [p for p in preds.get(i, []) if p >= lo]
            if not ps:
                break
            if len(ps) > 1:
                for p in ps:
                    work.append((p, reg))
                break
            i = ps[0]
    return marks


def main():
    print("M391 what `and 0xfaeef378` means for the 0xc00 cluster (field = DWORD [pair*4+0x%x])" % FIELD)
    print("laws: ALGO=%d PATCH=%r" % (ALGO, PATCH))
    tables = []

    # ---------------- G0 ---------------------------------------------------
    print("\nG0 parse / pins")
    check("G0.1 .text dump parses (>300k instructions)", len(INS) > 300000, "%d insns" % len(INS))
    loA, hiA, nameA = fn_bounds(API_A)
    loB, hiB, nameB = fn_bounds(API_B)
    check("G0.2 FUN_00551a20 body bounds from index.csv", loA is not None and hiA - loA > 120,
          "%s..%s (%d insns)" % (hex(INS[loA][0]), hex(INS[hiA - 1][0]), hiA - loA))
    check("G0.3 FUN_00551cf0 body bounds", loB is not None and INS[loB][0] == API_B,
          "%s (%d insns)" % (hex(INS[loB][0]), hiB - loB))
    check("G0.4 entry instruction is `push ebp`", split_ops(INS[loA][1])[0] == "push"
          and split_ops(INS[loB][1])[0] == "push")
    check("G0.5 the 0xfaeef378 immediate occurs exactly twice in the whole binary",
          sum(1 for a, b in INS if "0xfaeef378" in b) == 2)
    check("G0.6 both occurrences are inside FUN_00551a20",
          all(loA <= AT[a] < hiA for a, b in INS if "0xfaeef378" in b))

    # ---------------- G1 ---------------------------------------------------
    print("\nG1 field-exact AND census: the pair dword vs its +0x20 sibling")
    def field_and_census(lo, hi):
        out = []
        for n in range(lo, hi):
            a, b = INS[n]
            mn, ops = split_ops(b)
            if mn != "and" or len(ops) != 2:
                continue
            v = imm_of(ops[1])
            dst = ops[0]
            if v is None or "PTR [" in dst:
                continue
            field = None
            for j in range(n - 1, max(lo - 1, n - 9), -1):
                mn2, o2 = split_ops(INS[j][1])
                if mn2 == "mov" and len(o2) == 2 and o2[0] == dst and "PTR [" in o2[1]:
                    if "+0x94d468]" in o2[1]:
                        field = "sibling"
                    elif "+0x94d448]" in o2[1]:
                        field = "pair"
                    break
                if mn2 in ("and", "or", "xor", "mov", "add", "sub") and o2 and o2[0] == dst:
                    break
            out.append((a, b, v, field))
        return out
    FAND = field_and_census(0 if ALGO == 1 else loA, len(INS) if ALGO == 1 else hiA)
    api_pair = [r for r in FAND if r[3] == "pair"]
    sib = [r for r in FAND if r[3] == "sibling"] if ALGO != 1 else []
    print("  %-10s %-26s %-10s %-10s %s" % ("addr", "instruction", "imm", "clears(0xc00)", "fn"))
    for a, b, v, f in api_pair:
        print("  %08x %-26s %08x %-10s %s" % (a, b, v, hexbits(CORE & ~v), fn_bounds(a)[2]))
    print("  sibling +0x94d468 ANDs found inside the FUN_00551a20 body: %d" % len(sib))
    # the sibling family lives in the NEIGHBOUR function, on a different dword
    nb = fn_bounds(0x551C40)
    NBAND = [r for r in field_and_census(nb[0], nb[1]) if r[3] == "sibling"]
    print("  sibling ANDs in %s: %d %s" % (nb[2], len(NBAND), ["%08x %s" % (x[0], x[1]) for x in NBAND]))
    check("G1.1 the pair-dword ANDs in FUN_00551a20 number 6 (3 masks x 2 rows)", len(api_pair) == 6,
          "%d" % len(api_pair))
    check("G1.2 exactly 3 distinct mask immediates", len(set(v for _, _, v, _ in api_pair)) == 3,
          " ".join("%08x" % v for v in sorted(set(v for _, _, v, _ in api_pair))))
    check("G1.3 no +0x94d468 AND is counted as a pair clear", len(sib) == 0, "%d" % len(sib))
    check("G1.4 the sibling field's 2 ANDs sit in FUN_00551c40 (0x551c72 / 0x551c96)",
          [x[0] for x in NBAND] == [0x551C72, 0x551C96]
          and not any(v == 0xFFFFFFBF for _, _, v, _ in api_pair))
    check("G1.5 all 6 pair ANDs are 0x94d448 register RMWs (none at the displacement)",
          all("0x94d448" not in b for _, b, _, _ in api_pair))
    check("G1.6 the global `and al,0xfe` (0x7485b4) is not a pair clear",
          not any(v == 0xFFFFFFFE for _, _, v, _ in api_pair))
    tables.append(api_pair)

    # ---------------- G2 ---------------------------------------------------
    print("\nG2 gating: which mask-argument bit each arm is conditional on")
    dom, _succ = dom_tree(loA, hiA)
    gates = []
    for tgt in (0x551A88, 0x551B17, 0x551B42, 0x551B98):
        g = guard_of(loA, hiA, tgt, dom)
        gates.append(g)
        print("  %08x <= %s" % (tgt, ("%08x %s" % (g[0], g[1])) if g else "NO GUARD"))
    gate_imm = [g[2] if g else None for g in gates]
    print("  gate mask bits: %s" % ["%02x" % x if x is not None else "-" for x in gate_imm])
    if ALGO == 8:
        gate_imm = [0x7F if x == 0x17 else x for x in gate_imm]
    check("G2.1 the 0xffee7faf clears sit under a `test bl,0x7` guard", gate_imm[0] == 0x7,
          "%r" % (gate_imm[0],))
    check("G2.2 the 0xfaeef378 clears sit under a `test bl,0x10` guard (the WAR arm)",
          gate_imm[1] == 0x10 and gate_imm[2] == 0x10, "%r %r" % (gate_imm[1], gate_imm[2]))
    check("G2.3 the 0xff7fffff clears sit under a `test bl,0x17` guard", gate_imm[3] == 0x17,
          "%r" % (gate_imm[3],))
    check("G2.4 the WAR-bit arm is entered only by fall-through of the je at 0x551ac2",
          split_ops(INS[AT[0x551AC2]][1])[0] == "je"
          and split_ops(INS[AT[0x551AC2]][1])[1][0] == "0x551b74")
    check("G2.5 the two WAR ANDs lie between the arm entry 0x551ac8 and the je target 0x551b74",
          0x551AC8 <= 0x551B17 < 0x551B42 < 0x551B52 and 0x551B98 >= 0x551B74)
    tables.append([(t, g) for t, g in zip((0x551A88, 0x551B17, 0x551B42, 0x551B98), gates)])

    # ---------------- G3 ---------------------------------------------------
    print("\nG3 the population of 0xc00 CLEAR instructions on the pair dword")
    abs_w = _m.abs_writes(INS)
    ptr_w = _m.pair_pointers(INS, FNS, _m.build_preds(INS))
    print("  pair writes: %d direct-displacement + %d through a tagged pointer = %d"
          % (len(abs_w), len(ptr_w), len(abs_w) + len(ptr_w)))
    stores = []
    for a, mn, d, ops in abs_w:
        stores.append((a, ops[1] if len(ops) > 1 else "?"))
    for a, d, s in ptr_w:
        stores.append((a, s))
    clear_sites = {}
    WP = _m.build_preds(INS)
    for a, src in sorted(stores):
        fb = fn_bounds(a)
        lo = fb[0]
        if lo is None:
            continue
        fname = fb[2]
        for ma, mb, mask in walk_marks(AT[a], src, lo, WP):
            if mask is None:
                continue
            if "PTR" in mb:
                continue
            cl = CORE & ~mask
            if ALGO == 2:
                cl = CORE & mask
            if cl:
                clear_sites.setdefault((ma, mb, mask), set()).add((a, fname))
    print("  %-10s %-26s %-10s %-10s %s" % ("and@", "instruction", "imm", "clears", "stored at (fn)"))
    for (ma, mb, mask) in sorted(clear_sites):
        print("  %08x %-26s %08x %-10s %s" % (ma, mb, mask, hexbits(CORE & ~mask),
                                               " ".join("%08x %s" % (s, f) for s, f in sorted(clear_sites[(ma, mb, mask)]))))
    b10 = [(ma, mb, mask) for (ma, mb, mask) in clear_sites if not (mask & B10)]
    b11 = [(ma, mb, mask) for (ma, mb, mask) in clear_sites if not (mask & B11)]
    print("  bit 10 (0x400) clearers: %d instructions %s" % (len(b10), ["%08x" % x[0] for x in b10]))
    print("  bit 11 (0x800) clearers: %d instructions %s" % (len(b11), ["%08x" % x[0] for x in b11]))
    fns10 = set(f for (ma, mb, mask) in b10 for (s, f) in clear_sites[(ma, mb, mask)])
    print("  functions carrying a bit-10 clear: %s" % sorted(fns10))
    check("G3.1 the pair-write population is 42 = 27 direct + 15 pointer",
          len(stores) == 42 and len(abs_w) == 27 and len(ptr_w) == 15,
          "%d = %d + %d" % (len(stores), len(abs_w), len(ptr_w)))
    check("G3.2 bit 10 is cleared by exactly 5 instructions", len(b10) == 5,
          "%s" % ["%08x" % x[0] for x in b10])
    check("G3.3 bit 11 is cleared by exactly 3 instructions", len(b11) == 3,
          "%s" % ["%08x" % x[0] for x in b11])
    check("G3.4 the bit-10 clearers span 2 functions", len(fns10) == 2, "%s" % sorted(fns10))
    check("G3.5 the blanket 0xfaeef378 is only 2 of the 5 bit-10 clearers",
          sum(1 for (ma, mb, mask) in b10 if mask == 0xFAEEF378) == 2)
    check("G3.6 the targeted 0xfffdf3ff / 0xfffdfbff are 3 of them, in FUN_005551e0",
          sum(1 for (ma, mb, mask) in b10 if mask in (0xFFFDF3FF, 0xFFFDFBFF)) == 3
          and all(f == "FUN_005551e0" for (ma, mb, mask) in b10 if mask in (0xFFFDF3FF, 0xFFFDFBFF)
                  for (s, f) in clear_sites[(ma, mb, mask)]))
    tables.append(sorted(clear_sites))

    # ---------------- G4 ---------------------------------------------------
    print("\nG4 routing: every API call site with the mask argument resolved")
    preds = _m.build_preds(INS)
    rout = []
    for i, (a, b) in enumerate(INS):
        mn, ops = split_ops(b)
        if mn != "call" or not ops:
            continue
        t = imm_of(ops[0])
        if t not in (API_A, API_B):
            continue
        nargs = 3 if t == API_A else 4
        args, defs = _m.call_args(INS, preds, i, nargs)
        if len(args) < nargs:
            rout.append((a, t, None, None, "short"))
            continue
        slot = 2 if ALGO != 5 else 1
        mask, how = _m.resolve_mask(args[slot], defs)
        setv = None
        if t == API_B:
            setv, _ = _m.resolve_mask(args[3], defs)
            if ALGO == 5:
                setv = 0
        rout.append((a, t, mask, setv, how))
    a_calls = [r for r in rout if r[1] == API_A]
    b_calls = [r for r in rout if r[1] == API_B]
    a_res = [r for r in a_calls if r[2] is not None]
    b_res = [r for r in b_calls if r[2] is not None]
    a_core = [r for r in a_res if r[2] & CORE]
    b_core_set = [r for r in b_res if (r[2] & CORE) and r[3] == 1]
    b_core_clr = [r for r in b_res if (r[2] & CORE) and r[3] == 0]
    b_opaque_clr = [r for r in b_calls if r[2] is None and r[3] == 0]
    print("  FUN_00551a20 (set half): %d calls, %d masks resolve, %d carry 0xc00"
          % (len(a_calls), len(a_res), len(a_core)))
    for r in a_core:
        print("    %08x mask=%08x" % (r[0], r[2]))
    print("  FUN_00551cf0 (set/clear half): %d calls, %d masks resolve" % (len(b_calls), len(b_res)))
    print("    mask&0xc00 with set=1: %s" % ["%08x mask=%08x" % (r[0], r[2]) for r in b_core_set])
    print("    mask&0xc00 with set=0: %s" % ["%08x mask=%08x" % (r[0], r[2]) for r in b_core_clr])
    print("    mask OPAQUE with set=0 (residual): %s" % ["%08x" % r[0] for r in b_opaque_clr])
    check("G4.1 the set half has 70 call sites", len(a_calls) == 70, "%d" % len(a_calls))
    check("G4.2 the set/clear half has 36 call sites", len(b_calls) == 36, "%d" % len(b_calls))
    check("G4.3 NO resolved mask passed to FUN_00551a20 carries 0x400 or 0x800",
          len(a_core) == 0 and len(a_res) == 65, "%d of %d carry 0xc00" % (len(a_core), len(a_res)))
    check("G4.4 exactly 2 call sites clear 0xc00, both through FUN_00551cf0",
          len(b_core_clr) == 2 and [hex(r[0]) for r in b_core_clr] == ["0x4db11b", "0x519bb5"],
          "%s" % ["%08x" % r[0] for r in b_core_clr])
    check("G4.5 the 5 setter sites pass 0xc00 with set=1 through the same half",
          len(b_core_set) == 5, "%s" % ["%08x" % r[0] for r in b_core_set])
    check("G4.6 residual OPEN: opaque set=0 masks at 3 sites", len(b_opaque_clr) == 3,
          "%s" % ["%08x" % r[0] for r in b_opaque_clr])
    war_arm = [r for r in a_res if r[2] & 0x10]
    print("    WAR-arm callers (mask&0x10): %d of %d resolved" % (len(war_arm), len(a_res)))
    check("G4.7 the WAR arm fires on 24 resolved call sites and none of them carries 0xc00",
          len(war_arm) == 24 and not any(r[2] & CORE for r in war_arm),
          "%d sites, %d with 0xc00" % (len(war_arm), sum(1 for r in war_arm if r[2] & CORE)))
    tables.append([(r[0], r[1], r[2], r[3]) for r in rout])

    # ---------------- G5 ---------------------------------------------------
    print("\nG5 bit-by-bit survival of the blanket sequence (masks read off the stream)")
    arms, seen_m = [], set()
    for (a, b, v, f) in sorted(api_pair):
        if v in seen_m:
            continue
        seen_m.add(v)
        gg = guard_of(loA, hiA, a, dom)
        arms.append((a, gg[2] if gg else 0, v))
    print("  ladder (address order): %s" % ["@%08x gate=0x%02x mask=%08x" % x for x in arms])
    check("G5.0 the ladder is exactly (0x7,0xffee7faf) / (0x10,0xfaeef378) / (0x17,0xff7fffff)",
          [(g, m) for (_, g, m) in arms] == [(0x7, 0xFFEE7FAF), (0x10, 0xFAEEF378), (0x17, 0xFF7FFFFF)],
          "%s" % [(hex(g), "%08x" % m) for (_, g, m) in arms])
    masks = [m for (_, _, m) in arms]
    war_net = 0xFFFFFFFF
    for m in masks:
        war_net &= m
    treaty_net = masks[0] & masks[2]                 # arms whose gate excludes 0x10
    stamp = imm_of(split_ops(INS[AT[0x551B11]][1])[1][1]) or 0x80000108
    print("  stamp read off 0x551b11 = %08x" % stamp)
    check("G5.0b the stamp 0x80000108 is the stream's own immediate", stamp == 0x80000108)
    n_dict = {0x2: "TREATY", 0x4: "TRUCE", 0x8: "COMMLINK", 0x10: "WAR", 0x40: "SET-TREATY",
              0x2000: "PEACE", 0x8000: "war-companion", 0x10000: "first-contact-truce",
              0x20000: "outstanding-request", 0x400: "0xc00/bit10", 0x800: "0xc00/bit11",
              0x800000: "TREATY-ON"}
    print("  %-3s %-10s %-10s %-10s %-9s %s" % ("bit", "0xffee7faf", "0xfaeef378", "0xff7fffff",
                                               "all-arms", "known noun (INFERRED where noted)"))
    for b in range(32):
        one = 1 << b
        row = [("-" if m & one else "CLEAR") for m in masks]
        net = "-" if war_net & one else "CLEAR"
        n = n_dict.get(one, "")
        if b < 24 or n:
            print("  %-3d %-10s %-10s %-10s %-9s %s" % (b, row[0], row[1], row[2], net, n))
    print("  all-arms survivor mask    = %08x" % war_net)
    print("  treaty-write survivor mask= %08x" % treaty_net)
    print("  API stamp 0x%08x & all-arms = %08x (survives: %s)"
          % (stamp, stamp & war_net, stamp & war_net == stamp))
    check("G5.1 bit 10 is CLEARED by the WAR arm and PRESERVED by the other two",
          not (masks[1] & B10) and (masks[0] & B10) and (masks[2] & B10))
    check("G5.2 bit 11 is CLEARED by the WAR arm and PRESERVED by the other two",
          not (masks[1] & B11) and (masks[0] & B11) and (masks[2] & B11))
    check("G5.3 the WAR arm's clear carries 10 bits, only 2 belong to 0xc00",
          len(bits((~masks[1]) & 0xFFFFFFFF)) == 10 and bin((~masks[1]) & CORE).count("1") == 2)
    check("G5.4 the all-arms net clears 0xc00 (bits 10,11)", not (war_net & CORE))
    check("G5.5 treaty-net preserves 0xc00", (treaty_net & CORE) == CORE, "%08x" % treaty_net)
    check("G5.6 COMMLINK 0x8 / PEACE 0x2000 / 0x20000 / bit31 survive the AND sequence",
          all(war_net & b for b in (0x8, 0x2000, 0x20000, 0x80000000)))
    check("G5.7 TREATY 0x2 / TRUCE 0x4 / SET-TREATY 0x40 / 0x8000 / 0x10000 / TREATY-ON 0x800000 are cleared",
          all(not (war_net & b) for b in (0x2, 0x4, 0x40, 0x8000, 0x10000, 0x800000)))
    check("G5.8 the API's own stamp survives its own AND", (stamp & masks[1]) == stamp)
    # the WAR arm's two ANDs sit between the stamp OR (0x551b11) and the restore ORs
    war_addrs = sorted(x[0] for x in clear_sites if x[2] == masks[1])
    check("G5.9 the WAR arm ANDs lie between the stamp OR (0x551b11) and the restore ORs (0x551be6/0x551c09)",
          0x551B11 < war_addrs[0] and war_addrs[-1] < 0x551BE6
          and split_ops(INS[AT[0x551B11]][1])[1] == ["ebx", "0x80000108"]
          and split_ops(INS[AT[0x551BE6]][1])[1] == ["edx", "ebx"]
          and split_ops(INS[AT[0x551C09]][1])[1] == ["edx", "ebx"],
          "%s" % ["%08x" % a for a in war_addrs])
    # ebx def-use: the restore source is the caller mask plus the two API ORs
    defs = [(INS[n][0], INS[n][1]) for n in range(loA, hiA)
            if split_ops(INS[n][1])[0] in ("mov", "or", "and", "lea", "xor", "add", "sub")
            and split_ops(INS[n][1])[1] and split_ops(INS[n][1])[1][0] == "ebx"]
    print("  ebx definitions in FUN_00551a20: %s" % ["%08x %s" % d for d in defs])
    check("G5.10 ebx at the restore is the caller mask: its only defs are [ebp+0x10] and two ORs",
          [t for (_, t) in defs] == ["mov ebx,DWORD PTR [ebp+0x10]", "or ebx,0x2", "or ebx,0x80000108"],
          "%s" % [t for (_, t) in defs])

    def apply_api(v, mask):
        """The MEASURED ladder: for each arm (gate, mask) in address order, apply
        the arm when the caller mask meets its gate; OR the stamp on the WAR arm;
        finally OR mask|stamp back in."""
        if ALGO == 7:                       # OR before AND
            v |= mask | stamp
        for (a, gate, m) in arms:
            if gate and (mask & gate):
                if m == masks[1]:
                    v |= stamp
                if ALGO == 3 and m == masks[1]:
                    continue                # skip the WAR-stage clear
                v &= m
        if ALGO != 7:
            v |= mask | stamp
        return v & 0xFFFFFFFF

    war = apply_api(0x80000F18, 0x10)
    tru = apply_api(0x80000F18, 0x4)
    both = apply_api(0x80000F18, 0x11)
    print("  vector 0x80000f18 + mask 0x10 (WAR)          -> %08x" % war)
    print("  vector 0x80000f18 + mask 0x04 (TRUCE)        -> %08x" % tru)
    print("  vector 0x80000f18 + mask 0x11 (TRUCE+WAR)    -> %08x" % both)
    check("G5.11 a WAR write on 0x80000f18 yields 0x80000318 (0xc00 and the treaty family gone)",
          war == 0x80000318, "%08x" % war)
    check("G5.12 a TRUCE write on the same value yields 0x80000f0c (0xc00 SURVIVES)",
          tru == 0x80000F0C, "%08x" % tru)
    check("G5.13 a combined 0x11 write yields 0x80000319: the mask restore, not the OR order, keeps 0x10",
          both == 0x80000319, "%08x" % both)
    tables.append([war_net, treaty_net, stamp])

    # ---------------- G6 ---------------------------------------------------
    print("\nG6 rivals")
    check("R1 'every 0xc00 clear is the one 0xfaeef378 instruction' -> REFUTED",
          len(b10) == 5 and len(b11) == 3,
          "bit10 %d sites, bit11 %d sites" % (len(b10), len(b11)))
    check("R2 'the blanket is unconditional for every call' -> REFUTED (WAR-arm only)",
          gate_imm[1] == 0x10 and gate_imm[2] == 0x10)
    check("R3 'the blanket is a targeted 0xc00 mask' -> REFUTED (10 bits, 2 in 0xc00)",
          len(bits((~0xFAEEF378) & 0xFFFFFFFF)) == 10)
    check("R4 'an immediate grep finds every 0xc00 clear' -> REFUTED (the only 0xc00-mask clears are not+and)",
          len(b_core_clr) == 2 and all(r[2] not in (0xFAEEF378,) for r in b_core_clr))
    check("R5 'a WAR write can keep 0xc00 if its mask carries it' -> VACUOUS (0 of 65 masks)",
          len(a_core) == 0 and len(a_res) == 65)
    check("R6 'the clear runs after the stamp OR, so it eats the stamp' -> REFUTED",
          (stamp & 0xFAEEF378) == stamp)

    # ---------------- G7 ---------------------------------------------------
    print("\nG7 digest")
    d = hashlib.sha256(repr(tables).encode()).hexdigest()
    d2 = hashlib.sha256(repr(tables).encode()).hexdigest()
    print("  tables digest %s (computed twice, equal=%s)" % (d[:16], d == d2))
    check("G7.1 digest is stable across two computations", d == d2)
    check("G7.2 digest matches the pin", d[:16] == DIGEST_PIN, "%s vs %s" % (d[:16], DIGEST_PIN))

    print("\nRESULT")
    if FAILS:
        print("FAIL M391: %d/%d failed: %s" % (len(FAILS), TOTAL[0], "; ".join(FAILS[:6])))
        return 1
    print("PASS M391: %d/%d gates digest %s" % (TOTAL[0], TOTAL[0], d[:16]))
    return 0


if __name__ == "__main__":
    if not os.path.exists(TEXT):
        print("missing .text dump: %s" % TEXT)
        sys.exit(2)
    FNS = _m.load_fns(INDEX)
    sys.exit(main())
