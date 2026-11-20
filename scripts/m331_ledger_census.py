#!/usr/bin/env python3
"""M331 (chain2 s10): block+0x2fc / +0x308 census — the upkeep LEDGER SIBLINGS.

STATIC, zero box. Reuses M326's reviewed resolver (import m326_block224_census,
subreg-aware affine backward evaluator + lea-seed scan), retargeted per offset.
M330's import-patch pattern: M331_PATCH env applies instruction patches to
m326.INS AFTER import; every patched site is LITERAL-read by an exact-address
pin below (review_lint L2b, M328 lesson).

Footing: NAMED ## M330/M326/M325/M324/M311. Upkeep entry 520540 zeroes
+3f8/+2fc/+300/+308. Ledger @52081a-841: +310 := +2fc; +30c := +308-+300++2fc.
Findings pinned here:
  +2fc feeder = 4eacd9 (FUN_004eaa10, phase gate ds:8f0d64==1): per owned base
    += clamp(base_rec+0xd4, 0, 99999); base_rec+0xd4 = +0xc4-+0xf4-4e9880(...).
    Plus upkeep-tail +1 per owned base (52080c) in the no-interest fallback.
  +308 feeder = 4f5cb0 (FUN_004f5a70, per owned base): += sum of 8f0d40[k-1]
    over factions k!=owner gated by block+0xc0==0 (self and k).
  Cap hook: 546800 gates on MIN(ENERGY/2, 100*(+2fc-+300)) >= 50;
    535c60 sums MIN(+2fc-+300, block+0x1058) over two faction folds.

Acceptance: python3 -u scripts/m331_ledger_census.py -> table FIRST, then
gates, digest; re-run must be byte-identical. Mutants: scripts/m331_mutate.py.
"""
import hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326

BLKBASE, STRIDE, NBLK = 0x94d430, 0x20bc, 8
OFF2FC, OFF308 = 0x2fc, 0x308

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

def imm(a):
    mn, o = ins(a)
    if mn != "mov": return None
    parts = m326.split_ops(o)
    if len(parts) != 2 or not m326.reg_of(parts[0]): return None
    m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
    return int(m.group(1), 16) if m else None

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
            prov = ("STRIDE", None)     # mutant: trust every disp hit
        else:
            prov = m326.base_tag(a, mi)
        if prov[0] in ("BLKCONST", "STRIDE", "ABS"):
            field.append((h, prov))
        else:
            nonfield.append((h, prov))
    return field, nonfield, seeds, accesses

WRITE_MN = m326.STORE_MN | {"lea", "movsx", "movzx", "shl", "shr", "sar",
                            "rol", "ror", "rcl", "rcr", "imul", "mul", "div",
                            "idiv", "cdq", "cqo", "stos", "stosd", "lods",
                            "lodsb", "lodsw", "lodsd", "movs", "movsb",
                            "movsw", "movsd"}
# review #345 P1-5: implicit destination writes (mul/imul/div/idiv/cdq hit
# edx:eax; stos/movs advance edi; movs also esi; lods writes al/ax/eax;
# xchg/xadd write BOTH operands; cmpxchg also writes eax on failure).
IMPLICIT_AX_DX = {"mul", "imul", "div", "idiv", "cdq", "cqo"}
def reg_defs(lo, hi, regs):
    out = []
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, o = ins(a)
        if mn not in WRITE_MN: continue
        parts = m326.split_ops(o)
        hit = False
        if parts and m326.reg_of(parts[0]) in regs:
            hit = True
        if mn in ("xchg", "xadd") and len(parts) > 1 \
                and m326.reg_of(parts[1]) in regs:
            hit = True
        if mn == "cmpxchg" and "eax" in regs:
            hit = True
        if mn in IMPLICIT_AX_DX and regs & {"eax", "ax", "al", "ah",
                                            "edx", "dx", "dl", "dh"}:
            hit = True
        if mn in ("stos", "stosd", "movs", "movsb", "movsw", "movsd") \
                and regs & {"edi", "di"}:
            hit = True
        if mn in ("movs", "movsb", "movsw", "movsd") and regs & {"esi", "si"}:
            hit = True
        if mn in ("lods", "lodsb", "lodsw", "lodsd") \
                and regs & {"eax", "ax", "al"}:
            hit = True
        if hit:
            out.append(a)
    return out

def stores_to_ebp_slot(lo, hi, slot):
    # review #345 P1-3: ALL store mnemonics, not just mov (add/sub/xor/... to
    # the slot would invalidate a sole-def/last-overwrite law)
    out = []
    pat = re.compile(r"(BYTE|WORD|DWORD) PTR \[ebp%s\]" % re.escape(slot))
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, o = ins(a)
        if mn in m326.STORE_MN and pat.match(o):
            out.append(a)
    return out

def block_stores(lo, hi):
    """ANY store-mnemonic write to [esi+0x94dXXX] in [lo,hi): (addr, disp).
    review #345 P2-4: add/sub/or/... count too, not just mov."""
    out = []
    pat = re.compile(r"(BYTE|WORD|DWORD) PTR \[esi\+0x(94d[0-9a-f]+)\]")
    for a in m326.ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, o = ins(a)
        if mn in m326.STORE_MN:
            m = pat.match(o)
            if m: out.append((a, int(m.group(2), 16)))
    return out

# ---------------- G1/G2: census shape + provenance ----------------
W2FC = [0x520567, 0x52080c, 0x59f264]
R2FC = [0x4eacc9, 0x520805, 0x52081a, 0x520832, 0x5233ed, 0x532876, 0x5362d5]
NF2FC = [0x449377, 0x523dad, 0x5328c5, 0x5362ef, 0x542972, 0x544bae, 0x544eac,
         0x54b361, 0x54d43b, 0x554ee6, 0x5792d9, 0x5792ef, 0x579309]
W308 = [0x520573, 0x59f29e]
R308 = [0x45b23f, 0x520826]
NF308 = [0x40ed72, 0x4f5cb0, 0x596c06]

def g12_census():
    f2, n2, s2, a2 = census_at(OFF2FC)
    f3, n3, s3, a3 = census_at(OFF308)
    for off, f, n, s, a in ((OFF2FC, f2, n2, s2, a2), (OFF308, f3, n3, s3, a3)):
        W = sorted(h[0][0] for h in f if h[0][1])
        R = sorted(h[0][0] for h in f if h[0][2] and not h[0][1])
        provs = {}
        for h, p in f:
            provs[p[0]] = provs.get(p[0], 0) + 1
        row("G%d census %x: rawhits=%d FIELD=%d (W=%d R=%d) nonfield=%d seeds=%d "
            "seedacc=%d prov=%s" % (1 if off == OFF2FC else 2, off,
            len(f) + len(n), len(f), len(W), len(R), len(n), len(s), len(a),
            sorted(provs.items())))
        for (aa, w, r, width, tag, mi, src), p in f:
            row("  hit %06x %s%s w=%d tag=%s prov=%s src=%s owner=%s"
                % (aa, "W" if w else "-", "R" if r else "-", width, tag, p[0],
                   src, m326.owner(aa)))
        for (aa, w, r, width, tag, mi, src), p in n:
            row("  NONFIELD %06x %s%s tag=%s prov=%s owner=%s"
                % (aa, "W" if w else "-", "R" if r else "-", tag, p, m326.owner(aa)))
        for aa, dest, tgt in s:
            if tgt[0] == off:
                row("  seed %06x ->%s tgt=%s" % (aa, dest, tgt))
        for aa, dest, b, w, width, d, ea, ho, src, stag in a:
            if ho == off:
                row("  seedacc %06x %s[%+d]=%06x w=%d insn=%s"
                    % (aa, dest, d, ea, w, ins(b)))
    ok2 = (len(f2) + len(n2) == 23 and len(f2) == 10 and len(n2) == 13
           and sorted(h[0][0] for h in f2 if h[0][1]) == W2FC
           and sorted(h[0][0] for h in f2 if h[0][2] and not h[0][1]) == R2FC
           and sorted(h[0][0] for h in n2) == NF2FC
           and all(p[0] == "STRIDE" for h, p in f2)
           and [(aa, t[2]) for aa, d, t in s2 if t[0] == OFF2FC]
               == [(0x4eacd0, "STRIDE")]
           and [(aa, b, w) for aa, d, b, w, wd, dd, ea, ho, s, st in a2
                if ho == OFF2FC] == [(0x4eacd0, 0x4eacd9, 1)])
    gate("G1", ok2, "+2fc: rawhits=23 FIELD=10 (3W/7R, 10/10 STRIDE) nonfield=13; "
         "1 lea-seed 4eacd0 (STRIDE) + 1 seedacc WRITE @4eacd9 (the feeder)")
    ok3 = (len(f3) + len(n3) == 7 and len(f3) == 4 and len(n3) == 3
           and sorted(h[0][0] for h in f3 if h[0][1]) == W308
           and sorted(h[0][0] for h in f3 if h[0][2] and not h[0][1]) == R308
           and sorted(h[0][0] for h in n3) == NF308
           and all(p[0] == "STRIDE" for h, p in f3)
           and [t for aa, d, t in s3 if t[0] == OFF308] == []
           and [x for x in a3 if x[7] == OFF308] == [])
    gate("G2", ok3, "+308: rawhits=7 FIELD=4 (2W/2R, 4/4 STRIDE) nonfield=3; "
         "0 seeds/seedacc; feeder 4f5cb0 is arg-fed (resolved in G6)")
    return f2, f3

# ---------------- G3: writer/reader role pins (literal reads) ----------------
P_ROLES = {
    0x520567: ("mov", "DWORD PTR [esi+0x94d72c],eax"),
    0x52080c: ("mov", "DWORD PTR [esi+0x94d72c],edx"),
    0x59f264: ("mov", "DWORD PTR [ebx+0x94d72c],edx"),
    0x4eacc9: ("mov", "esi,DWORD PTR [ecx*4+0x94d72c]"),
    0x520805: ("mov", "edx,DWORD PTR [esi+0x94d72c]"),
    0x52081a: ("mov", "eax,DWORD PTR [esi+0x94d72c]"),
    0x520832: ("mov", "edx,DWORD PTR [esi+0x94d72c]"),
    0x5233ed: ("mov", "edi,DWORD PTR [edx+0x94d72c]"),
    0x532876: ("mov", "eax,DWORD PTR [edi+0x94d72c]"),
    0x5362d5: ("mov", "ecx,DWORD PTR [eax+0x94d72c]"),
    0x520573: ("mov", "DWORD PTR [esi+0x94d738],eax"),
    0x59f29e: ("mov", "DWORD PTR [ebx+0x94d738],edx"),
    0x45b23f: ("mov", "ecx,DWORD PTR [eax+0x94d738]"),
    0x520826: ("mov", "ecx,DWORD PTR [esi+0x94d738]"),
    0x4eacd9: ("mov", "DWORD PTR [ecx],esi"),
    0x4f5cb0: ("add", "DWORD PTR [esi+0x94d738],ecx"),
}
def g3_roles():
    ok = True
    for a in sorted(P_ROLES):
        t = ins(a)
        good = t == P_ROLES[a]
        ok = ok and good
        row("G3 role %06x: %s %s %s" % (a, t[0], t[1], "OK" if good else "MISMATCH"))
    gate("G3", ok, "16 exact role pins: +2fc W={entry-zero 520567, tail-inc 52080c, "
         "reset 59f264} + feeder 4eacd9; +308 W={entry-zero 520573, reset 59f29e} "
         "+ feeder 4f5cb0; all readers literal")
    return ok

# ---------------- G4: entry zeroing (shared quartet, M330 G7 re-pin) ----------------
P_ZERO = {0x520561: 0x94d828, 0x520567: 0x94d72c, 0x52056d: 0x94d730, 0x520573: 0x94d738}
P_ZGAP = {0x520559: ("shl", "esi,0x4"), 0x52055c: ("sub", "esi,edi"),
          0x52055e: ("shl", "esi,0x2")}
def g4_zero():
    x = ins(0x520557)
    ok = x == ("xor", "eax,eax")
    det = []
    for a, disp in sorted(P_ZERO.items()):
        mn, o = ins(a)
        good = mn == "mov" and o == "DWORD PTR [esi+0x%x],eax" % disp
        ok = ok and good
        det.append("%06x:+%x=%s" % (a, disp - BLKBASE, "0" if good else "?"))
    gapok = all(ins(a) == t for a, t in P_ZGAP.items())
    eaxdefs = reg_defs(0x520558, 0x520574, {"eax", "ax", "al", "ah"})
    tgts = set()
    for a in m326.ADDRS:
        if a < 0x520540: continue
        if a >= 0x520579: break
        mn, o = ins(a)
        if mn.startswith("j"):
            t = o.split()[-1]
            if t.startswith("0x"): tgts.add(int(t, 16))
    midtgts = sorted(t for t in tgts if 0x520559 <= t <= 0x520573)
    row("G4 entry-zero: %s | %s | gap=%s eaxdefs=%s mid-branch-targets=%s"
        % (x, " ".join(det), gapok, eaxdefs, midtgts))
    ok = ok and gapok and eaxdefs == [] and midtgts == []
    gate("G4", ok, "upkeep entry 520540 zeroes +3f8/+2fc/+300/+308 (eax=0 xor@520557, "
         "liveness + no mid-branch measured): BOTH siblings are per-upkeep accumulators")
    return ok

# ---------------- G5: +2fc feeder law (FUN_004eaa10) ----------------
P_F2 = {0x4eaa16: ("mov", "eax,ds:0x8f0d60"),
        0x4eaa2b: ("mov", "bl,BYTE PTR [eax+0x4]"),
        0x4eaa4d: ("mov", "DWORD PTR [ebp-0x4],ebx"),
        0x4eac54: ("mov", "ebx,DWORD PTR [ebp-0x4]"),
        0x4f5a99: ("mov", "DWORD PTR [ebp-0x8],ecx"),
        0x4f5c33: ("mov", "eax,DWORD PTR [ebp-0x8]"),
        0x4f5c3c: ("mov", "ds:0x8f0d60,eax"),
        0x4f5b4b: ("call", "0x4eaa10"),
        0x4eaa23: ("mov", "esi,DWORD PTR [eax+0xc4]"),
        0x4eaa2e: ("add", "esi,ecx"),
        0x4eaa30: ("mov", "DWORD PTR [eax+0xc4],esi"),
        0x4eaa1b: ("mov", "ecx,DWORD PTR ds:0x8f0c74"),
        0x4eaa3c: ("mov", "eax,ds:0x8f0c3c"),
        0x4eaa42: ("mov", "DWORD PTR [edx+0xf4],eax"),
        0x4eaa50: ("mov", "ecx,DWORD PTR [eax+0xc4]"),
        0x4eaa56: ("mov", "edx,DWORD PTR [eax+0xf4]"),
        0x4eaa5c: ("sub", "ecx,edx"),
        0x4eaa5e: ("push", "ecx"),
        0x4eaa5f: ("call", "0x4e9880"),
        0x4eaa6d: ("mov", "DWORD PTR [edx+0xe4],eax"),
        0x4eaa78: ("mov", "ecx,DWORD PTR [eax+0xc4]"),
        0x4eaa7e: ("mov", "esi,DWORD PTR [eax+0xf4]"),
        0x4eaa84: ("mov", "edx,DWORD PTR [eax+0xe4]"),
        0x4eaa8a: ("sub", "ecx,esi"),
        0x4eaa8c: ("sub", "ecx,edx"),
        0x4eaa8e: ("mov", "DWORD PTR [eax+0xd4],ecx"),
        0x4eac90: ("mov", "eax,ds:0x8f0d64"),
        0x4eac95: ("mov", "edx,DWORD PTR ds:0x8f0d60"),
        0x4eac9b: ("cmp", "eax,0x1"),
        0x4eaca0: ("mov", "eax,DWORD PTR [edx+0xd4]"),
        0x4eaca6: ("test", "eax,eax"),
        0x4eaca8: ("jl", "0x4eacb8"),
        0x4eacaa: ("cmp", "eax,0x1869f"),
        0x4eacaf: ("jle", "0x4eacba"),
        0x4eacb1: ("mov", "eax,0x1869f"),
        0x4eacb8: ("xor", "eax,eax"),
        0x4eacba: ("mov", "ecx,ebx"),
        0x4eacbc: ("shl", "ecx,0x6"),
        0x4eacbf: ("add", "ecx,ebx"),
        0x4eacc1: ("lea", "ecx,[ebx+ecx*2]"),
        0x4eacc4: ("shl", "ecx,0x4"),
        0x4eacc7: ("sub", "ecx,ebx"),
        0x4eacd7: ("add", "esi,eax"),
        0x4e8d86: ("mov", "ds:0x8f0c74,eax"),
        0x4e8d97: ("mov", "DWORD PTR ds:0x8f0c3c,ecx"),
        0x4f5b19: ("mov", "esi,0x1"),
        0x4f5b2c: ("mov", "DWORD PTR ds:0x8f0d64,esi"),
        0x4f5bdd: ("mov", "DWORD PTR ds:0x8f0d64,0x2"),
        0x4f5f11: ("mov", "DWORD PTR ds:0x8f0d64,0x0")}
def g5_feeder2fc():
    ok = all(ins(a) == t for a, t in P_F2.items())
    jne = ins(0x4eac9e)
    ok = ok and jne[0] == "jne" and "0x4eacdb" in jne[1]
    # fold multiplier DERIVED from the pinned ops: ((64+1)*2+1)*16-1 then *4
    fold = (((1 << 6) + 1) * 2 + 1) * 16 - 1
    stride = fold * 4
    clamp_hi = int(ins(0x4eacaa)[1].split(",")[1], 16)
    # phase-flag store set MEASURED image-wide (not authored)
    ph = sorted(a for a in m326.ADDRS
                if ins(a)[0] == "mov"
                and ins(a)[1].startswith("DWORD PTR ds:0x8f0d64,"))
    # 8f0c3c / 8f0c74 store sets MEASURED (both shapes: with/without DWORD PTR)
    s3c = sorted(a for a in m326.ADDRS if ins(a)[0] == "mov"
                 and re.match(r"(DWORD PTR )?ds:0x8f0c3c,", ins(a)[1]))
    s74 = sorted(a for a in m326.ADDRS if ins(a)[0] == "mov"
                 and re.match(r"(DWORD PTR )?ds:0x8f0c74,", ins(a)[1]))
    row("G5 feeder2fc: pins=%s jne=%s fold=%d stride=%d clamp_hi=%d phase-stores=%s "
        "8f0c3c-stores=%s 8f0c74-stores=%s"
        % (all(ins(a) == t for a, t in P_F2.items()), jne, fold, stride, clamp_hi,
           [hex(a) for a in ph], [hex(a) for a in s3c], [hex(a) for a in s74]))
    ok = (ok and stride == STRIDE and clamp_hi == 99999
          and ph == [0x4f5b2c, 0x4f5bdd, 0x4f5f11]
          and s3c == [0x4e8d97] and s74 == [0x4e8d86])
    # review #345 P1-1: the OWNER chain is measured end-to-end:
    # bl:=[8f0d60+4] @4eaa2b -> spill [ebp-0x4] @4eaa4d (SOLE store in 4eaa10)
    # -> reload ebx @4eac54 -> fold @4eacba (no ebx redef in between).
    # 8f0d60 inside the caller 4f5a70 is stored ONLY at 4f5a93 (= the G6
    # base_array fold 0x95da10+0x130*arg) and 4f5c3c (restore of the SAME
    # value via the sole-def [ebp-0x8] spill @4f5a99). The phase-1 call 4f5b4b
    # sits between the =1 store (4f5b2c) and the =2 store (4f5bdd).
    # base_rec+4 = owner player index is the M43/M311 identity (NAMED.md:384).
    fn4e = next(f for f in m326.funcs if f[0] == 0x4eaa10)
    s4 = stores_to_ebp_slot(fn4e[0], fn4e[0] + max(fn4e[2], 1), "-0x4")
    ebxlive = reg_defs(0x4eac55, 0x4eacba, {"ebx", "bx", "bl", "bh"})
    fn4f = next(f for f in m326.funcs if f[0] == 0x4f5a70)
    p60 = sorted(a for a in m326.ADDRS
                 if fn4f[0] <= a < fn4f[0] + max(fn4f[2], 1)
                 and ins(a)[0] == "mov"
                 and re.match(r"(DWORD PTR )?ds:0x8f0d60,", ins(a)[1]))
    s8 = stores_to_ebp_slot(fn4f[0], fn4f[0] + max(fn4f[2], 1), "-0x8")
    phwin = (0x4f5b2c < 0x4f5b4b < 0x4f5bdd
             and not [a for a in ph if 0x4f5b2c < a < 0x4f5bdd])
    row("G5 owner-chain: [-0x4]stores4e=%s ebx(4eac54,4eacba)=%s "
        "8f0d60-stores4f=%s [-0x8]stores4f=%s phase1-call-window=%s"
        % ([hex(a) for a in s4], [hex(a) for a in ebxlive],
           [hex(a) for a in p60], [hex(a) for a in s8], phwin))
    ok = (ok and s4 == [0x4eaa4d] and ebxlive == []
          and p60 == [0x4f5a93, 0x4f5c3c] and s8 == [0x4f5a99] and phwin)
    gate("G5", ok, "+2fc feeder 4eacd9 (FUN_004eaa10): gate ds:8f0d64==1 (phase 1, "
         "set @4f5b2c only, call 4f5b4b inside the =1/=2 window); += clamp(base_rec"
         "+0xd4,0,99999); +0xd4 = +0xc4-+0xf4-4e9880(+0xc4-+0xf4); +0xc4 += 8f0c74, "
         "+0xf4 := 8f0c3c (sole stores in 4e8d60); OWNER chain measured: bl:="
         "[8f0d60+4] -> sole-def spill -> reload -> 8380-fold; 8f0d60 in the caller "
         "= base_array fold only (M311; +4=owner per M43, NAMED.md:384)")
    return ok

# ---------------- G6: +308 feeder law (FUN_004f5a70, per owned base) ----------------
P_F3 = {0x4f5a77: ("mov", "ebx,DWORD PTR [ebp+0x8]"),
        0x4f5a7c: ("mov", "DWORD PTR ds:0x68cbb0,ebx"),
        0x4f5a82: ("lea", "eax,[ebx+ebx*8]"),
        0x4f5a87: ("lea", "eax,[ebx+eax*2]"),
        0x4f5a8a: ("shl", "eax,0x4"),
        0x4f5a8d: ("lea", "ecx,[eax+0x95da10]"),
        0x4f5a93: ("mov", "DWORD PTR ds:0x8f0d60,ecx"),
        0x4f5a9c: ("mov", "dl,BYTE PTR [ecx+0x4]"),
        0x4f5aa9: ("mov", "edi,edx"),
        0x4f5b7c: ("mov", "edx,edi"),
        0x4f5b7e: ("shl", "edx,0x6"),
        0x4f5b81: ("add", "edx,edi"),
        0x4f5b83: ("lea", "esi,[edi+edx*2]"),
        0x4f5b86: ("shl", "esi,0x4"),
        0x4f5b89: ("sub", "esi,edi"),
        0x4f5b8b: ("shl", "esi,0x2"),
        0x4f5c74: ("mov", "eax,DWORD PTR [esi+0x94d650]"),
        0x4f5c7f: ("mov", "edx,DWORD PTR [ecx+0xfc]"),
        0x4f5c85: ("add", "eax,edx"),
        0x4f5c8c: ("mov", "DWORD PTR [esi+0x94d650],eax"),
        0x4f5c7a: ("mov", "ebx,0x8f0d40"),
        0x4f5c87: ("mov", "edx,0x1"),
        0x4f5c92: ("mov", "eax,0x94f5ac"),
        0x4f5c97: ("cmp", "edx,edi"),
        0x4f5c9b: ("mov", "ecx,DWORD PTR [esi+0x94d4f0]"),
        0x4f5ca1: ("test", "ecx,ecx"),
        0x4f5ca5: ("cmp", "DWORD PTR [eax],0x0"),
        0x4f5caa: ("mov", "ecx,DWORD PTR [ebx]"),
        0x4f5cae: ("xor", "ecx,ecx"),
        0x4f5cb0: ("add", "DWORD PTR [esi+0x94d738],ecx"),
        0x4f5cb6: ("add", "eax,0x20bc"),
        0x4f5cbb: ("inc", "edx"),
        0x4f5cbc: ("add", "ebx,0x4"),
        0x4f5cbf: ("cmp", "eax,0x95dad0"),
        0x520699: ("mov", "eax,ds:0x985af4"),
        0x52069e: ("xor", "ebx,ebx"),
        0x5206c2: ("mov", "edi,0x95da14"),
        0x5206c7: ("mov", "eax,DWORD PTR [ebp+0x8]"),
        0x5206cc: ("mov", "cl,BYTE PTR [edi]"),
        0x5206ce: ("cmp", "ecx,eax"),
        0x5206d2: ("push", "ebx"),
        0x5206d3: ("call", "0x4f5a70"),
        0x5206db: ("test", "eax,eax"),
        0x5206dd: ("je", "0x5206e6"),
        0x5206df: ("dec", "ebx"),
        0x5206e0: ("sub", "edi,0x130"),
        0x5206f0: ("inc", "ebx"),
        0x5206f1: ("add", "edi,0x130"),
        0x5206f7: ("cmp", "ebx,eax")}
def g6_feeder308():
    ok = all(ins(a) == t for a, t in P_F3.items())
    je1 = ins(0x4f5c99); jne1 = ins(0x4f5ca3); jne2 = ins(0x4f5ca8)
    jmp1 = ins(0x4f5cac); jl = ins(0x4f5cc4); jne3 = ins(0x5206d0)
    jl2 = ins(0x5206f9); jle = ins(0x5206c0)
    ok = (ok and je1 == ("je", "0x4f5cb6") and jne1 == ("jne", "0x4f5cae")
          and jne2 == ("jne", "0x4f5cae") and jmp1 == ("jmp", "0x4f5cb0")
          and jl[0] == "jl" and "0x4f5c97" in jl[1]
          and jne3 == ("jne", "0x5206eb") and jl2[0] == "jl"
          and "0x5206c7" in jl2[1] and jle[0] == "jle" and "0x5206fd" in jle[1])
    # DERIVED: record stride, loop init/bound/iters, block fold
    recstride = (1 + 2 * 9) * 16
    init = int(ins(0x4f5c92)[1].split(",")[1], 16)
    bound = int(ins(0x4f5cbf)[1].split(",")[1], 16)
    iters = (bound - init) // STRIDE
    fold = ((((1 << 6) + 1) * 2 + 1) * 16 - 1) * 4
    # liveness: sole esi/edi redefs between fold and use are EXIT-path pops
    esid = reg_defs(0x4f5b8c, 0x4f5cb0, {"esi", "si"})
    edid = reg_defs(0x4f5b8c, 0x4f5cb0, {"edi", "di"})
    edid2 = reg_defs(0x4f5aaa, 0x4f5b7c, {"edi", "di"})
    exitpins = (ins(0x4f5c0d) == ("ret", "") and ins(0x4f5b13) == ("ret", "")
                and ins(0x4f5c03) == ("pop", "esi")
                and ins(0x4f5c02) == ("pop", "edi")
                and ins(0x4f5b08) == ("pop", "edi"))
    row("G6 feeder308: pins=%s recstride=%d init=%x bound=%x iters=%d fold=%d "
        "esi-defs=%s edi-defs=%s edi(load,fold)=%s exitpins=%s"
        % (all(ins(a) == t for a, t in P_F3.items()), recstride, init, bound,
           iters, fold, [hex(a) for a in esid], [hex(a) for a in edid],
           [hex(a) for a in edid2], exitpins))
    ok = (ok and recstride == 0x130 and init == BLKBASE + STRIDE + 0xc0
          and bound == BLKBASE + NBLK * STRIDE + 0xc0 and iters == NBLK - 1
          and fold == STRIDE and esid == [0x4f5c03] and edid == [0x4f5c02]
          and edid2 == [0x4f5b08] and exitpins)
    # review #345 P1-4: the CALLER loop is measured end-to-end: cursor edi walks
    # base_array+4 (0x95da14, stride 0x130 — the M311/M43 base_array identity,
    # NAMED.md:46,491), bound = ds:0x985af4 (the base count), owner compare vs
    # the faction arg [ebp+8] loaded @5206c7; push ebx IS the loop index: ebx
    # starts 0 (xor @52069e) and its ONLY defs in the loop body are the retry
    # dec @5206df (paired with sub edi,0x130 @5206e0 -> same index re-processed)
    # and the tail inc @5206f0. esi/edi inside 4f5a70 are callee-saved across
    # the calls; their only redefs in the windows are the exit-path pops above.
    ebxloop = reg_defs(0x52069f, 0x5206fa, {"ebx", "bx", "bl", "bh"})
    row("G6 caller-loop: ebx-defs(52069e,5206f9)=%s retry=%s/%s"
        % ([hex(a) for a in ebxloop], ins(0x5206df), ins(0x5206e0)))
    ok = ok and ebxloop == [0x5206df, 0x5206f0]
    gate("G6", ok, "+308 feeder 4f5cb0: FUN_004f5a70(base_idx) called per OWNED base "
         "(5206d3; cursor=base_array+4/0x130, bound=985af4, owner==[ebp+8] @5206c7; "
         "push ebx = loop index, sole defs retry-dec/tail-inc); esi=8380*owner "
         "(owner=base_rec+4); loop k=1..7 skips self, gates block+0xc0==0 (self AND "
         "k), += 8f0d40[k-1]; ENERGY += base_rec+0xfc @4f5c85-8c; exit-pop liveness")
    return ok

# ---------------- G7: upkeep tail — interest OR +1/base fallback ----------------
P_TAIL = {0x520795: ("mov", "ecx,DWORD PTR [ebp+0x8]"),
          0x520798: ("lea", "ebx,[ecx+ecx*4]"),
          0x52079b: ("lea", "ebx,[ebx+ebx*8]"),
          0x52079e: ("shl", "ebx,0x3"),
          0x5207a1: ("sub", "ebx,ecx"),
          0x5207a3: ("shl", "ebx,0x2"),
          0x5207a6: ("mov", "eax,DWORD PTR [ebx+0x927a98]"),
          0x5207ac: ("test", "ah,0x40"),
          0x5207b1: ("mov", "eax,DWORD PTR [ebx+0x927a7c]"),
          0x5207b7: ("test", "eax,eax"),
          0x5207bb: ("mov", "ecx,DWORD PTR [esi+0x94d650]"),
          0x5207c1: ("imul", "eax,ecx"),
          0x5207c6: ("mov", "eax,0x51eb851f"),
          0x5207cb: ("imul", "edx"),
          0x5207cd: ("sar", "edx,0x5"),
          0x5207d0: ("mov", "eax,edx"),
          0x5207d2: ("shr", "eax,0x1f"),
          0x5207d5: ("add", "edx,eax"),
          0x5207d7: ("add", "edx,ecx"),
          0x5207d9: ("mov", "DWORD PTR [esi+0x94d650],edx"),
          0x5207e1: ("mov", "edi,DWORD PTR ds:0x985af4"),
          0x5207e7: ("test", "edi,edi"),
          0x5207e9: ("jle", "0x52081a"),
          0x5207eb: ("mov", "eax,0x95da14"),
          0x596ec3: ("push", "0x2ce0"),
          0x596ec8: ("push", "0x927590"),
          0x596ed6: ("call", "0x64cc00"),
          0x5207f0: ("xor", "edx,edx"),
          0x5207f2: ("mov", "dl,BYTE PTR [eax]"),
          0x5207f4: ("cmp", "edx,ecx"),
          0x5207f8: ("mov", "edx,DWORD PTR [esi+0x94d650]"),
          0x5207fe: ("inc", "edx"),
          0x5207ff: ("mov", "DWORD PTR [esi+0x94d650],edx"),
          0x52080b: ("inc", "edx"),
          0x520812: ("add", "eax,0x130"),
          0x520817: ("dec", "edi")}
MAGIC100 = 0x51eb851f
def magic_div100(x):
    prod = x * MAGIC100
    hi = prod >> 32                      # Python >> on negatives = arithmetic (sar)
    hi = hi >> 5                         # sar edx,0x5
    return hi + (1 if hi < 0 else 0)     # shr eax,0x1f + add edx,eax
def g7_tail():
    ok = all(ins(a) == t for a, t in P_TAIL.items())
    je1 = ins(0x5207af); je2 = ins(0x5207b9); jne1 = ins(0x5207f6)
    jmp1 = ins(0x5207df); jne2 = ins(0x520818)
    ok = (ok and je1 == ("je", "0x52081a") and je2 == ("je", "0x5207e1")
          and jne1 == ("jne", "0x520812") and jmp1 == ("jmp", "0x52081a")
          and jne2[0] == "jne" and "0x5207f0" in jne2[1])
    profstride = (((1 + 4) * 9) * 8 - 1) * 4     # lea5/lea9/shl3/sub/shl2
    rate_off = 0x927a7c - 0x927590
    gate_off = 0x927a98 - 0x927590
    xs = [-1000, -7, -1, 0, 1, 99, 100, 101, 9999, 100000]
    model_ok = all(magic_div100(x) == int(x / 100) for x in xs)
    # the tail block writes ONLY these block fields (MEASURED)
    st = block_stores(0x5207a6, 0x52081a)
    row("G7 tail: pins=%s profstride=%d rate_off=%x gate_off=%x model100=%s "
        "stores=%s samples=%s"
        % (all(ins(a) == t for a, t in P_TAIL.items()), profstride, rate_off,
           gate_off, model_ok, [(hex(a), hex(d - BLKBASE)) for a, d in st],
           [(x, magic_div100(x)) for x in (99, 100, 101, 9999)]))
    ok = (ok and profstride == 1436 and rate_off == 0x4ec and gate_off == 0x508
          and model_ok
          and st == [(0x5207d9, 0x94d650), (0x5207ff, 0x94d650), (0x52080c, 0x94d72c)])
    # review #345 P2-5: the facprofile IDENTITY is byte-tied to the M324 save
    # carry: fread @596ed6 loads 0x2ce0 bytes into 0x927590 (push pins above);
    # 0x2ce0/8 = 1436 = the SAME stride the tail fold derives, so [ebx+0x927a7c]
    # with ebx=1436*faction is facprofile(faction)+0x4ec, not an unrelated array.
    ldsz = int(ins(0x596ec3)[1], 16)
    ldbs = int(ins(0x596ec8)[1], 16)
    row("G7 facprofile-id: load=%x size=%x size/8=%d == profstride=%s"
        % (ldbs, ldsz, ldsz // NBLK, ldsz // NBLK == profstride))
    ok = ok and ldbs == 0x927590 and ldsz == 0x2ce0 and ldsz // NBLK == profstride
    gate("G7", ok, "upkeep tail: facprofile(1436-fold, byte-tied to M324 save carry "
         "596ec3/ec8/ed6: 0x2ce0=8*1436 @0x927590)+0x508 bit14 gate; rate=+0x4ec: "
         "ENERGY += trunc(ENERGY*rate/100) (magic 51eb851f sar5+signfix); rate==0 "
         "fallback: per OWNED base (95da14/985af4 walk) ENERGY+=1 AND +2fc+=1; "
         "tail writes ONLY +220/+2fc (ALL store mnemonics scanned, no +308)")
    return ok

# ---------------- G8: ledger pins + SAVE numeric law ----------------
P_LEDGER = {0x520820: ("mov", "DWORD PTR [esi+0x94d740],eax"),
            0x520838: ("sub", "ecx,edi"),
            0x52083a: ("mov", "eax,0x1"),
            0x52083f: ("add", "ecx,edx"),
            0x520841: ("mov", "DWORD PTR [esi+0x94d73c],ecx")}
def g8_ledger():
    ok = all(ins(a) == t for a, t in P_LEDGER.items())
    # loads pinned by G3 (52081a +2fc, 520826 +308, 52082c +300, 520832 +2fc)
    sv = {}
    for off in (0x2fc, 0x308, 0x300, 0x30c, 0x310, 0x220):
        retarget(off)
        s = m326.save_values()
        if s is None:
            gate("G8", False, "save parse failed")
            return False
        sv[off] = s
    v2fc, v308, v300 = sv[0x2fc]["vals"], sv[0x308]["vals"], sv[0x300]["vals"]
    v30c, v310 = sv[0x30c]["vals"], sv[0x310]["vals"]
    ledger = [v308[k] - v300[k] + v2fc[k] for k in range(NBLK)]
    minus = [v308[k] - v300[k] - v2fc[k] for k in range(NBLK)]
    row("G8 ledger: pins=%s v2fc=%s v308=%s v300=%s v30c=%s v310=%s law=%s minus=%s"
        % (ok, v2fc, v308, v300, v30c, v310, ledger, minus))
    # review #345 P1-2: the INSTRUCTION law needs register liveness between the
    # loads (G3 pins 52081a/520826/52082c/520832) and the stores/arithmetic, plus
    # no branch into the middle of the ledger sequence, plus esi (the block base,
    # folded at entry per G4 P_ZGAP) unredefined from entry to the ledger.
    eaxl = reg_defs(0x52081b, 0x520820, {"eax", "ax", "al", "ah"})
    ecxl1 = reg_defs(0x520827, 0x520838, {"ecx", "cx", "cl", "ch"})
    edil = reg_defs(0x52082d, 0x520838, {"edi", "di"})
    edxl = reg_defs(0x520833, 0x52083f, {"edx", "dx", "dl", "dh"})
    ecxl2 = reg_defs(0x520840, 0x520841, {"ecx", "cx", "cl", "ch"})
    esil = reg_defs(0x52055f, 0x520842, {"esi", "si"})
    tgts = set()
    for a in m326.ADDRS:
        if a < 0x520540: continue
        if a >= 0x520900: break
        mn, o = ins(a)
        if mn.startswith("j"):
            t = o.split()[-1]
            if t.startswith("0x"): tgts.add(int(t, 16))
    midt = sorted(t for t in tgts if 0x52081b <= t <= 0x520841)
    row("G8 liveness: eax=%s ecx1=%s edi=%s edx=%s ecx2=%s esi(entry,ledger)=%s "
        "mid-branch=%s" % ([hex(a) for a in eaxl], [hex(a) for a in ecxl1],
        [hex(a) for a in edil], [hex(a) for a in edxl], [hex(a) for a in ecxl2],
        [hex(a) for a in esil], [hex(t) for t in midt]))
    ok = (ok and eaxl == [] and ecxl1 == [] and edil == [] and edxl == []
          and ecxl2 == [] and esil == [] and midt == [])
    ok = (ok and v2fc == [0, 7, 14, 4, 32, 9, 9, 2]
          and v308 == [0, 0, 0, 0, 3, 0, 0, 0]
          and v300 == [0, 1, 1, 0, 1, 0, 1, 1]          # M330 carry
          and v310 == v2fc and v30c == ledger
          and sv[0x2fc]["off"] == 0x32c and sv[0x2fc]["round"] == 50)
    gate("G8", ok, "+310 := +2fc; +30c := +308-+300++2fc: byte pins + load->store "
         "register liveness (eax/ecx/edi/edx) + esi unredefined entry->ledger + no "
         "mid-branch; the save law CORROBORATES numerically on all 8 m54b_clean "
         "blocks (v310==v2fc, v30c==ledger); minus-variant printed for R5")
    return ok

# ---------------- G9: 546800 cap — MIN(ENERGY/2, 100*net) >= 50 ----------------
P_546 = {0x54b1ba: ("mov", "edx,esi"), 0x54b1bf: ("shl", "edx,0x6"),
         0x54b1c4: ("add", "edx,esi"), 0x54b1c9: ("lea", "ecx,[esi+edx*2]"),
         0x54b1cf: ("shl", "ecx,0x4"), 0x54b1d4: ("sub", "ecx,esi"),
         0x54b1d9: ("shl", "ecx,0x2"), 0x54b1e5: ("mov", "DWORD PTR [ebp+0x8],ecx"),
         0x54b35c: ("mov", "edx,DWORD PTR [ebp+0x8]"),
         0x54b361: ("mov", "ecx,DWORD PTR [edx+0x94d72c]"),
         0x54b367: ("mov", "ebx,DWORD PTR [edx+0x94d730]"),
         0x54b353: ("mov", "eax,DWORD PTR [eax+0x94d650]"),
         0x54b359: ("cdq", ""), 0x54b35a: ("sub", "eax,edx"),
         0x54b35f: ("sar", "eax,1"),
         0x54b36d: ("sub", "ecx,ebx"),
         0x54b372: ("lea", "ecx,[ecx+ecx*4]"),
         0x54b375: ("lea", "ecx,[ecx+ecx*4]"),
         0x54b378: ("shl", "ecx,0x2"),
         0x54b37b: ("cmp", "eax,ecx"),
         0x54b37f: ("mov", "eax,ecx"),
         0x54b381: ("mov", "DWORD PTR [ebp+0xc],eax"),
         0x54b384: ("cmp", "eax,0x32"),
         0x54684a: ("mov", "edi,DWORD PTR [ebp+0x8]"),
         0x54d3ab: ("mov", "edx,edi"), 0x54d3ad: ("shl", "eax,0x6"),
         0x54d3b0: ("shl", "edx,0x6"), 0x54d3b3: ("add", "eax,esi"),
         0x54d3b5: ("add", "edx,edi"), 0x54d3b7: ("lea", "eax,[esi+eax*2]"),
         0x54d3ba: ("lea", "ebx,[edi+edx*2]"),
         0x54d3bd: ("shl", "eax,0x4"), 0x54d3c0: ("shl", "ebx,0x4"),
         0x54d3c3: ("sub", "eax,esi"), 0x54d3c5: ("sub", "ebx,edi"),
         0x54d3c7: ("shl", "eax,0x2"), 0x54d3ca: ("shl", "ebx,0x2")}
def g9_cap546():
    ok = all(ins(a) == t for a, t in P_546.items())
    jl1 = ins(0x54b37d); jl2 = ins(0x54b387)
    ok = (ok and jl1 == ("jl", "0x54b384") and jl2[0] == "jl"
          and "0x54b91b" in jl2[1])
    # x100 DERIVED from the pinned fold ops
    scale = (1 + 4) * (1 + 4) * 4
    thr = int(ins(0x54b384)[1].split(",")[1], 16)
    ow = stores_to_ebp_slot(0x54b1e6, 0x54b35c, "+0x8")
    edilive = reg_defs(0x54684b, 0x54d3ab, {"edi", "di"})
    fold = ((((1 << 6) + 1) * 2 + 1) * 16 - 1) * 4
    # review #345 round: liveness-window WITNESS pins — the two insns inside the
    # measured windows that the scanner mutants patch (MU41 shift-write to edi,
    # MU42 non-mov write to [ebp+8]); literal-read here for L2b.
    P_LIVEW = {0x54b350: ("mov", "eax,DWORD PTR [ebp-0x14]"),
               0x54b348: ("test", "eax,eax")}
    wok = all(ins(a) == t for a, t in P_LIVEW.items())
    row("G9 cap546: pins=%s scale=%d thr=%d overwrite(54b1e5,54b35c)=%s "
        "edi-defs(54684a,54d3ab)=%s fold=%d witnesses=%s"
        % (all(ins(a) == t for a, t in P_546.items()), scale, thr, ow,
           [hex(a) for a in edilive], fold, wok))
    ok = (ok and scale == 100 and thr == 50 and ow == [] and edilive == []
          and fold == STRIDE and wok)
    gate("G9", ok, "546800: net=+2fc-+300 (54b361/367, [ebp+8]=8380*esi last-overwrite "
         "law); cap=MIN(trunc(ENERGY/2), 100*net) (fold DERIVED=100); gate cap>=50 "
         "else exit 54b91b; second reader 54d43b = block(arg1)+2fc (edi sole def "
         "54684a, 8380-fold, zero redefs across 34 KB)")
    return ok

# ---------------- G10: 535c60 cap — MIN(net, block+0x1058) ----------------
P_535 = {0x5362c0: ("mov", "edx,ebx"), 0x5362c2: ("shl", "edx,0x6"),
         0x5362c5: ("add", "edx,ebx"), 0x5362c7: ("lea", "eax,[ebx+edx*2]"),
         0x5362ca: ("shl", "eax,0x4"), 0x5362cd: ("sub", "eax,ebx"),
         0x5362cf: ("shl", "eax,0x2"), 0x5362d2: ("mov", "DWORD PTR [ebp-0x18],eax"),
         0x5362e1: ("sub", "ecx,edx"),
         0x5362ef: ("mov", "edx,DWORD PTR [esi+0x94d72c]"),
         0x5362e3: ("mov", "edx,DWORD PTR [eax+0x94e488]"),
         0x5362e9: ("cmp", "edx,ecx"),
         0x5362ed: ("mov", "ecx,edx"),
         0x5362f5: ("sub", "edx,DWORD PTR [esi+0x94d730]"),
         0x5362fb: ("mov", "esi,DWORD PTR [esi+0x94e488]"),
         0x536301: ("cmp", "esi,edx"),
         0x536305: ("mov", "edx,esi"),
         0x536307: ("add", "edx,ecx"),
         0x536309: ("mov", "ecx,DWORD PTR [eax+0x94d650]"),
         0x53630f: ("imul", "edx,DWORD PTR [ebp+0xc]"),
         0x536313: ("mov", "eax,0x66666667"),
         0x536318: ("mov", "DWORD PTR [ebp+0xc],edx"),
         0x53631b: ("imul", "ecx"),
         0x53631d: ("mov", "ecx,DWORD PTR [ebp+0xc]"),
         0x536320: ("sar", "edx,1"),
         0x536322: ("mov", "eax,edx"),
         0x536324: ("shr", "eax,0x1f"),
         0x536327: ("add", "edx,eax"),
         0x536329: ("lea", "eax,[edx+ecx*2]"),
         # M330 G12 two-def law of [ebp-0x14] (re-pinned for the +2fc read 5362ef)
         0x535c90: ("mov", "edi,DWORD PTR [ebp+0xc]"),
         0x535cb1: ("mov", "eax,edi"), 0x535cb6: ("shl", "eax,0x6"),
         0x535cb9: ("add", "eax,edi"), 0x535cbb: ("lea", "eax,[edi+eax*2]"),
         0x535cbe: ("shl", "eax,0x4"), 0x535cc1: ("sub", "eax,edi"),
         0x535cc3: ("mov", "DWORD PTR [ebp-0x14],eax"),
         0x535f1a: ("mov", "ecx,edi"), 0x535f1c: ("shl", "ecx,0x6"),
         0x535f1f: ("add", "ecx,edi"), 0x535f21: ("lea", "esi,[edi+ecx*2]"),
         0x535f24: ("shl", "esi,0x4"), 0x535f27: ("sub", "esi,edi"),
         0x535f29: ("shl", "esi,0x2"), 0x535f2c: ("mov", "DWORD PTR [ebp-0x14],esi"),
         0x5362b1: ("mov", "esi,DWORD PTR [ebp-0x14]")}
MAGIC5 = 0x66666667
def magic_div5(x):
    prod = x * MAGIC5
    hi = prod >> 32
    hi = hi >> 1                         # sar edx,1 (arithmetic)
    return hi + (1 if hi < 0 else 0)
def g10_cap535():
    ok = all(ins(a) == t for a, t in P_535.items())
    jle1 = ins(0x5362eb); jle2 = ins(0x536303)
    ok = ok and jle1 == ("jle", "0x5362ef") and jle2 == ("jle", "0x536307")
    fn = next(f for f in m326.funcs if f[0] == 0x535c60)
    ss = stores_to_ebp_slot(fn[0], fn[0] + max(fn[2], 1), "-0x14")
    xs = [-100, -7, -1, 0, 1, 4, 5, 6, 10, 999999]
    model_ok = all(magic_div5(x) == int(x / 5) for x in xs)
    capoff = 0x94e488 - BLKBASE
    row("G10 cap535: pins=%s capoff=%x stores535[-0x14]=%s model5=%s samples=%s"
        % (all(ins(a) == t for a, t in P_535.items()), capoff,
           [hex(a) for a in ss], model_ok,
           [(x, magic_div5(x)) for x in (4, 5, 6, 10)]))
    ok = (ok and capoff == 0x1058 and ss == [0x535cc3, 0x535f2c] and model_ok)
    gate("G10", ok, "535c60: per faction fold, net=+2fc-+300 capped by block+0x1058 "
         "(MIN, both folds); sum*arg3 + trunc(ENERGY/5) (magic 66666667 sar1+signfix); "
         "5362ef +2fc read rides the M330 two-def [ebp-0x14] law (2095*arg3 / 8380*edi)")
    return ok

# ---------------- G11: reader laws ----------------
P_READ = {0x5233d5: ("cmp", "esi,edi"),
          0x5233d9: ("mov", "edi,DWORD PTR [edx+0x94d650]"),
          0x5233df: ("mov", "ebx,DWORD PTR [ecx-0xe0]"),
          0x5233e5: ("cmp", "ebx,edi"),
          0x5233f9: ("sub", "edi,ebx"),
          0x5233fb: ("mov", "ebx,DWORD PTR [ecx-0x4]"),
          0x5233fe: ("sub", "ebx,DWORD PTR [ecx]"),
          0x523400: ("cmp", "ebx,edi"),
          0x52340b: ("add", "ecx,0x20bc"),
          0x523412: ("cmp", "ecx,0x95dd10"),
          0x531df8: ("mov", "esi,DWORD PTR [ebp+0x8]"),
          0x531dfc: ("mov", "edi,DWORD PTR [ebp+0xc]"),
          0x531e3b: ("mov", "ecx,edi"),
          0x531e46: ("shl", "ecx,0x6"),
          0x531e4c: ("add", "ecx,edi"),
          0x531e51: ("lea", "ebx,[edi+ecx*2]"),
          0x531e57: ("shl", "ebx,0x4"),
          0x531e5d: ("sub", "ebx,edi"),
          0x531e61: ("shl", "ebx,0x2"),
          0x531e75: ("mov", "DWORD PTR [ebp-0x4],eax"),
          0x531e78: ("mov", "DWORD PTR [ebp-0xc],ebx"),
          0x532809: ("mov", "edi,DWORD PTR [ebp-0x4]"),
          0x53281a: ("mov", "edx,DWORD PTR [ebp-0xc]"),
          0x532876: ("mov", "eax,DWORD PTR [edi+0x94d72c]"),
          0x5328c5: ("mov", "eax,DWORD PTR [edx+0x94d72c]"),
          0x532864: ("cmp", "eax,0x63"),
          0x532869: ("mov", "ecx,0x63"),
          0x532874: ("xor", "ecx,ecx"),
          0x53287c: ("cdq", ""),
          0x53287d: ("idiv", "esi"),
          0x53287f: ("imul", "eax,ecx"),
          0x532882: ("mov", "ecx,DWORD PTR ds:0x920754"),
          0x532888: ("sub", "ecx,eax"),
          0x53288d: ("mov", "DWORD PTR ds:0x920754,ecx"),
          0x45b239: ("imul", "eax,eax,0x20bc"),
          0x45b23f: ("mov", "ecx,DWORD PTR [eax+0x94d738]"),
          0x45b245: ("push", "ecx"),
          0x45b24d: ("call", "0x423820"),
          0x40ed68: ("mov", "eax,ds:0x997b20"),
          0x40ed78: ("push", "eax"),
          0x40ed79: ("call", "0x61482f"),
          0x6146bf: ("call", "0x5be090"),
          0x6146c7: ("mov", "ds:0x997b20,eax")}
def g11_readers():
    ok = all(ins(a) == t for a, t in P_READ.items())
    jl = ins(0x523418)
    ok = ok and jl[0] == "jl" and "0x5233d5" in jl[1]
    # 531df0 slot-store sets MEASURED
    fn = next(f for f in m326.funcs if f[0] == 0x531df0)
    s4 = stores_to_ebp_slot(fn[0], fn[0] + max(fn[2], 1), "-0x4")
    sc = stores_to_ebp_slot(fn[0], fn[0] + max(fn[2], 1), "-0xc")
    clamp_hi = int(ins(0x532864)[1].split(",")[1], 16)
    brace_open = m326.pe_cstr(0x672aa8)
    brace_close = m326.pe_cstr(0x672a9c)
    # 997b20 store set MEASURED image-wide (both operand shapes)
    st997 = sorted(a for a in m326.ADDRS if ins(a)[0] == "mov"
                   and re.match(r"(DWORD PTR )?ds:0x997b20,", ins(a)[1]))
    row("G11 readers: pins=%s 531df0[-0x4]=%s [-0xc]=%s clamp=%d braces=%s/%s "
        "997b20-stores=%s"
        % (all(ins(a) == t for a, t in P_READ.items()), [hex(a) for a in s4],
           [hex(a) for a in sc], clamp_hi, brace_open, brace_close,
           [hex(a) for a in st997]))
    ok = (ok and s4 == [0x531e75] and sc == [0x531e78] and clamp_hi == 99
          and brace_open == b"{" and brace_close == b"}"
          and st997 == [0x614669, 0x6146c7])
    gate("G11", ok, "522b70: per-faction ENERGY + net(+2fc-+300) comparison score "
         "(both siblings read as a pair); 531df0: 920754 -= (block(arg1)+2fc/esi)*"
         "clamp(diff,0,99), arg2 +2fc via sole-def [ebp-0xc] fold; 45a920: formats "
         "block+308 into '{...}' template (423820); 40e720: +308 via 997b20 = HEAP "
         "alloc (5be090), NOT the raw block -> NONFIELD")
    return ok

# ---------------- G12: carry + turnfn + reset ----------------
def g12_carry():
    retarget(OFF2FC)
    sv = m326.save_values()
    if sv is None:
        gate("G12", False, "save parse failed")
        return False
    foffs2 = [sv["off"] + k * STRIDE + OFF2FC for k in range(NBLK)]
    foffs3 = [sv["off"] + k * STRIDE + OFF308 for k in range(NBLK)]
    rd = ins(0x596a91)
    ts = m326.turnfn_stores()
    blk = m326.turnfn_blkstores(ts)
    pin = ins(0x51f53c)
    r2 = ins(0x59f264); r3 = ins(0x59f29e)
    row("G12 carry: sha=%s round=%d energy=%s foffs2fc=%s foffs308=%s fread=%s "
        "turnfn=%d/%d pin=%s reset=%s/%s owners=%s/%s"
        % (sv["sha"], sv["round"], sv["energy"], [hex(x) for x in foffs2],
           [hex(x) for x in foffs3], rd, len(ts), len(blk), pin, r2, r3,
           m326.owner(0x59f264), m326.owner(0x59f29e)))
    ok = (sv["sha"] == "74d0f44ab9b9290b" and sv["round"] == 50
          and sv["energy"] == [10, 28, 112, 69, 229, 60, 102, 37]   # M325 blkA
          and rd == ("call", "0x64cc00")
          and foffs2 == [0x32c + OFF2FC + k * STRIDE for k in range(NBLK)]
          and foffs3 == [0x32c + OFF308 + k * STRIDE for k in range(NBLK)]
          and len(ts) == 16 and len(blk) == 0
          and pin == ("mov", "ds:0x985afc,eax")
          and r2 == ("mov", "DWORD PTR [ebx+0x94d72c],edx")
          and r3 == ("mov", "DWORD PTR [ebx+0x94d738],edx")
          and m326.owner(0x59f264) == "FUN_0059ec90"
          and m326.owner(0x59f29e) == "FUN_0059ec90")
    gate("G12", ok, "both siblings inside the M324 raw block carry (596a91 "
         "105e0/94d430), foffs pinned, energy==M325 blkA; turnfn 16st/0blk; "
         "reset writers in FUN_0059ec90 (M320 RESET)")
    return ok

# ---------------- G13: exclusions + arg-fed classification ----------------
P_EXCL = {0x5791a6: ("lea", "ecx,[eax*4+0x927590]"), 0x5791ae: ("call", "0x5791c0"),
          0x579e9c: ("mov", "esi,0x927590"), 0x579eaa: ("call", "0x5791c0"),
          0x5792d9: ("mov", "DWORD PTR [esi+0x2fc],ebx"),
          0x5792ef: ("mov", "DWORD PTR [esi+0x2fc],0x1"),
          0x579309: ("mov", "DWORD PTR [esi+0x2fc],0x2"),
          0x596c06: ("mov", "edx,DWORD PTR [edi+0x308]"),
          0x40ed72: ("mov", "eax,DWORD PTR [eax+0x308]")}
def g13_excl():
    ok = all(ins(a) == t for a, t in P_EXCL.items())
    # arg-fed NONFIELD hits resolved by G6/G9/G10/G11 — classification table
    cls = [("4f5cb0", "+308 FEEDER (G6: esi=8380*owner)"),
           ("54b361", "+2fc cap load (G9: [ebp+8] last-overwrite)"),
           ("54d43b", "+2fc reader (G9: edi=arg1 sole-def fold)"),
           ("5362ef", "+2fc cap load (G10: two-def [ebp-0x14])"),
           ("5328c5", "+2fc reader (G11: [ebp-0xc] sole-def fold)"),
           ("5792d9/ef/309", "facprofile+2fc (callers pass 0x927590)"),
           ("40ed72", "HEAP UI buffer via 997b20 (G11), not raw block"),
           ("596c06", "loader struct-rearrange (M330 family)"),
           ("449377/523dad/542972/544bae/544eac/554ee6",
            "DISP224 OUT-family (profile/ladder/stack siblings, M330)")]
    for a, c in cls:
        row("G13 class %s: %s" % (a, c))
    row("G13 excl pins=%s" % ok)
    gate("G13", ok, "3 facprofile+2fc writes excluded (0x927590 caller law, as M330's "
         "579329); 5 arg-fed NONFIELD hits RESOLVED to block reads (G6/G9/G10/G11); "
         "40ed72 heap; 596c06 loader; 6 DISP224 OUT-family")
    return ok

# ---------------- R: rivals ----------------
def rivals():
    # R1: persistent bases (survive upkeep entry) — needs the zero stores gone
    r1 = not (ins(0x520567) == ("mov", "DWORD PTR [esi+0x94d72c],eax")
              and ins(0x520573) == ("mov", "DWORD PTR [esi+0x94d738],eax")
              and ins(0x520557) == ("xor", "eax,eax"))
    # R2: fed by the +300 feeder 4f47f0 — scan its body for +2fc/+308 stores
    fn = next(f for f in m326.funcs if f[0] == 0x4f47f0)
    bad = []
    for a in m326.ADDRS:
        if a < fn[0]: continue
        if a >= fn[0] + max(fn[2], 1): break
        mn, o = ins(a)
        if mn in ("mov", "add", "sub") and ("0x94d72c" in o or "0x94d738" in o):
            if o.startswith("DWORD PTR"):
                bad.append(a)
    r2 = bool(bad) or ins(0x4f4962) != ("mov", "DWORD PTR [edi+0x94d730],edx")
    # R3: the cap scale is x10 or x1000 — derived scale must be exactly 100
    scale = (1 + 4) * (1 + 4) * 4
    r3 = scale != 100 or ins(0x54b372) != ("lea", "ecx,[ecx+ecx*4]") \
        or ins(0x54b375) != ("lea", "ecx,[ecx+ecx*4]") \
        or ins(0x54b378) != ("shl", "ecx,0x2")
    # R4: the interest/fallback block writes +308 — measured store set
    st = block_stores(0x5207a6, 0x52081a)
    r4 = any(d == 0x94d738 for _, d in st)
    # R5: ledger sign is -2fc — byte pin + numeric minus-variant
    retarget(OFF2FC)
    sv2 = m326.save_values()
    retarget(OFF308)
    sv3 = m326.save_values()
    retarget(0x300)
    sv0 = m326.save_values()
    retarget(0x30c)
    svc = m326.save_values()
    if not all((sv2, sv3, sv0, svc)):
        gate("R", False, "save parse failed")
        return False
    minus = [sv3["vals"][k] - sv0["vals"][k] - sv2["vals"][k] for k in range(NBLK)]
    r5 = ins(0x52083f) != ("add", "ecx,edx") or svc["vals"] == minus
    row("R rivals hold: R1(persistent)=%s R2(4f47f0-fed)=%s R3(scale!=100)=%s "
        "R4(tail-writes-308)=%s R5(minus-ledger)=%s scan4f47f0=%s"
        % (r1, r2, r3, r4, r5, [hex(a) for a in bad]))
    ok = not (r1 or r2 or r3 or r4 or r5)
    gate("R", ok, "R1 DEAD (entry-zero both); R2 DEAD (4f47f0 body has 0 sibling "
         "stores, its only store is +300 @4f4962); R3 DEAD (fold derives 100); "
         "R4 DEAD (tail store set = +220/+220/+2fc); R5 DEAD (add ecx,edx + save "
         "law matches plus-variant on all 8 blocks)")
    return ok

def main():
    print("== M331 ledger-siblings census (resolver: M326 import) patches=%d ==" % NPATCH)
    g12_census()
    g3_roles()
    g4_zero()
    g5_feeder2fc()
    g6_feeder308()
    g7_tail()
    g8_ledger()
    g9_cap546()
    g10_cap535()
    g11_readers()
    g12_carry()
    g13_excl()
    rivals()
    d = digest()
    npass = sum(1 for _, ok in GATES if ok)
    print("digest %s" % d)
    print("== M331: %d/%d ==" % (npass, len(GATES)))
    return 0 if npass == len(GATES) else 1

if __name__ == "__main__":
    sys.exit(main())