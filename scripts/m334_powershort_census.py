#!/usr/bin/env python3
"""M334 (chain2): the upkeep-FAILURE branch of FUN_004f47f0 — what is removed, what ENERGY
becomes, what is announced. Pick (x7) of NEXT_PROMPT's OPEN-LEADS (the row M333 printed but
did NOT gate). STATIC, zero box, zero /proc, zero gdb. Reuses M326's reviewed .text cache.

THE OLD CLAIM UNDER TEST (docs/named-archive-m32-m84e.md:268, conf H "pseudocode"):
  "insufficient funds => auto-SELL a facility (bitmap bit cleared,
   refund = 0x4e40a0 x refund table 0x984d44[item*0xc], POWERSHORT warning)"

WHAT THE BYTES SAY (every number below is COMPUTED by this file, printed, then asserted):
  FUN_004f47f0 charges item upkeep per base (M330/M333): ENERGY -= cost @0x4f4952 and
  block+0x300 += cost @0x4f4962 through one 8380*owner fold. It then RE-READS ENERGY and
  tests it against 0 (@0x4f4968-70, jge -> next item). The negative side is a THREE-WAY
  dispatch:
    A @0x4f4976  cmp [block+0x8],1 / jg      -> ENERGY := 0 @0x4f497f
    B @0x4f498a  cmp [base_rec+0x50],-item   -> ENERGY := 0 @0x4f4999
    C @0x4f49a4  the removal path: clear the item's bit in the CURRENT base's facility map
                 (304*ds:0x68cbb0 + byte_index + 0x95da9c), then
                 ENERGY := FUN_004e40a0(owner,1,-1) * row[item]+12 @0x4f4a0b,
                 FUN_006265a2(1, row[item]+0, -1, -1) @0x4f4a11,
                 FUN_0048f100("POWERSHORT",0x10000,0xe,"genwarning_sm.pcx",0) @0x4f4a29.
  block+0x8 is the faction's EFFECTIVE DIFFICULTY: its only two destination-named writers are
  0x59eed6 (faction create: ds:0x985aec for a human, the immediate 3 for the AI) and 0x57ef57
  (save/load: a sign-extended byte). So branch A means "on the easiest difficulty the shortfall
  just clamps ENERGY to 0" — the auto-sell is difficulty-gated.
  The store at 0x4f4a0b is a MOV of a product with ZERO reads of ENERGY on the path: the old
  row's word "refund" (an addition) is REFUTED; the multiplication is CONFIRMED.
  base_rec+0x50 is the production-queue HEAD (archived live H: named-archive-m32-m84e.md:312,
  negative = facility id) — so branch B protects the facility the base is currently building.

Acceptance: python3 -u scripts/m334_powershort_census.py -> TABLE FIRST, then gates, digest;
a re-run must be byte-identical.  Mutants: scripts/m334_mutate.py (--selftest runs them).
Patch env: M334_PATCH="addr|mnemonic ops" applied to m326.INS after import (the instrument
prints `patches applied: n/m` as contact proof).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326  # noqa: E402

INS, ADDRS, AIDX = m326.INS, m326.ADDRS, m326.AIDX
owner, split_ops = m326.owner, m326.split_ops
pe_cstr = m326.pe_cstr
STORE_MN = m326.STORE_MN

FN = 0x4F47F0                    # FUN_004f47f0(cur_base) facility-upkeep charge loop
LOOP_TOP, LOOP_BOTTOM = 0x4F480B, 0x4F4A34
NEG_TEST = 0x4F4970              # jge LOOP_BOTTOM when ENERGY >= 0
CLAMP_A, CLAMP_B, REMOVAL = 0x4F4976, 0x4F498A, 0x4F49A4
E_RMW, S_RMW = 0x4F4952, 0x4F4962
E_STORE = (0x4F497F, 0x4F4999, 0x4F4A0B)
MAPPER, FACTOR, SLOTTER, MEMO = 0x507410, 0x4E40A0, 0x6265A2, 0x48F100
ITEM_ROW0, ROW = 0x984D38, 48    # row+12 = 0x984d44 (the "refund"/price field), +16 = upkeep
BLKBASE, BLKSTRIDE = 0x94D430, 0x20BC
ENERGY_OFF, SPEND_OFF, DIFF_OFF = 0x220, 0x300, 0x8
ENERGY_VA, SPEND_VA, DIFF_VA = BLKBASE + ENERGY_OFF, BLKBASE + SPEND_OFF, BLKBASE + DIFF_OFF
BASEMAP, BASE_STRIDE = 0x95DA9C, 304
CURR_BASE, CURR_REC = 0x68CBB0, 0x8F0D60
QUEUE_HEAD_OFF = 0x50
STR_LABEL, STR_ICON = 0x68D24C, 0x68D238
DIFF_GLOB, HUMAN_MASK = 0x985AEC, 0x985B10
AI_DIFF = 3
EV = os.environ.get("M334_EVIDENCE_ROOT", ROOT)

_npatch = 0


def apply_patch():
    """M334_PATCH='addr|mn ops;addr|mn ops' — the mutation harness's contact surface."""
    global _npatch
    spec = os.environ.get("M334_PATCH", "")
    if not spec:
        return 0, 0
    want = [x for x in spec.split(";") if x.strip()]
    n = 0
    for item in want:
        a, _, rest = item.partition("|")
        addr = int(a, 16)
        mn, _, ops = rest.strip().partition(" ")
        if addr in INS:
            INS[addr] = (mn, ops)
            n += 1
    _npatch = n
    return n, len(want)


# ---------------------------------------------------------------- operand machinery
BASE_REG = {"eax": "eax", "al": "eax", "ah": "eax", "ax": "eax",
            "ebx": "ebx", "bl": "ebx", "bh": "ebx", "bx": "ebx",
            "ecx": "ecx", "cl": "ecx", "ch": "ecx", "cx": "ecx",
            "edx": "edx", "dl": "edx", "dh": "edx", "dx": "edx",
            "esi": "esi", "si": "esi", "edi": "edi", "di": "edi",
            "ebp": "ebp", "bp": "ebp", "esp": "esp", "sp": "esp"}
TERM_RE = re.compile(r"[+-]?\s*(?:0x[0-9a-fA-F]+|\w+(?:\s*\*\s*\d+)?)")


def mem_parts(op):
    """'[ecx+edx*1+0x95da9c]' -> ({'ecx':1,'edx':1}, 0x95da9c); None if not memory."""
    m = re.search(r"\[(.*)\]", op)
    if not m:
        return None
    regs, disp = {}, 0
    for t in TERM_RE.findall(m.group(1)):
        t = t.strip()
        sign = 1
        if t.startswith("-"):
            sign, t = -1, t[1:].strip()
        elif t.startswith("+"):
            t = t[1:].strip()
        mm = re.fullmatch(r"0x[0-9a-fA-F]+", t)
        if mm:
            disp += sign * int(t, 16)
            continue
        mm = re.fullmatch(r"(\w+)(?:\s*\*\s*(\d+))?", t)
        if mm:
            regs[mm.group(1)] = regs.get(mm.group(1), 0) + sign * int(mm.group(2) or 1)
    return regs, disp


def strip_ptr(op):
    return re.sub(r"^\s*(dword|byte|word|fword|ptr)\s+", "", op.strip(), flags=re.I)


def resolve(op, st):
    """affine value (a, b) of an operand under state st, or None."""
    op = strip_ptr(op)
    if op in BASE_REG:
        return st.get(BASE_REG[op])
    mm = re.fullmatch(r"0x[0-9a-fA-F]+", op)
    if mm:
        return (0, int(op, 16))
    mm = re.fullmatch(r"-?\d+", op)
    if mm:
        return (0, int(op))
    if op.startswith("ds:") or re.fullmatch(r"0x[0-9a-fA-F]+", op):
        return None
    mp = mem_parts(op)
    if mp is None:
        return None
    regs, disp = mp
    a = b = 0
    for r, sc in regs.items():
        v = st.get(BASE_REG.get(r, r))
        if v is None:
            return None
        a += v[0] * sc
        b += v[1] * sc
    return (a, b + disp)


def step(st, mn, ops, a):
    """advance the affine state by one instruction (unknown -> None)."""
    parts = split_ops(ops)
    d = parts[0].strip() if parts else ""
    dr = BASE_REG.get(strip_ptr(d)) if not d.startswith("[") else None
    if mn == "lea" and len(parts) == 2:
        st[dr] = resolve(parts[1], st) if dr else None
    elif mn in ("mov", "movzx", "movsx") and len(parts) == 2:
        v = resolve(parts[1], st)
        if dr:
            st[dr] = v
    elif mn == "xor" and len(parts) == 2 and strip_ptr(parts[0]) == strip_ptr(parts[1]):
        if dr:
            st[dr] = (0, 0)
    elif mn in ("shl", "sal") and len(parts) == 2:
        k = resolve(parts[1], st)
        v = st.get(dr) if dr else None
        if dr:
            st[dr] = (v[0] << k[1], v[1] << k[1]) if (v and k and k[0] == 0) else None
    elif mn == "shr" and len(parts) == 2:
        if dr:
            st[dr] = None
    elif mn in ("add", "sub") and len(parts) == 2:
        v, w = st.get(dr), resolve(parts[1], st)
        if dr:
            if v and w:
                st[dr] = (v[0] + w[0], v[1] + w[1]) if mn == "add" else (v[0] - w[0], v[1] - w[1])
            else:
                st[dr] = None
    elif mn in ("inc", "dec") and len(parts) == 1:
        v = st.get(dr)
        if dr:
            st[dr] = (v[0], v[1] + (1 if mn == "inc" else -1)) if v else None
    elif mn == "neg" and len(parts) == 1:
        v = st.get(dr)
        if dr:
            st[dr] = (-v[0], -v[1]) if v else None
    elif mn == "call":
        for r in ("eax", "ecx", "edx"):
            st[r] = None
    elif dr:
        st[dr] = None
    return a


def affine(lo, hi, seeds):
    st = {BASE_REG.get(k, k): v for k, v in seeds.items()}
    for a in range(lo, hi + 1):
        if a in INS:
            step(st, INS[a][0], INS[a][1], a)
    return st


def push_args(call_addr, n):
    """the last n `push` operands before call_addr, in cdecl order (nearest first)."""
    out, i = [], AIDX[call_addr] - 1
    while i >= 0 and len(out) < n:
        a = ADDRS[i]
        if a < FN or a > LOOP_BOTTOM:
            break
        mn, ops = INS[a]
        if mn == "push":
            out.append((a, strip_ptr(ops)))
        elif mn == "call":
            break
        i -= 1
    return out


def reads_of(lo, hi, va):
    """instructions in [lo,hi] whose NON-destination operand text names `va`."""
    hits = []
    for a in range(lo, hi + 1):
        if a not in INS:
            continue
        mn, ops = INS[a]
        if f"0x{va:x}" not in ops:
            continue
        parts = split_ops(ops)
        for p in parts[1:] if (mn in STORE_MN and mn not in ("cmp", "test")) else parts:
            if f"0x{va:x}" in p:
                hits.append((a, mn, ops))
                break
    return hits


def stores_naming(va):
    """.text stores whose DESTINATION operand text names `va` (absolute or folded)."""
    w, r = [], []
    for a in ADDRS:
        mn, ops = INS[a]
        if f"0x{va:x}" not in ops:
            continue
        parts = split_ops(ops)
        if mn in STORE_MN and mn not in ("cmp", "test") and f"0x{va:x}" in parts[0]:
            w.append((a, mn, ops, str(owner(a))))
        elif mn == "lea" and f"0x{va:x}" in parts[1]:
            r.append((a, mn, ops, str(owner(a))))
    return w, r


def folded_stores_to(off):
    """stores to [R+off] where R's nearest def in the same function is a fold naming BLKBASE
    (the hole an operand-text grep for the absolute VA cannot see: `lea R,[k*4+0x94d430]`
    then `mov [R+8],v`). Path-insensitive, 60-instruction def walk, stops at any other write."""
    hits = []
    for a in ADDRS:
        mn, ops = INS[a]
        if mn not in STORE_MN or mn in ("cmp", "test"):
            continue
        parts = split_ops(ops)
        mp = mem_parts(parts[0]) if parts else None
        if not mp:
            continue
        regs, disp = mp
        if disp != off or len(regs) != 1:
            continue
        r = list(regs)[0]
        if r not in ("eax", "ebx", "ecx", "edx", "esi", "edi"):
            continue
        fa = owner(a)
        i = AIDX[a]
        for _ in range(60):
            i -= 1
            if i < 0:
                break
            b = ADDRS[i]
            if owner(b) != fa:
                break
            bm, bo = INS[b]
            d = strip_ptr(split_ops(bo)[0]) if split_ops(bo) else ""
            if d == r:
                if f"0x{BLKBASE:x}" in bo:
                    hits.append((a, mn, ops, b, bm, bo))
                break
    return hits


def main():
    npatch, nwant = apply_patch()
    T = []

    def P(s):
        T.append(s)
        print(s)

    P(f"patches applied: {npatch}/{nwant}")
    P("== M334 TABLE (computed, then gated) ==")

    # ---- G1 machinery: the two folds + the ENERGY/SPEND RMW pair
    st = affine(0x4F48C8, 0x4F48CB, {"esi": (1, 0)})
    upkeep_fold = st.get("eax")
    upkeep_off = None
    mp = mem_parts(INS[0x4F48CE][1])
    if mp:
        upkeep_off = mp[1] - ITEM_ROW0
    st = affine(0x4F4938, 0x4F4947, {"ebx": (1, 0)})
    blk_fold = st.get("edi")
    rmw = {}
    for tag, rd, op, wr, want in (("ENERGY", 0x4F494A, 0x4F4950, 0x4F4952, ENERGY_OFF),
                                  ("SPEND", 0x4F4958, 0x4F495E, 0x4F4962, SPEND_OFF)):
        off_r = (mem_parts(INS[rd][1]) or ({}, None))[1]
        off_w = (mem_parts(INS[wr][1]) or ({}, None))[1]
        off_r = off_r - BLKBASE if off_r is not None else None
        off_w = off_w - BLKBASE if off_w is not None else None
        rmw[tag] = (off_r, off_w, INS[op][0], want)
    e_rmw_off, s_rmw_off = rmw["ENERGY"][0], rmw["SPEND"][0]
    P(f"G1 upkeep fold: item*{upkeep_fold[0] if upkeep_fold else '?'} @0x4f48cb; "
      f"table field +{upkeep_off} (row0={ITEM_ROW0:#x})")
    P(f"G1 block fold: owner*{blk_fold[0] if blk_fold else '?'} @0x4f4947 "
      f"(BLKSTRIDE={BLKSTRIDE:#x}={BLKSTRIDE})")
    for tag, (rd, op, wr) in (("ENERGY", (0x4F494A, 0x4F4950, 0x4F4952)),
                              ("SPEND", (0x4F4958, 0x4F495E, 0x4F4962))):
        off_r, off_w, mnm, want = rmw[tag]
        P(f"G1 {tag} RMW read@{rd:#x} {INS[rd][0]} {INS[rd][1]} -> block+{off_r:#x}; "
          f"op@{op:#x} {mnm} {INS[op][1]}; store@{wr:#x} {INS[wr][0]} {INS[wr][1]} -> "
          f"block+{off_w:#x} (want +{want:#x})")

    # ---- G2 machinery: the negative test + the three-way dispatch
    eax_def = None
    for a in range(NEG_TEST, NEG_TEST - 20, -1):
        if a in INS and INS[a][0] == "xor" and "eax" in INS[a][1]:
            eax_def = a
            break
    cmpA = INS[CLAMP_A]
    mpA = mem_parts(cmpA[1])
    offA = mpA[1] - BLKBASE if mpA else None
    immA = re.findall(r"0x[0-9a-f]+", cmpA[1])[-1]
    jgA_addr = ADDRS[AIDX[CLAMP_A] + 1]
    jgA = INS[jgA_addr]
    cmpB = INS[0x4F4994]
    mpB = mem_parts(cmpB[1])
    offB = mpB[1] if mpB else None
    P(f"G2 negative test @{0x4F4968:#x} {INS[0x4F4968][0]} {INS[0x4F4968][1]} / "
      f"{INS[0x4F496E][0]} {INS[0x4F496E][1]} / {INS[NEG_TEST][0]} {INS[NEG_TEST][1]} "
      f"-> {LOOP_BOTTOM:#x}; zero-source {INS[eax_def][0]} {INS[eax_def][1]} @{eax_def:#x}")
    P(f"G2 branch A @{CLAMP_A:#x} {cmpA[0]} {cmpA[1]} (block+{offA:#x}, imm {immA}) "
      f"-> {jgA[0]} {jgA[1]}; clamp store @{E_STORE[0]:#x} {INS[E_STORE[0]][0]} {INS[E_STORE[0]][1]}")
    P(f"G2 branch B @{CLAMP_B:#x} {INS[0x4F4990][0]} {INS[0x4F4990][1]} / "
      f"{INS[0x4F4992][0]} {INS[0x4F4992][1]} / {cmpB[0]} {cmpB[1]} (rec+{offB:#x}); "
      f"clamp store @{E_STORE[1]:#x} {INS[E_STORE[1]][0]} {INS[E_STORE[1]][1]}")

    # ---- G3 machinery: block+0x8's writers
    w8, lea8 = stores_naming(DIFF_VA)
    P(f"G3 block+0x8 ({DIFF_VA:#x}) destination-named STORES in .text: {len(w8)}; "
      f"lea-absolute copies: {len(lea8)}")
    for a, mn, ops, fn in w8:
        P(f"G3   W {a:#x} {mn} {ops}  [{fn}]")
    for a, mn, ops, fn in lea8:
        P(f"G3   L {a:#x} {mn} {ops}  [{fn}]")
    create_defs = [(a, INS[a][0], INS[a][1]) for a in range(0x59EEC3, 0x59EED7)
                   if a in INS and INS[a][0] == "mov" and INS[a][1].startswith("eax")]
    P(f"G3 create-path defs of eax reaching {0x59EED6:#x}: "
      + "; ".join(f"{a:#x} {m} {o}" for a, m, o in create_defs))
    load_def = [(a, INS[a][0], INS[a][1]) for a in range(0x57EF30, 0x57EF58)
                if a in INS and INS[a][1].startswith("edx")]
    st = affine(0x57EF37, 0x57EF50, {"eax": (1, 0)})
    load_fold = st.get("ecx")
    P(f"G3 save/load-path def of edx: " + "; ".join(f"{a:#x} {m} {o}" for a, m, o in load_def)
      + f"; index fold ecx = {load_fold[0]}*eax, store scale 4 "
      f"-> {load_fold[0] * 4 if load_fold else '?'}")
    folded8 = folded_stores_to(DIFF_OFF)
    P(f"G3 folded-pointer stores to block+{DIFF_OFF:#x} (a def of the base register naming "
      f"{BLKBASE:#x} within 60 instructions): {len(folded8)} -> "
      + "; ".join(f"{a:#x} {m} {o} <- {b:#x} {bm} {bo}" for a, m, o, b, bm, bo in folded8[:8]))

    # ---- G4 machinery: the two mapper calls + the bit test vs the bit clear
    chg_fold = affine(0x4F482B, 0x4F4834, {"edi": (1, 0)}).get("ecx")
    rem_fold = affine(0x4F49BE, 0x4F49CB, {"esi": (1, 0)}).get("eax")
    chg_read = INS[0x4F4837]
    rem_mat = INS[0x4F49D1]
    rem_read = INS[0x4F49DA]
    rem_store = INS[0x4F49E1]
    chg_and = [(a, INS[a][0], INS[a][1]) for a in range(0x4F4838, 0x4F4860)
               if a in INS and INS[a][0] == "and"]
    P(f"G4 charge mapper call @{0x4F4823:#x} args(nearest-first) "
      + " ".join(f"{a:#x}:{o}" for a, o in push_args(0x4F4823, 3)))
    P(f"G4 removal mapper call @{0x4F49B6:#x} args(nearest-first) "
      + " ".join(f"{a:#x}:{o}" for a, o in push_args(0x4F49B6, 3)))
    P(f"G4 base-map fold: charge {chg_fold[0] if chg_fold else '?'}*base @0x4f4834; "
      f"removal {rem_fold[0] if rem_fold else '?'}*base @0x4f49cb; both + byte_index + {BASEMAP:#x}")
    P(f"G4 charge TEST {chg_read[0]} {chg_read[1]} then "
      + "; ".join(f"{a:#x} {m} {o}" for a, m, o in chg_and))
    P(f"G4 removal CLEAR: {INS[0x4F49D8][0]} {INS[0x4F49D8][1]} / {rem_read[0]} {rem_read[1]} / "
      f"{INS[0x4F49DF][0]} {INS[0x4F49DF][1]} / {rem_store[0]} {rem_store[1]}")

    # ---- G5 machinery: ENERGY := FACTOR * row+12, with no ENERGY read on the path
    item_fold = affine(0x4F49DC, 0x4F49EF, {"esi": (1, 0)}).get("esi")
    mp44 = mem_parts(INS[0x4F49F7][1])
    off44 = mp44[1] - ITEM_ROW0 if mp44 else None
    e_reads = reads_of(REMOVAL, 0x4F4A0A, ENERGY_VA)
    P(f"G5 item fold for the price read: {item_fold[0] if item_fold else '?'}*item @0x4f49ef; "
      f"imul @{0x4F49F7:#x} {INS[0x4F49F7][0]} {INS[0x4F49F7][1]} -> row+{off44}")
    P(f"G5 factor call @{0x4F49F2:#x} call {INS[0x4F49F2][1]} args(nearest-first) "
      + " ".join(f"{a:#x}:{o}" for a, o in push_args(0x4F49F2, 3)))
    P(f"G5 owner-byte source: {INS[0x4F49E3][0]} {INS[0x4F49E3][1]} / {INS[0x4F49E9][0]} "
      f"{INS[0x4F49E9][1]} / {INS[0x4F49EB][0]} {INS[0x4F49EB][1]}")
    P(f"G5 ENERGY store @{E_STORE[2]:#x} {INS[E_STORE[2]][0]} {INS[E_STORE[2]][1]}; "
      f"reads of block+{ENERGY_OFF:#x} in [{REMOVAL:#x},{0x4F4A0B:#x}) = {len(e_reads)}")

    # ---- G6 machinery: the announcement
    P(f"G6 slot-setter @{0x4F4A11:#x} call {INS[0x4F4A11][1]} args(nearest-first) "
      + " ".join(f"{a:#x}:{o}" for a, o in push_args(0x4F4A11, 4)))
    P(f"G6 memo @{0x4F4A29:#x} call {INS[0x4F4A29][1]} args(nearest-first) "
      + " ".join(f"{a:#x}:{o}" for a, o in push_args(0x4F4A29, 5)))
    P(f"G6 row+0 read @{0x4F49FE:#x} {INS[0x4F49FE][0]} {INS[0x4F49FE][1]}")
    P(f"G6 PE strings: {STR_LABEL:#x}={pe_cstr(STR_LABEL)!r}  {STR_ICON:#x}={pe_cstr(STR_ICON)!r}")

    # ---- G7 machinery: no loop exit; the single base-map store; the queue-head census
    tail = [(a, INS[a][0], INS[a][1]) for a in range(0x4F4A2E, LOOP_BOTTOM + 8) if a in INS]
    P("G7 tail after the memo call: " + "; ".join(f"{a:#x} {m} {o}" for a, m, o in tail))
    # the 304*base + BASEMAP fold is MATERIALIZED at these sites (the address is computed into
    # a register, so a "store naming BASEMAP" grep would find nothing — materialization census)
    mats = [(a, INS[a][0], INS[a][1]) for a in range(FN, LOOP_END + 1)
            if a in INS and f"0x{BASEMAP:x}" in INS[a][1]]
    P(f"G7 sites inside FUN_004f47f0 materializing the {BASEMAP:#x} map address: {len(mats)} -> "
      + "; ".join(f"{a:#x} {m} {o}" for a, m, o in mats))
    eax_writes = [(a, INS[a][0], INS[a][1]) for a in range(0x4F49D2, 0x4F49E1)
                  if a in INS and re.match(r"^(e?ax|al|ah)\b", strip_ptr(split_ops(INS[a][1])[0]))]
    P(f"G7 writes to eax between the fold @{0x4F49D1:#x} and the store @{0x4F49E1:#x}: "
      f"{len(eax_writes)} -> " + "; ".join(f"{a:#x} {m} {o}" for a, m, o in eax_writes))
    qh = []
    for a in ADDRS:
        mn, ops = INS[a]
        hit = None
        for p in split_ops(ops):
            mp = mem_parts(p)
            if not mp:
                continue
            regs, disp = mp
            if disp == QUEUE_HEAD_OFF and len(regs) == 1 and list(regs)[0] in (
                    "eax", "ebx", "ecx", "edx", "esi", "edi"):
                hit = list(regs)[0]
                break
        if not hit:
            continue
        fa = owner(a)
        i = AIDX[a]
        for _ in range(60):
            i -= 1
            if i < 0:
                break
            b = ADDRS[i]
            if owner(b) != fa:
                break
            bm, bo = INS[b]
            if f"0x{CURR_REC:x}" in bo and bm in ("mov", "lea") and strip_ptr(split_ops(bo)[0]) == hit:
                qh.append((a, mn, ops, str(fa)))
                break
            if bm in STORE_MN and bm not in ("cmp", "test") and strip_ptr(split_ops(bo)[0]) == hit:
                break
    P(f"G7 [R+0x50] with R loaded from ds:{CURR_REC:#x} in .text: {len(qh)} sites -> "
      + "; ".join(f"{a:#x}" for a, _, _, _ in qh[:12]))

    # ---- RIVAL machinery
    P(f"RIVAL reads of block+{ENERGY_OFF:#x} between the negative test and the price store: "
      f"{len(e_reads)} (a refund would need >=1); store mnemonic = {INS[E_STORE[2]][0]!r}")
    dis_hits = [(a, INS[a][0], INS[a][1]) for a in range(REMOVAL, LOOP_BOTTOM)
                if a in INS and "0x927a" in INS[a][1]]
    P(f"RIVAL mentions of the disabled-item family (0x927a..) inside the removal path: {len(dis_hits)}")
    memo_args = push_args(0x4F4A29, 5)
    tbl_in_memo = [a for a, o in memo_args if "0x984d" in o]
    P(f"RIVAL item-table operands among the memo's 5 args: {len(tbl_in_memo)}")

    print()
    print("== GATES ==")
    gates = []

    def G(gid, ok, why):
        gates.append((gid, ok))
        print(f"{'PASS' if ok else 'FAIL'} {gid} — {why}")

    G("G1", upkeep_fold and upkeep_fold[0] == ROW and upkeep_off == 16
      and blk_fold and blk_fold[0] == BLKSTRIDE
      and rmw["ENERGY"] == (ENERGY_OFF, ENERGY_OFF, "sub", ENERGY_OFF)
      and rmw["SPEND"] == (SPEND_OFF, SPEND_OFF, "add", SPEND_OFF),
      f"folds {upkeep_fold[0] if upkeep_fold else '?'}/{blk_fold[0] if blk_fold else '?'} "
      f"vs {ROW}/{BLKSTRIDE}; ENERGY off {e_rmw_off:#x} {rmw['ENERGY'][2]}, "
      f"SPEND off {s_rmw_off:#x} {rmw['SPEND'][2]}")

    G("G2", INS[NEG_TEST][0] == "jge" and INS[NEG_TEST][1].endswith(f"{LOOP_BOTTOM:x}")
      and eax_def == 0x4F4960 and INS[eax_def][1] == "eax,eax"
      and offA == DIFF_OFF and immA == "0x1" and jgA[0] == "jg"
      and jgA[1].endswith(f"{CLAMP_B:x}")
      and INS[0x4F4992][0] == "neg" and offB == QUEUE_HEAD_OFF
      and all(INS[s][0] == "mov" and f"0x{ENERGY_VA:x}" in INS[s][1] for s in E_STORE[:2]),
      f"jge->{LOOP_BOTTOM:#x}; A gates block+{offA:#x} vs {immA}; B gates rec+{offB:#x} "
      f"against neg(item); 2 clamp stores of the zeroed eax")

    G("G3", len(w8) == 2 and {a for a, _, _, _ in w8} == {0x57EF57, 0x59EED6}
      and len(folded8) == 0
      and any("ds:" in o and f"0x{DIFF_GLOB:x}" in o for _, _, o in create_defs)
      and any(o.replace("eax,", "") == f"0x{AI_DIFF:x}" for _, _, o in create_defs)
      and load_fold and load_fold[0] * 4 == BLKSTRIDE
      and any(m == "movsx" for _, m, _ in load_def),
      f"{len(w8)} destination-named writers + {len(folded8)} folded-pointer ones; create stores "
      f"ds:{DIFF_GLOB:#x} or {AI_DIFF}; save/load stores a movsx byte "
      f"through {load_fold[0] if load_fold else '?'}*4={BLKSTRIDE if load_fold else '?'}")

    G("G4", chg_fold and chg_fold[0] == BASE_STRIDE and rem_fold and rem_fold[0] == BASE_STRIDE
      and f"0x{BASEMAP:x}" in chg_read[1] and f"0x{BASEMAP:x}" in rem_mat[1]
      and "[eax]" in rem_read[1].lower() and "[eax]" in rem_store[1].lower()
      and INS[0x4F49D8][0] == "not" and INS[0x4F49DF][0] == "and"
      and rem_store[0] == "mov" and "byte" in rem_store[1].lower()
      and len(chg_and) >= 1,
      f"both folds {chg_fold[0] if chg_fold else '?'}/{rem_fold[0] if rem_fold else '?'} "
      f"vs {BASE_STRIDE}; same base {BASEMAP:#x}; clear = not/and/mov-byte through [eax]")

    G("G5", item_fold and item_fold[0] == ROW and off44 == 12
      and INS[0x4F49F7][0] == "imul" and INS[0x4F49F2][1].endswith(f"{FACTOR:x}")
      and INS[E_STORE[2]][0] == "mov" and len(e_reads) == 0,
      f"price = FACTOR({FACTOR:#x}) x row+{off44} via {item_fold[0] if item_fold else '?'}*item; "
      f"store is {INS[E_STORE[2]][0]!r} with {len(e_reads)} ENERGY reads on the path")

    G("G6", INS[0x4F4A11][1].endswith(f"{SLOTTER:x}") and INS[0x4F4A29][1].endswith(f"{MEMO:x}")
      and pe_cstr(STR_LABEL) == b"POWERSHORT" and pe_cstr(STR_ICON) == b"genwarning_sm.pcx"
      and any(f"0x{STR_LABEL:x}" in o for _, o in memo_args)
      and any(f"0x{STR_ICON:x}" in o for _, o in memo_args)
      and any(o == "0x1" for _, o in push_args(0x4F4A11, 4)),
      f"memo args carry {STR_LABEL:#x}/{STR_ICON:#x} = "
      f"{pe_cstr(STR_LABEL)!r}/{pe_cstr(STR_ICON)!r}; slot-setter param_1 = 1")

    G("G7", any(m == "inc" and "esi" in o for _, m, o in tail)
      and any(m == "jl" and o.endswith(f"{LOOP_TOP:x}") for _, m, o in tail)
      and len(mats) == 2 and [a for a, _, _ in mats] == [0x4F4837, 0x4F49D1]
      and len(eax_writes) == 0 and INS[0x4F49E1][0] == "mov"
      and "byte ptr [eax]" in INS[0x4F49E1][1].lower()
      and any(a == 0x4F4994 for a, _, _, _ in qh),
      f"back-edge to {LOOP_TOP:#x} after the removal; {len(mats)} map-address sites "
      f"(test@0x4f4837 / clear-read@0x4f49da), {len(eax_writes)} eax writes before the store; "
      f"{len(qh)} rec+0x50 readers incl. 0x4f4994")

    r1_dead = len(e_reads) == 0 and INS[E_STORE[2]][0] == "mov"
    r2_dead = len(dis_hits) == 0 and f"0x{BASEMAP:x}" in rem_mat[1]
    r3_dead = len(tbl_in_memo) == 0
    print(f"{'PASS' if r1_dead else 'FAIL'} RIVAL1 — 'the shortfall REFUNDS ENERGY (+=)': "
          f"dies on {len(e_reads)} reads + store {INS[E_STORE[2]][0]!r}")
    print(f"{'PASS' if r2_dead else 'FAIL'} RIVAL2 — 'the removal clears a DISABLED-LIST bit "
          f"(0x927a.. family)': dies on {len(dis_hits)} mentions; the clear names {BASEMAP:#x}")
    print(f"{'PASS' if r3_dead else 'FAIL'} RIVAL3 — 'the POWERSHORT memo names the facility': "
          f"dies on {len(tbl_in_memo)} table operands in its 5 args")

    body = "\n".join(T)
    dig = hashlib.sha256(body.encode()).hexdigest()[:16]
    nfail = sum(1 for _, ok in gates if not ok)
    print()
    print(f"table rows: {len(T)}  gates: {len(gates) - nfail}/{len(gates)}  digest {dig}")
    if nfail:
        print(f"FAIL M334: {nfail} gate(s) red")
        return 1
    print("PASS M334: 7/7 gates")
    return 0


LOOP_END = 0x4F4A3C

if __name__ == "__main__":
    sys.exit(main())
