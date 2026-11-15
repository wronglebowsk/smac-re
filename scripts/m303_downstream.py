#!/usr/bin/env python3
"""M303 (s259, STATIC, zero box): what CONSUMES the counter after the increment -
the post-counter read at 0x51e02c, its index algebra, and its downstream consumers.

QUESTION (B19 DECLARED UNMODELED, NAMED.md B19 "the 0x51e02c 0x94ed28 post-read
downstream"; M299 lead "the byte read 0x51e02c [site + 8380*block + 0x94ed28] is a LEAD"):
  (a) the exact byte address 0x51e02c computes - symbolically, from the PRODUCERS of
      ebx/edx/ecx in the same function window; prove or REFUTE "this expression IS
      B18's 28-B stride law (site*8-site)<<2" from the registers, not from the law.
  (b) name the table at 0x94ed28 and its entry width / block stride from the index
      algebra (a *4 scale on top of a shl4/sub chain is NOT a plain dword index).
  (c) every other reader/writer of that address family in the corpus, and what the
      byte is used for downstream: gate a store, feed the MAX table at 0x989ce8,
      or terminate in a compare?
  (d) what stays UNKNOWN - stated plainly.

ANSWER (computed below; asserted at the end): 0x51e02c is NOT a pure read - it is the
load half of a BYTE RMW INCREMENT: 0x51e02c mov dl,[ecx+eax*4+0x94ed28] / 0x51e033 lea
eax,[SAME address] / 0x51e03a inc dl / 0x51e03e mov [eax],dl, entered on exactly the
same fall-through (je 0x51e007 skips the whole block) as the dword slot-counter inc
(M299). The folded index is site + 2095*block*4 = site + 8380*block: 0x94ed28 =
0x94eca8 + 0x80 is the per-block 128-entry visit-CNT byte array, twin of the per-block
128-entry MAX byte array at 0x94eca8 - both zeroed per call by the init loop
0x51dcb8-0x51dd03 (fields [edx+site] and [edx+site+0x80], edx stepping 0x20bc to the
stop constant 0x95f288: (0x95f288-0x94eca8)/8380 = 8 blocks), so the multiplier the
fold computes (8380) and the stride the init uses are the SAME number, derived twice.
It is the BYTE twin of the dword slot table 0x989ce8 (128 x {MAX@+0, CNT@+4}, stride
28): the byte family is indexed by (block, site), the dword table only by site. The
B18-28-B claim about THIS expression is REFUTED: the 28-B fold (site*8-site)<<2 is
three instructions earlier on DIFFERENT registers (esi) feeding the dword slot table,
while the 0x51e024-2a chain (lea[ebx+edx*2]; shl 4; sub ebx; *4) evaluates to 8380*ebx
with edx itself a derived copy (mov edx,ebx; shl 6; add = 65*ebx) - multipliers 28 and
8380 coexist in one window. Downstream: the incremented byte is NEVER a branch operand
(dl's only consumers are the inc and the store; the branch 0x51e040 je tests flags of
`test ebx,ebx` 0x51e03c); the family census over the whole .text dump is 11 literal
mentions - the byte-MAX field has 6 external readers (FUN_0050d140, FUN_00556690,
FUN_0055f650 x4), ALL terminating in cmp/test; the byte-CNT field has exactly ONE
other reader, FUN_004f6030 0x4f946d, consumer `test al,al`+`jne` (a visited? gate).
NO family byte feeds the dword MAX at 0x989ce8: both MAX stores take the walk's
candidate edi; the loaded bytes appear only in the cmp. The disp-only census
(name_global.py 0x94ed28 --disp) reports "0 writes" - the store at 0x51e03e is
pointer-form via the 0x51e033 lea: the register-after-lea class that evades any
displacement grep.

METHOD: every number printed is COMPUTED from evidence-grade inputs - the full .text
disassembly cache scratch/m574/text.txt (opcode + mnemonic columns) and
ghidra_out/index.csv containment; a small shadow evaluator (mov/shl/add/sub/lea) runs
the folds; rivals are evaluated on the SAME tables and must FAIL on printed numbers.
stdout mirrors to evidence/m303_downstream.txt. Run: python3 scripts/m303_downstream.py
(exit 0 = all assertions hold).
"""
import bisect
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
OUT = os.path.join(ROOT, "evidence/m303_downstream.txt")

LINE = re.compile(r"^  ([0-9a-f]{5,8}):\t((?:[0-9a-f]{2} )+)\s*\t(\S.*?)\s*$")
REG = r"(?:eax|ecx|edx|ebx|esi|edi|ebp)"
addr_line, order = {}, []


def load_text():
    with open(TEXT, errors="replace") as f:
        for ln in f:
            m = LINE.match(ln.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            if a not in addr_line:
                addr_line[a] = (m.group(2).strip(), m.group(3))
                order.append(a)
    order.sort()


def load_index():
    rows = []
    with open(INDEX) as f:
        for d in csv.DictReader(f):
            try:
                rows.append((int(d["addr"], 16), d["name"]))
            except (KeyError, ValueError):
                pass
    rows.sort()
    return rows


def owner(idx, a):
    k = bisect.bisect_right([x[0] for x in idx], a) - 1
    return idx[k][1] if k >= 0 else "?"


def win(lo, hi):
    return [(a, addr_line[a][0], addr_line[a][1]) for a in order if lo <= a <= hi]


def ins(a):
    return addr_line[a][1]


def enc(a):
    return addr_line[a][0]


# ---------------------------------------------------------------- shadow eval
def parse_mem(op):
    m = re.match(r"^(?:BYTE|WORD|DWORD) PTR \[([^]]+)\]$|^\[([^]]+)\]$", op.strip())
    if not m:
        return None
    expr = m.group(1) or m.group(2)
    terms = {"const": 0}
    for part in expr.split("+"):
        part = part.strip()
        mm = re.match(r"^(" + REG + r")\*(\d+)$", part)
        if mm:
            terms[mm.group(1)] = terms.get(mm.group(1), 0) + int(mm.group(2))
            continue
        if re.fullmatch(REG, part):
            terms[part] = terms.get(part, 0) + 1
            continue
        terms["const"] += int(part, 0)
    return terms


def shadow(items, seed, loads=None):
    """items: list of addresses (all seed regs must be in seed or produced).
    loads: normalized operand text -> value, for the [frame] loads the census pins."""
    loads = loads or {}
    v = dict(seed)
    for a in items:
        t = ins(a)
        m = re.match(r"^(\w+)\s+(.+?)(?:,\s*(.+))?$", t)
        if not m:
            raise RuntimeError(f"unparsed at {a:x}: {t}")
        op, d1, d2 = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        if op in ("push", "pop", "nop", "test", "cmp", "jmp", "je", "jne", "jle", "jge", "setg", "setl"):
            continue
        if re.match(r"^(BYTE|WORD|DWORD) PTR ", d1):  # store: operand recorded elsewhere
            continue
        if op == "mov":
            if re.fullmatch(REG, d1):
                if re.fullmatch(REG, d2):
                    v[d1] = v[d2]
                elif re.match(r"^(BYTE|WORD|DWORD) PTR ", d2):
                    v[d1] = loads.get(re.sub(r"\s+", " ", d2), f"mem[{d2}]")
                else:
                    v[d1] = int(d2, 0)
            continue
        if op == "xor" and d1 == d2:
            v[d1] = 0
        elif op == "shl":
            v[d1] = v[d1] << int(d2, 0)
        elif op == "add":
            v[d1] = v[d1] + v[d2]
        elif op == "sub":
            v[d1] = v[d1] - v[d2]
        elif op == "or" and d2 == "0xffffffff":
            v[d1] = -1
        elif op == "lea":
            mm = parse_mem(d2)
            tot = mm["const"] + sum(c * v.get(r, r) for r, c in mm.items() if r != "const")
            v[d1] = tot
        else:
            raise RuntimeError(f"shadow: unsupported op at {a:x}: {t}")
    return v


def main():
    load_text()
    idx = load_index()
    rep = []

    def P(s=""):
        print(s)
        rep.append(s)

    P("== M303: the post-counter read at 0x51e02c - index algebra and downstream consumer")
    P("== inputs: scratch/m574/text.txt (full .text dump, 150k+ insns) + ghidra_out/index.csv;")
    P("== zero box / zero /proc / zero gdb.  B19 lead CLOSED: `evidence/b19_visitcounter.txt:14`")

    # ---- S0 family census over the WHOLE dump ---------------------------------
    P("\n-- S0. every literal mention of 0x94eca8 / 0x94ed28 in the full .text dump --")
    fam = []
    for a in order:
        t = ins(a)
        if "0x94eca8" in t or "0x94ed28" in t:
            fam.append((a, "MAX" if "94eca8" in t else "CNT", t))
    for a, field, t in fam:
        P(f"  {a:#x} {field} {owner(idx, a):15s} {t}")
    p_eca8 = [x for x in fam if x[1] == "MAX"]
    p_ed28 = [x for x in fam if x[1] == "CNT"]

    # ---- S1 the fold chains, shadow-evaluated ---------------------------------
    P("\n-- S1. index algebra: CNT fold 0x51e013..0x51e02a and its byte-identical "
      "MAX-side copy 0x51dfd3..0x51dfe0 --")
    FOLD_CNT = [0x51E013, 0x51E015, 0x51E018, 0x51E024, 0x51E027, 0x51E02A]
    FOLD_MX = [0x51DFD3, 0x51DFD5, 0x51DFD8, 0x51DFDA, 0x51DFDD, 0x51DFE0]
    for a in FOLD_CNT + [0x51E02C]:
        P(f"  {a:#x}\t{enc(a):21s}\t{ins(a)}")
    st = shadow(FOLD_CNT, {"ebx": 1})
    K_cnt = st["eax"]
    st2 = shadow(FOLD_MX, {"ebx": 1})
    K_mx = st2["eax"]
    edx_k = shadow(FOLD_CNT[:3], {"ebx": 1})["edx"]
    P(f"  shadow(ebx=1): edx = {edx_k}*ebx -> eax = {K_cnt} (first copy) / {K_mx} (second copy)")
    P(f"  load form: [ecx + eax*4 + 0x94ed28] -> byte addr = site + {K_cnt * 4} * block "
      f"(scale 4 x {K_cnt})")
    K = K_cnt * 4
    P(f"  multiplier arithmetic: 65 = 64+1 | 131 = 1+2*65 | 2095 = 131*16-1 | "
      f"{K} = 2095*4 = 0x{K:x}")
    P(f"  the two 6-insn folds are BYTE-IDENTICAL encodings: {[enc(a) for a in FOLD_CNT] == [enc(a) for a in FOLD_MX]} "
      "(compiler rematerialized across the call at 0x51dffd; ebx survives it)")
    # sibling WORD array with the SAME block stride, scale *2 (width 2) instead of *4:
    WORD_FOLD = [0x51DF26, 0x51DF28, 0x51DF2B, 0x51DF2E, 0x51DF30, 0x51DF33, 0x51DF36,
                 0x51DF38, 0x51DF3B]
    ws = shadow(WORD_FOLD, {"ebx": 1}, loads={"DWORD PTR [ebp-0xc]": 1})
    P(f"  sibling 0x51df3d `inc WORD PTR [eax+0x94e8a8]`: shadow(ebx=1,site=1) eax = "
      f"{ws['eax']} = 2*(site + 4190*block) -> WORD array, row stride {ws['eax'] - 2} B "
      f"= {K}: SAME 8380-B block phase, entry width 2, scale *2 = width")
    P(f"  -> the *4 scale at 0x51e02c is NOT element width: byte array indexed in "
      f"dword units ({K}/4 = {K // 4}), scale 4 chosen so 2095 fits lea/shl/sub")

    # ---- S2 the B18 law fold in the SAME window (the rival) --------------------
    P("\n-- S2. rival R1: 'the 0x51e024-2a expression IS the 28-B stride (site*8-site)<<2' --")
    LAW = [0x51DFAC, 0x51DFAF, 0x51DFB1, 0x51DFB8, 0x51DFBA]
    for a in LAW + [0x51DFBD, 0x51DFCB]:
        P(f"  {a:#x}\t{enc(a):21s}\t{ins(a)}")
    K28 = shadow(LAW, {}, loads={"DWORD PTR [ebp-0xc]": 1})["esi"]
    P(f"  shadow(site=1): law esi = {K28} * site -> feeds DWORD [esi+0x989ce8] / "
      f"[esi+0x989cec] (the dword slot table, M299/M302)")
    P(f"  encodings: law lea SIB-scale-8 `{enc(0x51DFB1)}` vs byte-fold `{enc(0x51E024)}`; "
      f"law `shl esi,2` `{enc(0x51DFBA)}` vs byte-fold `shl eax,4` `{enc(0x51E027)}` + load scale *4")
    P(f"  law K = {K28} on esi/site | byte-fold K = {K} on eax/block -> equal? {K28 == K} "
      f"| R1 {'FAILS' if K28 != K else 'holds'}")

    # ---- S3 producers: site / block / edx --------------------------------------
    P("\n-- S3. producers of the three fold inputs (same function, from the dump) --")
    wr = [a for a in order if owner(idx, a) == "FUN_0051dcb0"
          and re.match(r"^mov    DWORD PTR \[ebp-0xc\],", ins(a))]
    P(f"  [ebp-0xc] (=site) in-function writers: {[hex(a) for a in wr]}")
    P(f"    0x51dd4f {ins(0x51DD4F)}   (cl <- tile byte 3; ecx zeroed at 0x51dd48)")
    P(f"    0x51dd57 {ins(0x51DD57)}")
    P(f"  0x51dfac {ins(0x51DFAC)} and 0x51e021 {ins(0x51E021)} both read it "
      f"-> same value pins esi (S2) AND the byte-fold base ecx (NOT the counter)")
    P(f"  block: 0x51ddff {ins(0x51DDFF)}")
    P_304 = shadow([0x51DDF2, 0x51DDF7, 0x51DDFA], {"eax": 1})
    P(f"    index fold 0x51ddf2-fa shadow(i=1): eax = {P_304['eax']} * i "
      f"== 0x130 = the base_array row stride M301 pinned (global 0x95da10 = NAMED base_array)")
    P(f"    sentinels: 0x51ddea {ins(0x51DDEA)} | 0x51ddbd {ins(0x51DDBD)} | "
      f"cell store 0x51df1f {ins(0x51DF1F)} | clamp 0x51df22 {ins(0x51DF22)} -> 0x51df24 {ins(0x51DF24)}")
    P(f"    => ebx into the fold is >= 0 always (clamp before 0x51dfd3); live upper bound UNKNOWN")
    P(f"  edx: 0x51e013 {ins(0x51E013)} -> a DERIVED COPY of ebx, not a coordinate")
    P(f"  (x,y are elsewhere: 0x51dff5 {ins(0x51DFF5)} / 0x51dff8 {ins(0x51DFF8)} pushed to the "
      f"predicate at 0x51dffd - never touch the fold)")

    # ---- S4 table geometry from the init loop ----------------------------------
    P("\n-- S4. per-call init 0x51dcb8-0x51dd17: the record geometry, derived twice --")
    for a, _, t in win(0x51DCB8, 0x51DD17):
        P(f"  {a:#x}\t{t}")
    base, stop, step = 0x94ECA8, 0x95F288, 0x20BC
    blocks, rem = divmod(stop - base, step)
    dstep, drem = divmod(0x98AAE8 - 0x989CE8, 0x1C)
    P(f"  byte family: rows from {base:#x} step {step:#x} until {stop:#x} -> blocks = {blocks} (rem {rem})")
    P(f"  CNT-MAX field gap: 0x94ed28-0x94eca8 = {0x94ED28 - 0x94ECA8} (matches the +0x80 in "
      f"`mov BYTE PTR [edx+ecx*1+0x80],0x0`)")
    P(f"  inner loop bound cmp ecx,0x80 -> 128 ENTRIES per field, store opcodes `c6` = mov BYTE, "
      f"ecx by 1 -> ENTRY WIDTH 1 B")
    P(f"  dword twin: 0x989ce8..0x98aae8 stride 0x1c -> slots = {dstep} (rem {drem}); "
      f"stores DWORD [eax],[eax+4] = {{MAX, CNT}}")
    P(f"  stride cross-derivation: init step {step} == fold K {K}? {step == K} "
      f"(two independent instrument legs)")

    # ---- S5 the RMW identity ----------------------------------------------------
    P("\n-- S5. 0x51e02c is the LOAD HALF of a byte RMW ++ (same predicate-gated block) --")
    for a in (0x51E007, 0x51E00D, 0x51E01A, 0x51E01B, 0x51E02C, 0x51E033, 0x51E03A,
              0x51E03C, 0x51E03E, 0x51E040):
        P(f"  {a:#x}\t{enc(a):21s}\t{ins(a)}")
    sib_disp = lambda a: enc(a).split()[2:]
    P(f"  operand tails (SIB+disp32, after opcode+modrm): 0x51e02c {sib_disp(0x51E02C)} vs "
      f"0x51e033 {sib_disp(0x51E033)} -> SAME address expression? {sib_disp(0x51E02C) == sib_disp(0x51E033)}")
    P(f"  and vs the MAX-side lea 0x51dfe2 {sib_disp(0x51DFE2)} -> same SIB {sib_disp(0x51DFE2)[0]} "
      f"(scale 4, base ecx, index eax*4)")
    seq = [a for a, _, _ in win(0x51E02C, 0x51E03E)]
    branch = [a for a in seq if re.match(r"^j\w+\b", ins(a))]
    P(f"  branch instructions between load and store: {[hex(a) for a in branch]} -> store unconditional")
    flg = [a for a, _, _ in win(0x51E03C, 0x51E040)
           if re.match(r"^(test|cmp|inc|dec|add|sub|or|and|xor)\b", ins(a))]
    P(f"  flag-writers in [0x51e03c..0x51e040]: {[(hex(a), ins(a).split()[0]) for a in flg]} "
      f"-> 0x51e040 `je` tests `test ebx,ebx` flags, NOT the byte")
    dlc = [(a, ins(a)) for a, _, _ in win(0x51E03A, 0x51E06C)
           if re.search(r"\bdl\b|\bedx\b", ins(a))]
    P(f"  every dl/edx mention 0x51e03a-0x51e06c: {[(hex(a), t) for a, t in dlc]}")
    P(f"  -> the incremented byte's ONLY consumers are the inc + the store; edx is then "
      f"reloaded from [ebp-0x8] (y) for the call: dl is DEAD after 0x51e03e")

    # ---- S6 external readers: first downstream consumer -------------------------
    P("\n-- S6. every family reader and the first instruction that consumes the loaded value --")
    readers = [(0x51DFE2, "ecx"), (0x50E4FB, "al"), (0x5583C0, "bl"), (0x563C59, "cl"),
               (0x5642B4, "al"), (0x5646E6, "dl"), (0x56B818, "al"), (0x4F946D, "al")]
    rows6 = []
    DW = {"al": "eax", "bl": "ebx", "cl": "ecx", "dl": "edx"}
    for a, reg in readers:
        reg32 = DW.get(reg, reg)
        cons = None
        for b in [x for x in order if a < x <= a + 0x40]:
            t = ins(b)
            if re.match(r"^(cmp|test)\b", t) and re.search(rf"\b({reg}|{reg32})\b", t):
                cons = (b, t, "cmp/test")
                break
            if re.search(r"PTR \[[^\]]*\b" + reg + r"\b", t):
                cons = (b, t, "memory-read")
                break
        rows6.append((a, owner(idx, a), ins(a), cons))
    for a, fn, t, c in rows6:
        P(f"  {a:#x} {fn:15s} {t}")
        if c:
            P(f"           -> {c[0]:#x} [{c[2]}] {c[1]}")
        else:
            P("           -> no consumer within 0x40 B")
    n_cmp = sum(1 for r in rows6 if r[3] and r[3][2] == "cmp/test")

    # ---- S6b writers to the family/twin: window scan of FUN_0051dcb0 ------------
    P("\n-- S6b. every store to the byte family, the dword twin, and the WORD sibling --")
    FAMOPS = {r"BYTE PTR \[edx\+ecx\*1\]$", r"BYTE PTR \[edx\+ecx\*1\+0x80\]$",
              r"WORD PTR \[eax\]$", r"WORD PTR \[eax\+0x100\]$", r"WORD PTR \[eax\+0x200\]$",
              r"WORD PTR \[eax\+0x300\]$", r"WORD PTR \[eax\+0x94e8a8\]$",
              r"DWORD PTR \[esi\+0x989ce8\]$", r"DWORD PTR \[esi\+0x989cec\]$",
              r"BYTE PTR \[ecx\]$", r"BYTE PTR \[eax\]$"}
    stores = []
    for a, _, t in win(0x51DCC1, 0x51E03E):
        m = re.match(r"^(mov|inc)\s+(.+)$", t)
        if not m:
            continue
        dest = m.group(2).split(",")[0].strip()
        if any(re.search(pat, dest) for pat in FAMOPS):
            stores.append((a, t))
    for a, t in stores:
        P(f"  {a:#x} {t}")
    inscope = {0x51DF3D, 0x51DFCB, 0x51DFF3, 0x51E01B, 0x51E03E}
    n_init = sum(1 for a, _ in stores if a <= 0x51DCE7)
    P(f"  -> all {len(stores)} stores inside FUN_0051dcb0; init-zero {n_init}; "
      f"per-tile updates {sorted(hex(x) for x in inscope)} all present: "
      f"{inscope <= {a for a, _ in stores}}")

    # ---- S7 dispatch after the store ------------------------------------------
    P("\n-- S7. post-store dispatch (branching on block, not on the byte) --")
    calls = [(a, t) for a, _, t in win(0x51E042, 0x51E11D) if re.match(r"^call\b", t)]
    for a, t in calls:
        tgt = int(t.split()[-1], 16)
        P(f"  {a:#x} {t}  -> {owner(idx, tgt)} (n_callers={dict((int(d['addr'],16), d['n_callers']) for d in csv.DictReader(open(INDEX))).get(tgt, '?')})")
    P(f"  mask 0x51e042-49: {ins(0x51E042)} / {ins(0x51E047)} / {ins(0x51E049)} -> 1<<block")
    P(f"  gates both legs: {ins(0x51E04E)} | {ins(0x51E053)} | {ins(0x51E05F)} "
      f"(tile flag byte +4 bit block, ds:0x985b10, ds:0x985aec>3)")
    P(f"  ebx==0 leg walks the 8 block rows of the byte field @0x950664: {ins(0x51E083)} / "
      f"advance {ins(0x51E10B)} / bound {ins(0x51E111)}")
    P(f"  ebx!=0 leg: {ins(0x51E076)} -> FUN_0056d480(block,3,1,x,y); ebx==0 leg per-row: "
      f"call 0x56d630(block,3,x,y) + row finder 0x4e37f0 then FUN_0056d480(block,3,1,x,y)")

    # ---- S8 two-instrument disagreement -----------------------------------------
    P("\n-- S8. the disp-census blind spot (skill: register-after-lea stores evade store greps) --")
    P(f"  scripts/name_global.py 0x94ed28 --disp classifies the 3 literal mentions as READS, "
      f"writes = 0; it is correct about LITERAL writes only:")
    lit_write = [a for a in order if re.match(r"^(mov|inc)\s+(BYTE|WORD|DWORD) PTR \[[^]]*0x94ed28", ins(a))]
    P(f"  literal-disp writes to 0x94ed28 anywhere in .text: {len(lit_write)}")
    P(f"  actual writer: 0x51e03e `{ins(0x51E03E)}` through 0x51e033 `{ins(0x51E033)}` (lea) "
      f"+ the init store `[edx+ecx*1+0x80]` through 0x51dcb8 `mov edx,0x94eca8` "
      f"- two pointer forms; the RMW store exists and the disp census cannot see it")

    # ---- S9 what stays UNKNOWN ---------------------------------------------------
    P("\n-- S9. DECLARED UNKNOWN (not settled by this census) --")
    P("  1. live VALUES of the byte CNT/MAX fields and the 8 block bytes (no /proc in this "
      "fire; M302 pinned only the dword twin 0x989ce8).")
    P("  2. the live upper bound of the block byte (BYTE[304*i+0x95da14]): the fold and the "
      "8-row init imply block < 8, but no static bound-check on the byte is in the window "
      "(only the -1 sentinel clamp).")
    P("  3. field identity inside one 8380-B record: offsets 0(MAX B) 128(CNT B) "
      f"256..1023(word fields zeroed by init) and siblings reached by stride {K} "
      "(dword @+3140 witness 0x94f4ec, word @+8636 witness 0x950a64, byte @+7612 witness 0x950664, "
      "word @+0 witness 0x94e8a8) - widths witnessed, semantics NOT named here.")
    P("  4. semantics of FUN_0056d480 / FUN_0056d630 / ds:0x985b10 / ds:0x985aec (printed "
      "call+gates; no decode done) - the byte++ itself NEVER gates them.")
    P("  5. save-carry vs rebuild of the BYTE family: the per-call init at function entry "
      "zeroes it, so at least after this function runs the values are rebuilt, but whether "
      "a save round-trips them is OUTSIDE this window (M302's twin-table OPEN persists).")

    # ===================== RIVALS (must fail on printed numbers) ==================
    P("\n-- R. rival models evaluated against the printed tables --")
    P(f"  R1 'the 0x51e024-2a chain is B18's 28-B law': law K={K28} vs fold K={K} -> FAIL ({K28 != K}), "
      f"different registers (esi vs eax) and encodings (S1/S2).")
    P(f"  R2 'edx and ebx are two coordinates (x,y)': edx produced by `mov edx,ebx` 0x51e013 "
      f"(shadow {edx_k}=1*ebx) and x,y are the [ebp-0x10]/[ebp-0x8] pushes at 0x51dffd - FAIL.")
    P(f"  R3 '0x51e02c is a pure read that gates the je 0x51e040': je tests flags of "
      f"`test ebx,ebx` 0x51e03c (only flag-writer before it); the byte is stored back at "
      f"0x51e03e; dl dead after -> FAIL.")
    P(f"  R4 'the *4 scale means a dword table, entry width 4': the sibling word array uses "
      f"scale *2 at width 2 with the SAME stride {K}; init stores are `mov BYTE` by +1 and "
      f"all 11 corpus readers are BYTE PTR -> entry width 1 B, *4 is multiplier placement "
      f"({K}/4 = {K // 4} index units) -> FAIL.")

    # ===================== ASSERTIONS =============================================
    A = []
    A.append(len(fam) == 11 and len(p_eca8) == 8 and len(p_ed28) == 3
             and {owner(idx, a) for a, _, _ in fam} == {"FUN_004f6030", "FUN_0050d140",
                                                        "FUN_0051dcb0", "FUN_00556690",
                                                        "FUN_0055f650"})
    A.append(K_cnt == K_mx == 2095 and K == 8380 == 0x20BC and edx_k == 65
             and [enc(a) for a in FOLD_CNT] == [enc(a) for a in FOLD_MX])
    A.append(K28 == 28 and K != K28 and enc(0x51DFB1).startswith("8d 34")
             and enc(0x51E024).startswith("8d 04"))
    A.append(wr == [0x51DD57] and P_304["eax"] == 304)
    A.append(blocks == 8 and rem == 0 and (0x94ED28 - 0x94ECA8) == 128
             and dstep == 128 and drem == 0 and step == K)
    A.append(sib_disp(0x51E02C) == sib_disp(0x51E033) and branch == []
             and flg == [0x51E03C]
             and all(not re.match(r"^(cmp|test)", t) for _, t in dlc))
    A.append(all(r[3] for r in rows6) and n_cmp == len(rows6) - 1)  # the lea row = memory-read
    A.append(n_init == 6 and inscope <= {a for a, _ in stores}
             and all(owner(idx, a) == "FUN_0051dcb0" for a, _ in stores))
    A.append({t.split()[-1] for _, t in calls} == {"0x56d480", "0x56d630", "0x4e37f0"})
    A.append(lit_write == [])
    names = ["A1_corpus", "A2_fold", "A3_rival28", "A4_producers", "A5_geometry",
             "A6_rmw", "A7_consumers", "A8_stores", "A9_dispatch", "A10_ptrform"]
    P("\n===================")
    for n, ok in zip(names, A):
        P(f"{n:14s} {'PASS' if ok else 'FAIL'}")
    n_pass = sum(A)
    P(f"{'RESULT':14s} {'PASS M303' if n_pass == 10 else 'FAIL M303'}: {n_pass}/10 "
      f"(zero box, zero /proc, zero gdb)")
    with open(OUT, "w") as f:
        f.write("\n".join(rep) + "\n")
    sys.exit(0 if n_pass == 10 else 1)


if __name__ == "__main__":
    main()
