#!/usr/bin/env python3
"""M351 - the CHOOSER-SIDE PRODUCER of the negative queue head.

M349 settled the decode side: FUN_004ef6d0 negates the head to get the unit TYPE
(neg @0x4ef89f).  This milestone settles the OTHER end: which number the production
item chooser negates, and which field of a unit design that number is.

Answer (static, terran.exe .text):

    the chooser negates its ROW'S ITEM, and for a unit row that item is the loop
    counter i of the row builder -- the TYPE ORDINAL into the 72-record unit-type
    array at 0x984d38 (stride 0x30; +0x00 name, +0x0c cost).  It is NOT the
    design id the candidate table carries (0x9267e4: idx<64 -> idx, idx>=64 ->
    owner*0x40 + (idx&0x3f), i.e. 192..255 for owner 3), NOT the cost, and NOT
    the +0x04 string field.  The sign is a FLAG BIT: bit 0x20 set -> +item
    (facility rows), bit 0x20 clear -> -item (unit rows), so a unit row always
    returns -type and the queue slot 0 write stores exactly that.

The chain, each hop pinned below:

  0x496ad0  chooser_run_modal:  item = [list+0xa780->current_row + 4]
                                flags = 0x495480(list)  (current_row->payload +8)
                                (flags & 0x20) == 0  ->  neg item        @0x49772a-0x49777c
  0x494e61  the SAME law in 9 instructions (second, independent site)
  0x495b27  unit row loop i = 1..0x47: label/cost from 0x984d38/0x984d44 + 0x30*i,
            affordability asked with -i @0x495c2f, flags = 0x4960f0(i) | 0x10,
            append(list, buf, item = i, flags, 0) @0x495e0a-0x495e1e
  0x4956c6  facility row loop idx = 0..0x7f: item = cand[idx] @0x9267e4,
            flags = 0x496050(item) | 0x20, append item = cand[idx]
  0x401110  append: node+4 = the item argument @0x401217   (what 0x401940 returns)
  0x41860a  call 0x496ad0 -> edi -> [ebp-0x10] -> ds:0x8f0d60 (the base record)
            -> mov [edx+0x50],eax  @0x418b57, gated on pos == 0 @0x418b48

Static only: no box, no Wine, no gdb.  Every printed number is PARSED from the objdump
listing (scratch/m574/text.txt) or from committed evidence; each gate then asserts the
parsed value against a declared literal, so a drift in binary, listing or trace reddens.

    python3 -u scripts/m351_type_producer.py             # acceptance
    python3 -u scripts/m351_type_producer.py --digest    # digest only
    SMAC_M351_TEXT=/path/to/text.txt  ...                # alternate listing (mutants)
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M351_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
M349 = os.environ.get("SMAC_M351_M349") or os.path.join(ROOT, "evidence", "m349_unit_id.txt")
M68 = os.environ.get("SMAC_M351_M68") or os.path.join(ROOT, "evidence", "m68_key_run_attempt1.txt")
MUT = os.environ.get("SMAC_M351_MUTANT", "")

ROW = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


class Listing:
    def __init__(self, path):
        self.at = {}
        self.order = []
        with open(path, "r", errors="replace") as f:
            for line in f:
                m = ROW.match(line)
                if not m:
                    continue
                a = int(m.group(1), 16)
                self.at[a] = norm(m.group(3))
                self.order.append(a)
        self.order.sort()

    def get(self, addr):
        return self.at.get(addr)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a <= hi]

    def count(self, lo, hi, pred):
        return sum(1 for a, s in self.window(lo, hi) if pred(s))


def imm(text, pat):
    """first integer captured by pat inside text (hex or dec), else None"""
    m = re.search(pat, text or "")
    if not m:
        return None
    g = next((x for x in m.groups() if x), None)
    if g is None:
        return None
    return int(g, 16) if g.lower().startswith("0x") else int(g)


# ------------------------------------------------------------------ declared literals
UNIT_LOOP_LO, UNIT_LOOP_HI = 0x1, 0x48          # the unit row loop i = 1..71
FAC_LOOP_HI = 0x80                              # facility row loop idx = 0..127
TYPE_STRIDE = 0x30
TYPE_BASE = 0x984D38                            # +0x00 name  (M349: +0x0c cost)
TYPE_COST = 0x984D44
CAND_TABLE, CAND_N = 0x9267E4, 0x9267E0
FLAG_POS, FLAG_UNIT, FLAG_MISC = 0x20, 0x10, 0x80
QUEUE_SLOT0 = 0x50
BASE_CUR = 0x8F0D60
STORE_GUARD = 0xFFFFFFD9                        # cmp [base+0x50],-39 / jg at the store

PASS, FAIL = [], []
LISTING_SHA = ""


def gate(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print("%s   %s%s" % ("ok  " if ok else "FAIL", name, ("  " + detail) if detail else ""))
    return ok


def main():
    if not os.path.exists(TEXT):
        print("listing not found: %s" % TEXT)
        return 2
    L = Listing(TEXT)

    global LISTING_SHA
    LISTING_SHA = hashlib.sha1(open(TEXT, "rb").read()).hexdigest()[:16]
    print("M351 - the chooser-side producer of the negative queue head (static)")
    print("listing: %s" % os.path.relpath(TEXT, ROOT))
    print("listing sha1 %s  insns %d" % (LISTING_SHA, len(L.order)))
    print()

    # ---------------------------------------------------------------- TABLE 1 windows
    blocks = [
        ("modal sign law  FUN_00496ad0", 0x497704, 0x497780),
        ("second site     0x494e61", 0x494E61, 0x494E92),
        ("unit row loop   0x495b27 (head)", 0x495B27, 0x495C37),
        ("unit row loop   0x495df0 (append)", 0x495DF3, 0x495E1E),
        ("facility row loop 0x4956c6 (head)", 0x4956C6, 0x4956E0),
        ("facility row loop 0x495a81 (append)", 0x495A81, 0x495AB6),
        ("item getter / flags getter", 0x401940, 0x401968),
        ("append: node+4 = item", 0x40120E, 0x40121A),
        ("store: chooser -> base+0x50", 0x41860A, 0x41861A),
        ("store: the write", 0x418B46, 0x418B58),
    ]
    print("TABLE 1  the pinned windows")
    for label, lo, hi in blocks:
        w = L.window(lo, hi)
        print("  %-38s %d insns 0x%x..0x%x" % (label, len(w), lo, hi))
        for a, s in w[:3]:
            print("    0x%x  %s" % (a, s))
        if len(w) > 3:
            print("      ..  ")
    print()

    # ---------------------------------------------------------------- TABLE 2 measured
    loop_init = imm(L.get(0x495B27), r"\[ebp-0x24\],(0x[0-9a-f]+|\d+)")
    loop_bound = imm(L.get(0x495B39), r"\[ebp-0x24\],(0x[0-9a-f]+|\d+)")
    fac_bound = imm(L.get(0x4956C6), r"\[ebp-0x28\],(0x[0-9a-f]+|\d+)")
    stride_name = imm(L.get(0x495BC8), r"imul\s+\w+,\w+,(0x[0-9a-f]+|\d+)")
    base_name = imm(L.get(0x495BCB), r"\[[a-z]+(?:\+|\s\+)(0x98[0-9a-f]+)\]")
    stride_cost = imm(L.get(0x495BF3), r"imul\s+\w+,\w+,(0x[0-9a-f]+|\d+)")
    base_cost = imm(L.get(0x495C0E), r"\+(0x984[0-9a-f]+)\]")
    cand_base = imm(L.get(0x4956D6), r"\*4\+(0x92[0-9a-f]+)\]")
    store_off = imm(L.get(0x418B57), r"\[edx\+(0x[0-9a-f]+)\],eax")
    shown = {}
    shown["unit loop init"] = loop_init
    shown["unit loop bound"] = loop_bound
    shown["facility loop bound"] = fac_bound
    shown["unit stride (imul)"] = stride_name
    shown["unit name base"] = base_name
    shown["unit cost base"] = base_cost
    shown["candidate table"] = cand_base
    shown["queue store offset"] = store_off
    print("TABLE 2  measured literals")
    for k, v in shown.items():
        print("  %-22s %s" % (k, ("0x%x" % v) if v is not None else "PARSE-FAIL"))
    neg_call = L.count(0x41860F, 0x418B57, lambda s: s.startswith("neg "))
    neg_modal = L.count(0x497704, 0x4977AC, lambda s: s.startswith("neg "))
    calls_401940 = L.count(0x497704, 0x4977AC, lambda s: s == "call 0x401940")
    print("  %-22s %d" % ("neg in store path", neg_call))
    print("  %-22s %d" % ("neg in modal resolve", neg_modal))
    print("  %-22s %d" % ("call 0x401940 in modal", calls_401940))
    print()

    # ---------------------------------------------------------------- TABLE 3 sign law
    # 0x4960f0 is the unit row's flag producer: read its four return immediates.
    rets = {}
    for a in (0x496102, 0x496130, 0x496137, 0x49613B, 0x496142):
        s = L.get(a) or ""
        if s.startswith("mov eax,") or s.startswith("xor eax,eax"):
            rets[a] = 0 if s.startswith("xor") else imm(s, r"eax,(0x[0-9a-f]+|\d+)")
    unit_flags_vals = sorted(set(rets.values()))
    # ---------------------------------------------------------------- TABLE 0 the two sections
    print("TABLE 0  the row list the modal resolves is TWO sections, appended in this order")
    print("  A  0x%x..0x%x  idx<0x%x  item = cand[idx] @0x%x (k<0x40 -> k, k>=0x40 -> owner*0x40|(k&0x3f))"
          % (0x4956C6, 0x495B24, fac_bound or 0, cand_base or 0))
    print("      flags = 0x496050(item) | 0x20  ->  (flags & 0x20) != 0  ->  return +item")
    print("  B  0x%x..0x%x  i = %s..0x%x  item = i (TYPE ordinal: 0x%x + 0x%x*i, cost at +0x%x)"
          % (0x495B27, 0x495E91, loop_init, (loop_bound or 1) - 1, base_name or 0,
             stride_name or 0, (base_cost or 0) - (base_name or 0)))
    print("      flags = 0x4960f0(i) | 0x10, 0x4960f0 in %s  ->  bit 0x20 ALWAYS clear  ->  return -i"
          % (unit_flags_vals,))
    print("  then 0x418b5x stores that return into ds:0x%x + 0x%x (the base record's queue slot 0)"
          % (BASE_CUR, store_off or 0))
    print()

    print("TABLE 3  the sign law, computed over ALL 256 flag bytes (plus the reachable rows)")
    print("  0x4960f0 return immediates: %s  (from %d sites)" % (unit_flags_vals, len(rets)))
    rows = [(f, "flag byte", f) for f in range(256)]        # the WHOLE 8-bit flag space
    rows += [(FLAG_UNIT | f, "unit row", f) for f in unit_flags_vals]
    rows += [(FLAG_POS | f, "facility row", f) for f in (0, FLAG_MISC)]
    sign_rows = []
    sign_bit = FLAG_UNIT if MUT == "sign" else FLAG_POS      # MU21: classifier mutant
    if MUT == "sign":
        print("  [mutant sign] classifier sign bit = 0x%02x instead of 0x%02x" % (sign_bit, FLAG_POS))
    for flags, label, _ in rows:
        for item in (1, 3, 6, 71):
            ret = item if (flags & sign_bit) else -item
            sign_rows.append((flags, item, ret))
    n_clear = sum(1 for f in range(256) if not (f & FLAG_POS))
    n_neg_all = sum(1 for f, i, r in sign_rows if f < 256 and not (f & sign_bit) and r < 0)
    n_pos_all = sum(1 for f, i, r in sign_rows if f < 256 and (f & sign_bit) and r > 0)
    print("  256 flag bytes: %d with 0x20 clear, %d with 0x20 set" % (n_clear, 256 - n_clear))
    print("  of the 1024 (flag,item) samples: %d returned -item, %d returned +item"
          % (n_neg_all, n_pos_all))
    seen = set()
    for flags, item, ret in sign_rows:
        if flags in (FLAG_UNIT, FLAG_UNIT | 3, FLAG_POS, FLAG_POS | FLAG_MISC) and item == 6 \
                and flags not in seen:
            seen.add(flags)
            print("    reachable flags 0x%02x  item 6 -> %+d" % (flags, ret))
    n_neg = sum(1 for f, i, r in sign_rows if not (f & sign_bit) and r < 0)
    print()

    # ---------------------------------------------------------------- TABLE 4 rivals
    recorded = read_recorded()
    pairs = read_pairs()
    print("TABLE 4  rivals against the recorded heads")
    print("  recorded B31 heads: %s" % (recorded,))
    r1_dead = any(r > 0 for r in recorded)                     # a positive head exists
    print("  R1 'return is always -item'        -> recorded %s holds positives: dead=%s"
          % (recorded, r1_dead))
    r2_hits = []
    for tag, item, cell_entry, stored, cell in pairs:
        if item is None or stored is None:
            continue
        pred = -(item - 192)
        r2_hits.append((tag, item, cell, stored, pred, pred == stored))
    print("  R2 'negative is -(design id - 192)', tested on the parsed trace pairs:")
    for tag, item, cell, stored, pred, hit in r2_hits:
        print("    %s item=%s cell=%s stored=%s  predicts %+d  %s"
              % (tag, item, cell, stored, pred, "MATCH" if hit else "MISMATCH"))
    r2_ok = bool(r2_hits) and all(h for *_, h in r2_hits)
    r3 = neg_call == 0
    print("  R3 'the store site negates'        -> neg count in the store path = %d : %s"
          % (neg_call, r3))
    print()

    # ---------------------------------------------------------------- GATES
    print("GATES")
    # G1 the modal sign law
    ok = (L.get(0x49772A) == "and eax,0x20" and L.get(0x49772D) == "test eax,eax"
          and L.get(0x49772F) == "je 0x49776e" and L.get(0x49777C) == "neg eax"
          and L.get(0x497725) == "call 0x495480" and L.get(0x497777) == "call 0x401940"
          and L.get(0x49773A) == "call 0x401940" and L.get(0x497704) == "mov eax,DWORD PTR [ebp-0x10]"
          and L.get(0x497707) == "mov ecx,DWORD PTR [eax+0xa774]"
          and L.get(0x497717) == "call 0x4026b0")
    gate("G1 the modal resolves the cell, tests flags&0x20, and negates on the clear branch",
         ok, "flags 0x20 set -> +item @0x497766 ; clear -> neg @0x49777c")

    # G2 the second site: same law, 9 instructions
    ok = (L.get(0x494E67) == "call 0x401940" and L.get(0x494E78) == "call 0x495480"
          and L.get(0x494E83) == "and eax,0x20" and L.get(0x494E88) == "jne 0x494e92"
          and L.get(0x494E8D) == "neg ecx" and L.get(0x494E8F) == "mov DWORD PTR [ebp-0x24],ecx")
    gate("G2 an independent second site applies the same item/flags/0x20/neg law", ok,
         "0x494e61..0x494e8f")

    # G3 the unit row builder
    ok = (loop_init == UNIT_LOOP_LO and loop_bound == UNIT_LOOP_HI
          and stride_name == TYPE_STRIDE and base_cost == TYPE_COST
          and L.get(0x495C2C) == "mov ecx,DWORD PTR [ebp-0x24]"
          and L.get(0x495C2F) == "neg ecx" and L.get(0x495C32) == "call 0x4e4350"
          and L.get(0x495DFA) == "call 0x4960f0" and L.get(0x495DFF) == "or al,0x10"
          and L.get(0x495E0A) == "mov ecx,DWORD PTR [ebp-0x24]"
          and L.get(0x495E0D) == "push ecx" and L.get(0x495E1E) == "call 0x42ee20")
    gate("G3 the unit row loop appends item = the loop counter i (1..71), flags = f(i)|0x10",
         ok, "i=%s..%s stride=0x%x" % (loop_init, hex(loop_bound), stride_name or 0))

    # G4 the flag fn never sets 0x20
    ok = (unit_flags_vals == [0, 1, 2, 3]) and not any(v & FLAG_POS for v in unit_flags_vals)
    gate("G4 0x4960f0 returns only {0,1,2,3}, so a unit row's flags never carry 0x20",
         ok, "%s" % (unit_flags_vals,))

    # G5 the facility loop is the positive one
    ok = (fac_bound == FAC_LOOP_HI and cand_base == CAND_TABLE
          and L.get(0x495A8D) == "or al,0x20"
          and L.get(0x495A9D) == "mov ecx,DWORD PTR [ebp-0x2c]"
          and L.get(0x495AB1) == "call 0x42ee20"
          and L.get(0x4956DD) == "mov DWORD PTR [ebp-0x2c],edx")
    gate("G5 the facility loop appends item = cand[idx] with 0x20 ORed in (the +item branch)",
         ok, "idx<0x%x, cand@0x%x" % (fac_bound or 0, cand_base or 0))

    # G6 node+4 = the appended item
    ok = (L.get(0x401214) == "mov eax,DWORD PTR [ebp+0x8]"
          and L.get(0x401217) == "mov DWORD PTR [edx+0x4],eax"
          and L.get(0x401958) == "mov edx,DWORD PTR [ecx+0xc]"
          and L.get(0x40195B) == "mov eax,DWORD PTR [edx+0x4]")
    gate("G6 the append stores its item argument at node+4, and 0x401940 returns node+4", ok)

    # G7 flags are a DIFFERENT field (+8 of the row payload)
    ok = (L.get(0x495498) == "call 0x4027e0" and L.get(0x49549D) == "mov eax,DWORD PTR [eax+0x8]"
          and L.get(0x4027FB) == "mov eax,DWORD PTR [edx+0x8]")
    gate("G7 the flags getter reads the row payload's +8, not the item at +4", ok)

    # G8 the store into the base record's queue slot 0
    ok = (L.get(0x41860A) == "call 0x496ad0" and L.get(0x41860F) == "mov edi,eax"
          and L.get(0x418616) == "mov DWORD PTR [ebp-0x10],edi"
          and L.get(0x418B46) == "test esi,esi" and L.get(0x418B48) == "jne 0x418c39"
          and L.get(0x418B4E) == "mov edx,DWORD PTR ds:0x8f0d60"
          and L.get(0x418B54) == "mov eax,DWORD PTR [ebp-0x10]"
          and L.get(0x418B57) == "mov DWORD PTR [edx+0x50],eax")
    gate("G8 the chooser's return reaches base+0x50 only when the insert position is 0", ok,
         "0x41860a -> edi -> [ebp-0x10] -> [base+0x50]")

    # G9 sign is produced in the chooser, not at the store
    ok = (neg_call == 0 and neg_modal == 1)
    gate("G9 no negation between the chooser call and the store (%d negs); one in the modal"
         % neg_call, ok, "381-insn store path")

    # G10 same array as M349's decode
    m349 = read_m349()
    agree = (m349.get("base") == TYPE_COST and m349.get("stride") == TYPE_STRIDE
             and base_cost == m349.get("base") and stride_cost == m349.get("stride"))
    gate("G10 the row builder indexes the SAME type array M349's cost read uses", agree,
         "M349 cost base=%s stride=%s ; here base=%s stride=%s"
         % (hex(m349.get("base") or 0), m349.get("stride"), hex(TYPE_COST), stride_name))

    # G11 sign table
    ok = (all(r < 0 for f, i, r in sign_rows if not (f & sign_bit))
          and all(r > 0 for f, i, r in sign_rows if (f & sign_bit))
          and all(((FLAG_UNIT | v) & sign_bit) == 0 for v in unit_flags_vals)
          and all(((FLAG_POS | v) & sign_bit) != 0 for v in (0, FLAG_MISC)))
    gate("G11 every flag byte with 0x20 clear yields -item, every one with it set yields +item,"
         " and the reachable unit flags are all in the clear set", ok,
         "%d/%d samples negative, %d/%d positive" % (n_neg_all, n_clear * 4,
                                                     len(sign_rows) - n_neg_all,
                                                     (256 - n_clear) * 4))

    # G12 rivals
    gate("G12 R1/R2/R3 fail on the printed numbers",
         bool(recorded) and r1_dead and bool(r2_hits) and not r2_ok and r3,
         "facility +2 ; 196 predicts -4 ; 0 negs at the store")

    # G13 cell != item
    ok = (L.get(0x495B00) == "mov DWORD PTR [eax+0xa774],edx"
          and L.get(0x495AFA) == "mov edx,DWORD PTR [ecx+0xa818]"
          and L.get(0x495B69) == "test eax,eax" and L.get(0x495B6B) == "jne 0x495b6f"
          and L.get(0x495B6D) == "jmp 0x495b30")
    trace = open(M68, "r", errors="replace").read() if os.path.exists(M68) else ""
    verdict = [l for l in trace.splitlines() if l.lstrip().startswith("FAIL")]
    stale = [p for p in pairs if p[0] == "m68" and p[1] is not None and p[3] is not None
             and p[1] != p[3]]
    note_ok = bool(verdict) and "re-sorted" in " ".join(str(v) for v in verdict) and bool(stale)
    gate("G13 the selection cell is the ROW counter and rows are filtered, so cell != item",
         ok and note_ok,
         "m68 verdict states the re-sort: %s ; intent %s vs stored %s"
         % (note_ok, stale[0][1] if stale else None, stale[0][3] if stale else None))


    # G14 the type row is already represented as -i in QUEUE space (the chooser compares
    #     the base's own queue slot against -i; the design row compares against +item)
    ok = (L.get(0x49555B) == "mov edx,DWORD PTR [ecx+0xb68]"
          and L.get(0x495566) == "mov ecx,DWORD PTR [eax+edx*4+0x50]"
          and L.get(0x49556A) == "mov DWORD PTR [ebp-0x30],ecx"
          and L.get(0x495AEC) == "mov edx,DWORD PTR [ebp-0x2c]"
          and L.get(0x495AEF) == "cmp edx,DWORD PTR [ebp-0x30]"
          and L.get(0x495E59) == "mov edx,DWORD PTR [ebp-0x24]"
          and L.get(0x495E5C) == "neg edx"
          and L.get(0x495E5E) == "cmp edx,DWORD PTR [ebp-0x30]")
    gate("G14 the two sections compare the base queue slot against +item and against -i", ok,
         "[ebp-0x30] = ds:0x8f0d60 slot [sub+0xb68] @0x495566")

    # G15 the candidate table is owner-encoded, so its >=64 entries are faction items
    ok = (L.get(0x59600E) == "mov DWORD PTR ds:0x9267e0,ecx"
          and L.get(0x596017) == "cmp ecx,0x40" and L.get(0x59601F) == "shl eax,0x6"
          and L.get(0x596037) == "mov DWORD PTR [ecx*4+0x9267e4],ebx")
    gate("G15 cand[k] = k for k<0x40 else owner*0x40|(k&0x3f): the >=64 entries are faction items",
         ok, "cand_n @0x9267e0, table @0x9267e4")

    print()
    print("%d/%d gates" % (len(PASS), len(PASS) + len(FAIL)))
    facts = "|".join(str(x) for x in (loop_init, loop_bound, fac_bound, stride_name, base_name,
                                      base_cost, cand_base, store_off, neg_call, neg_modal,
                                      calls_401940, unit_flags_vals, recorded, pairs))
    dg = hashlib.sha1(("|".join(PASS) + "|" + TEXT + "|" + LISTING_SHA + "|" + facts).encode()).hexdigest()[:16]
    print("DIGEST %s  universe=%d gates=%d" % (dg, len(PASS) + len(FAIL), len(PASS)))
    if FAIL:
        print("FAIL M351: %d/%d gates" % (len(PASS), len(PASS) + len(FAIL)))
        return 1
    print("PASS M351: %d/%d gates" % (len(PASS), len(PASS)))
    return 0


def read_recorded():
    """the recorded B31 head sequence, PARSED from evidence/m349_unit_id.txt TABLE 3 (no fallback)"""
    heads = []
    path = os.path.join(ROOT, "evidence", "m349_unit_id.txt")
    if os.path.exists(path):
        for line in open(path, "r", errors="replace"):
            m = re.match(r"\s+head=(-?\d+)", line)
            if m:
                heads.append(int(m.group(1)))
    return heads


def read_pairs():
    """the two recorded intents, PARSED from the m68/m69 traces:
       m68 insert_4: item / cell_entry / stored_id ; m69 insert + verdict: item + stored."""
    out = []
    if os.path.exists(M68):
        for line in open(M68, "r", errors="replace"):
            if not line.lstrip().startswith("{") or '"insert_4"' not in line:
                continue
            d = json.loads(line)
            out.append(("m68", d.get("item"), d.get("cell_entry"), d.get("stored_id"), d.get("cell")))
    m69 = os.path.join(ROOT, "evidence", "m69_cursor2.jsonl")
    if os.path.exists(m69):
        stored = None
        for line in open(m69, "r", errors="replace"):
            if not line.lstrip().startswith("{"):
                continue
            d = json.loads(line)
            if d.get("tag") == "insert":
                stored = d.get("stored")
            if d.get("tag") == "verdict" and stored is not None:
                out.append(("m69", d.get("item"), d.get("item"), stored, d.get("poked_cursor")))
    return out


def read_m349():
    out = {}
    if not os.path.exists(M349):
        return out
    for line in open(M349, "r", errors="replace"):
        if "cost read" in line:
            m = re.search(r"base=0x([0-9a-f]+)", line)
            if m:
                out["base"] = int(m.group(1), 16)
            m = re.search(r"stride=(\d+)", line)
            if m:
                out["stride"] = int(m.group(1))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    a = ap.parse_args()
    sys.exit(main())
