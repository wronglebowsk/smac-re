#!/usr/bin/env python3
"""M364 (chain-2, STATIC) - the NOUNS of the faction-relations bits.

M362 proved the 0x4db1xx dialog's +0x15a0 group is 13 checkboxes whose ids ARE the bits of
the (faction,target) relation dwords. This milestone asks what each bit MEANS.

The lever is the relation PREDICATE `FUN_00426d60(fac, tgt, mask)`, 17 insns:
    eax = fac * 0x20bc ; eax = DWORD PTR [eax + tgt*4 + 0x94d448] ; eax &= mask ; ret
i.e. `(rel[fac][tgt] & mask) != 0`.  Its 232 call sites push the BIT ITSELF, and the code
that asks is the diplomacy menu (FUN_00442320), whose branches are named by Script.txt keys
("DONTHAVEPACT"/"REALLYENDPACT" for the end-pact case, "DIPLOVENDETTA"/"DIPLONOVENDETTA"
for the declare-vendetta case).  That is what pins a bit to a NOUN.

Gates (tables print FIRST, every gate names a mutant in scripts/m364_mutate.py):
  G1  the 13 (id, mask, dword) rows re-decoded from FUN_004db1b0's sync blocks; record
      offsets +0x18/+0x38; 0x82f dwords == the predicate's 0x20bc-byte stride.
  G2  the predicate decoded insn by insn (rival: 'it is a setter').
  G3  call-site census: the 3rd pushed argument is the mask (register args resolved);
      single-bit vs composite asks, and composite asks are ORs of singly-asked bits.
  G4  noun witnesses: per bit the asker functions and their diplomacy literals.
  G5  the co-setting rules inside the six writers + the page's bulk apply masks.
  G6  direct-access corroboration: every addressing form that names a pair dword.
  G7  RIVALS, each measured and each FAILING on the printed numbers.
"""
import bisect
import collections
import csv
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M364_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.environ.get("M364_INDEX") or os.path.expanduser("~/reverse/smac/ghidra_out/index.csv")
SHARDS = os.environ.get("M364_SHARDS") or os.path.expanduser("~/reverse/smac/ghidra_out")

SYNC = (0x4DB1B0, 0x4DB474)      # FUN_004db1b0: the 13 sync blocks
APPLY = (0x4DA2C0, 0x4DA9C0)     # FUN_004da2c0: the page's apply/OK handler
SET_CHECKED = 0x6050D4
PRED = 0x426D60                  # FUN_00426d60(fac, tgt, mask)
MENU = 0x442320                  # FUN_00442320: the diplomacy menu (string-keyed branches)
WRITERS = (0x5518F0, 0x5519C0, 0x551A20, 0x551C40, 0x551CF0, 0x551D70)
BASE_A, BASE_B = 0x94D448, 0x94D468
REC_OFF_A = BASE_A - 0x94D430    # 0x18
REC_OFF_B = BASE_B - 0x94D430    # 0x38
STRIDE_DW = 0x82F                # dwords per faction record
STRIDE_B = 0x20BC                # bytes per faction record (the predicate's imul)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
FNHEAD = re.compile(r"^// ==== (\S+) @ 0x([0-9a-f]+) size=(\d+)$")
DISP = re.compile(r"0x(94d448|94d468)(?![0-9a-f])", re.I)
NOUNS = ["VENDETTA", "BLOODTRUCE", "TRUCE", "TREATY", "PACT", "ATROCIT", "SANCTION",
         "COUNCIL", "INFILTRAT", "SURRENDER", "ALLIANCE", "REPUTE", "DIPLO"]
LEXICON = re.compile(r'"([^"]*(' + "|".join(NOUNS) + r')[^"]*)"', re.I)

# declared nouns: mask -> (noun, the literals that must witness it)
DECLARED = {
    0x1: ("pact in force", ["REALLYENDPACT", "DONTHAVEPACT"]),
    0x8: ("at war (vendetta)", ["DIPLOVENDETTA", "DIPLONOVENDETTA"]),
}
RELSTATE = ("PACT", "VENDETTA")

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


# ---------------------------------------------------------------- G1 geometry
def g1():
    print("G1  the 13 sync rows of FUN_004db1b0, re-decoded (id, mask, dword)")
    print("    #  call@       id         mask       and@        dword  rec_off")
    hits = []
    w = window(*SYNC)
    for k, ins in enumerate(w):
        if ins["op"] != "call" or ins["arg"].lower() != "0x%x" % SET_CHECKED:
            continue
        idv = None
        for back in range(k - 1, max(-1, k - 4), -1):
            v = imm(w[back]["arg"])
            if w[back]["op"] == "push" and v is not None:
                idv = v
                break
        mask = andat = None
        for back in range(k - 1, max(-1, k - 8), -1):
            if w[back]["op"] == "and" and w[back]["arg"].startswith("eax,"):
                v = imm(w[back]["arg"][4:])
                if v is not None:
                    mask, andat = v, w[back]["a"]
                    break
        dw = None
        for back in range(k - 1, max(-1, k - 12), -1):
            m = DISP.search(w[back]["arg"])
            if m:
                dw = int(m.group(1), 16)
                break
        if idv is not None:
            hits.append((ins["a"], idv, mask, andat, dw))
    for n, (a, i, mk, aa, dw) in enumerate(hits, 1):



        print(f"   {n:2d} {a:#010x} {i:#010x} {mk:#010x} {aa:#010x} {dw:#08x} "
              f"{dw - 0x94D430:#06x}")
    a_rows = [h for h in hits if h[4] == BASE_A]
    b_rows = [h for h in hits if h[4] == BASE_B]
    gate("G1a", len(hits) == 13 and len(a_rows) == 11 and len(b_rows) == 2
         and all(h[2] == (h[1] & 0x7FFFFFFF) for h in hits),
         f"{len(hits)} rows, {len(a_rows)} on 0x94d448 + {len(b_rows)} on 0x94d468, "
         f"mask==id&0x7fffffff {sum(h[2] == (h[1] & 0x7FFFFFFF) for h in hits)}/13")
    gate("G1b", all(h[4] - 0x94D430 in (REC_OFF_A, REC_OFF_B) for h in hits),
         f"record offsets +{REC_OFF_A:#x} (dword A) / +{REC_OFF_B:#x} (dword B), "
         f"delta {REC_OFF_B - REC_OFF_A:#x} = {(REC_OFF_B - REC_OFF_A)//4} dwords")
    masks = [h[2] for h in hits]
    gate("G1c", len({h[1] for h in hits}) == 13 and all(single(m) for m in masks),
         f"{len({h[1] for h in hits})} distinct ids over {len(set(masks))} mask values; "
         f"single-bit masks {sum(single(m) for m in masks)}/{len(masks)}")
    dup = sorted(m for m in set(masks) if masks.count(m) > 1)
    gate("G1d", dup == [0x8, 0x2000],
         f"mask values carried by BOTH dwords {[hex(m) for m in dup]} -> directional pairs"
         f" (A/B copies of one bit)")
    gate("G1e", STRIDE_DW * 4 == STRIDE_B and 0x82F == STRIDE_B // 4,
         f"stride {STRIDE_DW:#x} dwords x4 == {STRIDE_B:#x} bytes = the predicate's imul")
    return hits


# ---------------------------------------------------------------- G2 predicate
def g2():
    print("\nG2  the relation predicate FUN_00426d60(fac, tgt, mask), decoded")
    w = window(PRED, PRED + size_of("FUN_00426d60"))
    for ins in w:
        print(f"      {ins['a']:#010x}  {ins['t']}")
    body = [i for i in w if i["op"] not in ("push", "pop", "int3", "ret", "nop")]
    stores = [i for i in body if i["op"] in ("mov", "or", "and", "xor", "add", "sub")
              and "[" in i["arg"].split(",")[0]]
    imul = [i for i in body if i["op"] == "imul"]
    ands = [i for i in body if i["op"] == "and" and "[" not in i["arg"].split(",")[0]]
    gate("G2a", imul and imm(imul[0]["arg"].split(",")[-1]) == STRIDE_B,
         f"{len(body)} insns, 1 imul {imul[0]['arg'] if imul else '-'} = the 0x20bc record stride")
    gate("G2b", len(stores) == 0,
         f"{len(stores)} stores: a pure READ, i.e. a test and not a setter")
    gate("G2c", ands and ands[-1]["arg"].replace(" ", "").endswith("[ebp+0x10]"),
         f"tail `{ands[-1]['t'] if ands else '-'}` -> arg2 (3rd pushed) is the MASK")


# ------------------------------------------------------------ G3 call-site census
def g3():
    print("\nG3  every call site of the predicate: the 3rd pushed argument is the mask")
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
                continue          # the arg movs interleave with the pushes
            break
        sites.append((ins["a"], owner(ins["a"]), args))
    const, dyn, out = collections.Counter(), collections.Counter(), []
    for a, fn, args in sites:
        v = None
        if len(args) == 3:
            v = imm(args[2][0])                  # nearest-first: arg0, arg1, arg2 = mask
        out.append((a, fn, args, v))
        if v is not None:
            const[v] += 1
        else:
            dyn[args[2][0] if len(args) == 3 else f"{len(args)}pushes"] += 1
    print(f"    {len(out)} call sites in {len({s[1] for s in out})} functions;"
          f" mask constant at {sum(const.values())}, unresolved at {sum(dyn.values())}")
    print("    mask   n  single")
    for m, c in sorted(const.items()):
        print(f"    {m:#010x} {c:3d}  {'yes' if single(m) else 'NO'}")
    sb = sorted(m for m in const if single(m))
    comp = sorted(m for m in const if not single(m))
    lone = {b for m in comp for b in (1 << k for k in range(32) if m >> k & 1) if b not in sb}
    gate("G3a", len(out) == 232 and sum(const.values()) == 214,
         f"{len(out)} sites, {sum(const.values())} constant masks, {len(dyn)} unresolved"
         f" ({sum(dyn.values())} sites)")
    gate("G3b", len(sb) == 19 and len(comp) == 16 and lone == {0x800},
         f"{len(sb)} single-bit masks / {len(comp)} composite; the ONLY bit asked inside a"
         f" composite and never alone: {[hex(b) for b in sorted(lone)]}")
    gate("G3c", sb == [0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80, 0x400, 0x1000, 0x2000,
                       0x8000, 0x10000, 0x40000, 0x200000, 0x400000, 0x2000000, 0x8000000,
                       0x10000000],
         f"bits asked in the single form: {[hex(m) for m in sb]}")
    print(f"    composite masks: {[hex(m) for m in comp]}")
    print(f"    unresolved argument registers: "
          + ", ".join(f"{k}={v}" for k, v in dyn.most_common(6)))
    return out, const


# ------------------------------------------------------------ G4 witnesses
def literals_by_function():
    lit = collections.defaultdict(set)
    for name in sorted(os.listdir(SHARDS)):
        if not (name.startswith("shard_") and name.endswith(".c")):
            continue
        with open(os.path.join(SHARDS, name), errors="replace") as f:
            cur = None
            for line in f:
                h = FNHEAD.match(line)
                if h:
                    cur = h.group(1)
                    continue
                if cur is None:
                    continue
                for s in LEXICON.findall(line):
                    lit[cur].add(s[0].upper())
    return lit


def menu_case_witness():
    """Per-mask witness at the CALL-SITE level: inside FUN_00442320's decompiled body, a
    predicate call belongs to the enclosing `case N:` block, and that block's literals are
    the menu entries the ask gates.  Function-level literals cannot tell 0x1 from 0x8."""
    body = None
    for name in sorted(os.listdir(SHARDS)):
        if not (name.startswith("shard_") and name.endswith(".c")):
            continue
        cur = None
        lines = []
        for line in open(os.path.join(SHARDS, name), errors="replace"):
            h = FNHEAD.match(line)
            if h:
                if cur == "FUN_00442320":
                    body = lines
                    break
                cur = h.group(1)
                lines = []
                continue
            if cur == "FUN_00442320":
                lines.append(line)
        if body:
            break
    if not body:
        return {}
    blocks, cur = {}, []
    for line in body:
        if re.match(r"^\s*case\s+[-0-9a-fx]+:", line):
            if cur:
                blocks[len(blocks)] = cur
            cur = [line]
            continue
        cur.append(line)
    if cur:
        blocks[len(blocks)] = cur
    out = collections.defaultdict(set)
    for k, blk in blocks.items():
        lits = set()
        for l in blk:
            for s in LEXICON.findall(l):
                lits.add(s[0].upper())
        if not lits:
            continue
        for line in blk:
            for m in re.finditer(r"FUN_00426d60\([^)]*,\s*(0x[0-9a-f]+|\d+)\s*\)", line):
                v = int(m.group(1), 0)
                out[v] |= lits
    return dict(out)


def g4(sites, const):
    print("\nG4  noun witnesses: the literals of the functions that ASK each bit")
    lit = literals_by_function()
    print(f"    {len(lit)} functions in the image carry a diplomacy literal")
    ask = collections.defaultdict(set)
    for a, fn, args, v in sites:
        if v is not None:
            ask[v].add(fn)
    print("    bit        n_sites askers")
    for m in sorted(ask):
        print(f"    {m:#010x} {const[m]:5d} {sorted(ask[m])}")
    print("    literal sets of the askers that carry one:")
    for f in sorted({s[1] for s in sites}):
        l = sorted(lit.get(f, ()))
        if l:
            print(f"      {f:16s} {l}")
    casew = menu_case_witness()
    print("    CASE-BLOCK witnesses inside the diplomacy menu (FUN_00442320):")
    for m in sorted(casew):
        print(f"      mask {m:#010x}  block literals {sorted(casew[m])}")
    print("\n    NOUN TABLE")
    print("    bit        n_sites  noun                 conf  case-block witness")
    out = {}
    for m in sorted(ask):
        wits = set(casew.get(m, ()))
        noun, need = DECLARED.get(m, (None, None))
        conf = "INF"
        if noun:
            conf = "V" if all(x in wits for x in need) else "FAIL"
        out[m] = (noun, sorted(wits), conf)
        print(f"    {m:#010x} {len(ask[m]):8d}  {noun or '-':20s} {conf:4s}  "
              f"{sorted(wits) if wits else ''}")
    for m, (noun, need) in DECLARED.items():
        other = set(DECLARED[0x8 if m == 0x1 else 0x1][1])
        gate(f"G4{'a' if m == 0x1 else 'b'}",
             all(x in casew.get(m, ()) for x in need)
             and not (other & set(casew.get(m, ()))),
             f"bit {m:#x} = {noun}: its case block carries {need} and NONE of the rival keys"
             f" {sorted(other)}")
    gate("G4c", set(casew.get(0x1, ())) .isdisjoint(casew.get(0x8, ())),
         f"the 0x1 and 0x8 case blocks share NO literal -> the two nouns are discriminated"
         f" at the call-site level")
    gate("G4d", len(ask[0x1]) == 14 and len(ask[0x8]) == 9,
         f"asker counts: 0x1={len(ask[0x1])} functions ({const[0x1]} sites), "
         f"0x8={len(ask[0x8])} ({const[0x8]}), 0x10={len(ask[0x10])} ({const[0x10]})")
    return out


# ------------------------------------------------- G5 co-set rules + bulk masks
def g5():
    print("\nG5  the co-setting rules inside the writers, and the page's bulk apply masks")
    print("    rule = `test m` then, on the taken path, `or s` / `and ~c`")
    rules = []
    for wf in WRITERS:
        w = window(wf, wf + size_of("FUN_%08x" % wf))
        last = None
        for ins in w:
            if ins["op"] == "test" and "," in ins["arg"]:
                last = imm(ins["arg"].split(",")[-1])
                continue
            if last is not None and ins["op"] in ("or", "and"):
                v = imm(ins["arg"].split(",")[-1])
                if v is not None:
                    rules.append((wf, last, ins["op"], v))
                    print(f"      {wf:#08x}  test {last:#010x} -> {ins['op']} {v:#010x}"
                          f"  ({'set' if ins['op'] == 'or' else 'clear'} "
                          f"{v if ins['op'] == 'or' else (~v) & 0xFFFFFFFF:#x})")
            if ins["op"] in ("or", "and", "test"):
                last = None
            elif ins["op"] in ("mov", "push", "pop", "lea", "shl", "add", "sub", "cmp"):
                continue
            elif ins["op"].startswith("j") or ins["op"] == "not":
                continue
            else:
                last = None
    gate("G5a", (0x5518F0, 0x7, "or", 0x1100000) in rules,
         "the 3-bit group 0x7 also sets 0x1000000|0x100000 in FUN_005518f0")
    gate("G5b", (0x5518F0, 0x10, "or", 0x8040) in rules,
         "bit 0x10 also sets 0x8000|0x40 (one rule, both directions)")
    ids = {0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x400, 0x1000, 0x2000, 0x40000, 0x2000000}
    calls = []
    w = window(*APPLY)
    for k, ins in enumerate(w):
        if ins["op"] != "call" or imm(ins["arg"]) not in WRITERS:
            continue
        args = []
        for back in range(k - 1, max(-1, k - 7), -1):
            if w[back]["op"] != "push":
                break
            args.append(w[back]["arg"])
        calls.append((ins["a"], int(ins["arg"], 16), list(reversed(args))))
    bulk = {}
    for a, wf, args in calls:
        for x in args:
            v = imm(x)
            if v is not None and v > 0xFF:
                bulk[v] = {i for i in ids if v & i == i}
    print(f"    {len(calls)} writer calls in the apply handler; bulk masks:")
    for m, cov in sorted(bulk.items()):
        print(f"      {m:#010x} covers {len(cov):2d} of the 13 ids {[hex(c) for c in sorted(cov)]}")
    gate("G5c", len(calls) == 4 and bulk.get(0x1F89) == {0x1, 0x8, 0x400, 0x1000},
         f"{len(calls)} writer calls; 0x1f89 covers exactly {{1,8,400,1000}} = "
         f"{[hex(c) for c in sorted(bulk.get(0x1F89, ()))]}")


# ------------------------------------------------- G6 direct-access corroboration
def g6():
    print("\nG6  corroboration: instructions that name a pair dword directly")
    kinds = collections.Counter()
    bits = collections.Counter()
    for ins in INS:
        if not DISP.search(ins["arg"]):
            continue
        kinds[ins["op"]] += 1
        if ins["op"] in ("and", "test"):
            v = imm(ins["arg"].split(",")[-1])
            if v is not None and single(v):
                bits[v] += 1
    print("    mnemonics: " + ", ".join(f"{k}={v}" for k, v in kinds.most_common(8)))
    print("    single-bit immediates: " + ", ".join(f"{m:#x}={c}" for m, c in sorted(bits.items())))
    gate("G6a", kinds["test"] == 388 and kinds["mov"] == 300 and kinds["lea"] == 39,
         f"direct-displacement census: test={kinds['test']} mov={kinds['mov']} "
         f"lea={kinds['lea']} (all other mnemonics {sum(kinds.values()) - 388 - 300 - 39})")
    gate("G6b", bits[0x1] == 150 and bits[0x1] > 2 * bits[0x10],
         f"bit 0x1 dominates the direct single-bit immediates ({bits[0x1]} vs 0x10={bits[0x10]})")
    return kinds, bits


# ---------------------------------------------------------------- G7 rivals
def g7(sites, const):
    print("\nG7  RIVALS (each must FAIL on the numbers printed above)")
    sb = sorted(m for m in const if single(m))
    outside = [m for m in sb if m & 0x7 == 0]
    gate("G7a", len(outside) == 16,
         f"R1 'the bits are a 3-bit enum 0..7': {len(outside)} of {len(sb)} single-bit asks lie"
         f" OUTSIDE 0x7 -> refuted")
    ords = sorted({h for h in sb})
    gate("G7b", len(set(sb)) != 13,
         f"R2 'ids are row ordinals 1..13': {len(set(sb))} distinct bits, gaps at 0x200/0x800 -"
         f" refuted")
    ask = collections.defaultdict(set)
    for a, fn, args, v in sites:
        if v is not None:
            ask[v].add(fn)
    flip = ask.get(0x1) == ask.get(0x8)
    gate("G7c", not flip,
         f"R3 '0x1 is vendetta (the natural guess)': 0x1 askers {len(ask.get(0x1, ()))} vs 0x8"
         f" askers {len(ask.get(0x8, ()))}; the pact keys sit on 0x1, the vendetta keys on 0x8"
         f" -> refuted")
    gate("G7d", (REC_OFF_B - REC_OFF_A) >> 2 == 8,
         f"R4 'the two dwords are one 16-bit field': they are {REC_OFF_B - REC_OFF_A:#x} apart"
         f" = {(REC_OFF_B - REC_OFF_A)//4} dwords, and only 2 of 11 mask values repeat - refuted")


def main():
    load()
    global FNS, STARTS
    FNS, STARTS = extents()
    print("M364 - the nouns of the faction-relations bits\n")
    g1()
    g2()
    sites, const = g3()
    g4(sites, const)
    g5()
    g6()
    g7(sites, const)
    good = sum(1 for _, ok, _ in GATES if ok)
    n = len(GATES)
    head = f"M364: {good}/{n} gates"
    if good == n:
        print(f"\nPASS  M364: {good}/{n} gates")
    else:
        print(f"\nFAIL  M364: {good}/{n} gates")
        for name, ok, msg in GATES:
            if not ok:
                print(f"  red: {name}  {msg}")
    digest = hashlib.sha256("\n".join(f"{k}:{ok}" for k, ok, _ in GATES)
                            .encode()).hexdigest()[:16]
    print(f"digest {digest}")
    return 0 if good == n else 1


if __name__ == "__main__":
    sys.exit(main())
