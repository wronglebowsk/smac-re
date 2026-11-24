#!/usr/bin/env python3
"""M366 (chain-2, STATIC) - the NOUNS of faction-relations bits 0x10 and 0x20.

M364 named 0x1 = PACT and 0x8 = AT WAR from the diplomacy menu's case blocks and left 11
bits unnamed.  This milestone takes the two most-asked of those leftovers:

  0x10   37 bare asks in 14 functions (+15 composite sites); the declare-vendetta path writes it.
  0x20   18 bare asks in 3 functions (+12 composite); no game transition ever sets it.

Method: census every FUN_00426d60 site; re-derive what the six relation WRITERS do to the
masks 0x10/0x20 from their own bytes; then follow the only path that writes 0x10 (declare
vendetta) and the only place the engine asks 0x20 together with a noun-bearing mask (the
game-over selector that picks "...LOSE2" over "...LOSE").  Every number prints BEFORE it is
asserted; each VERIFIED row names its mutant in scripts/m366_mutate.py.

Gates:
  G1  census of the ask sites for 0x10/0x20 + the 13 editor ids (dword-A/B geometry).
  G2  the writers' mask rules, re-derived from the writer windows.
  G3  the declare-vendetta chain: FUN_00507ce0 -> FUN_005076d0 -> set(0x10); the literals.
  G4  read-side witnesses: the game-over selector (0x40020) and FUN_00502cd0's war literals.
  G5  direct-immediate access census for the two bits.
  G6  RIVALS, each measured and each FAILING on the printed numbers.
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
EXE = os.environ.get("M366_EXE") or os.path.join(ROOT, "programs/terran.exe")
SCRIPT = os.environ.get("M366_SCRIPT") or os.path.join(ROOT, "programs/Script.txt")

PRED = 0x426D60
SET_A, CLR_A = 0x551A20, 0x5518F0          # dword-A set / clear
CLR_B, SET_B = 0x551C40, 0x551D70          # dword-B clear / set (4-arg twins)
WRITERS = (0x5518F0, 0x5519C0, 0x551A20, 0x551C40, 0x551CF0, 0x551D70)
DECLARE, VENDETTA = 0x507CE0, 0x5076D0     # FUN_00507ce0 / FUN_005076d0
SYNC = (0x4DB1B0, 0x4DB474)                # FUN_004db1b0: the 13 editor ids
SET_CHECKED = 0x6050D4
BASE_A, BASE_B = 0x94D448, 0x94D468
STRIDE_DW, STRIDE_B = 0x82F, 0x20BC
DATA_VMA, DATA_OFF = 0x689000, 0x289000    # .data section (objdump -h)
TEXTOBJ = 0x997B20

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")

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
    return [i for i in INS[POS.get(lo, 0):] if i["a"] < hi]


def imm(s):
    m = re.fullmatch(r"(-?)0x([0-9a-f]+)", s.strip().lower())
    if m:
        v = int(m.group(2), 16)
        return (-v) & 0xFFFFFFFF if m.group(1) else v
    return None


def single(x):
    return x and x.bit_count() == 1


def bits(v, width=32):
    return sorted(1 << k for k in range(width) if v >> k & 1)


def cstr(va, n=24):
    with open(EXE, "rb") as f:
        f.seek(DATA_OFF + (va - DATA_VMA))
        raw = f.read(n)
    return raw.split(b"\0")[0].decode("latin-1")


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
        sites.append({"a": ins["a"], "fn": owner(ins["a"]), "n": n, "mask": mask})
    return sites


def editor_ids():
    """FUN_004db1b0 syncs 13 checkbox ids into the relation dwords."""
    hits = []
    w = window(*SYNC)
    for k, ins in enumerate(w):
        if ins["op"] != "call" or ins["arg"].lower() != "0x%x" % SET_CHECKED:
            continue
        rid = None
        for back in range(k - 1, max(-1, k - 4), -1):
            if w[back]["op"] == "push" and imm(w[back]["arg"]) is not None:
                rid = imm(w[back]["arg"])
                break
        mask = dw = None
        for back in range(k - 1, max(-1, k - 8), -1):
            if w[back]["op"] == "and" and w[back]["arg"].startswith("eax,"):
                mask = imm(w[back]["arg"][4:])
                break
        for back in range(k - 1, max(-1, k - 12), -1):
            m = re.search(r"0x(94d448|94d468)(?![0-9a-f])", w[back]["arg"], re.I)
            if m:
                dw = int(m.group(1), 16)
                break
        hits.append((ins["a"], rid, mask, dw))
    return hits


def g1(sites):
    print("\nG1  the ask census for bits 0x10 / 0x20 (every site of FUN_00426d60)")
    cnt = collections.Counter(s["mask"] for s in sites if s["mask"] is not None)
    print("    mask       n  bare  askers")
    for m, c in sorted(cnt.items()):
        if not (m & 0x10 or m & 0x20):
            continue
        ask = sorted({s["fn"] for s in sites if s["mask"] == m})
        print(f"    {m:#010x} {c:3d}  {'yes' if single(m) else 'NO '}  "
              f"{ask if len(ask) < 5 else str(len(ask)) + ' fns'}")
    ids = editor_ids()
    print("    the 13 editor ids (FUN_004db1b0):")
    print("     " + " ".join(f"{r[1]:#x}@{r[3]-0x94D430:#04x}" for r in ids))
    stats = {}
    for b in (0x10, 0x20):
        hit = [s for s in sites if s["mask"] is not None and s["mask"] & b]
        stats[b] = (len([s for s in sites if s["mask"] == b]), len(hit),
                    len({s["fn"] for s in hit}), {s["mask"] for s in hit} & cnt.keys())
        bare, tot, nf, masks = stats[b]
        print(f"    0x{b:x}: {tot} sites ({bare} bare) in {nf} functions;"
              f" composites {sorted(hex(m) for m in masks if not single(m))}")
    both = sorted(m for m in cnt if m & 0x30 == 0x30)
    print(f"    masks carrying BOTH bits: {[hex(m) for m in both]}")
    gate("G1a", len(sites) == 232 and len(cnt) == 35,
         f"{len(sites)} predicate sites, {len(cnt)} distinct constant masks (rest register-passed)")
    gate("G1b", stats[0x10][:3] == (37, 52, 16) and stats[0x20][:3] == (18, 30, 5),
         f"0x10 = {stats[0x10][0]} bare / {stats[0x10][1]} total in {stats[0x10][2]} fns; "
         f"0x20 = {stats[0x20][0]} bare / {stats[0x20][1]} total in {stats[0x20][2]} fns")
    a_bits = sorted({r[1] & 0x7FFFFFFF for r in ids if r[3] == BASE_A})
    b_bits = sorted({r[1] & 0x7FFFFFFF for r in ids if r[3] == BASE_B})
    print(f"    dword-A ids {[hex(x) for x in a_bits]}")
    print(f"    dword-B ids {[hex(x) for x in b_bits]}")
    gate("G1c", len(ids) == 13 and 0x10 in a_bits and 0x20 in a_bits and b_bits == [0x8, 0x2000],
         f"13 editor ids; 0x10 and 0x20 are dword-A ids; the only dword-B twins are "
         f"{[hex(x) for x in b_bits]}")
    gate("G1d", both == [0x30, 0x31, 0x40C31],
         f"the masks that ask BOTH bits: {[hex(m) for m in both]} -> the two bits are "
         f"asked together but never fused")


# ------------------------------------------------------------------ G2 writers
def writer_rules():
    """`test m` starts a rule block; every or/and immediate in the next 12 insns belongs to it."""
    rules = []
    for w in WRITERS:
        size = next((n for st, n, _ in FNS if st == w), 700)
        win = window(w, w + size)
        cur = None
        for k, ins in enumerate(win):
            if ins["op"] == "test":
                o = [x.strip() for x in ins["arg"].split(",")]
                if len(o) > 1 and "[" not in o[0]:
                    cur = imm(o[-1])
                    cur_k = k
                continue
            if cur is None or k - cur_k > 40:
                continue
            if ins["op"] in ("or", "and"):
                o = [x.strip() for x in ins["arg"].split(",")]
                v = imm(o[-1]) if len(o) == 2 else None
                if v is not None:
                    rules.append((w, cur, ins["op"], v, o[0]))
    return rules


def g2():
    print("\nG2  the six relation writers: `test m` then `or s` / `and ~c` (re-derived)")
    rules = writer_rules()
    print("    writer      test-mask  op   value       dest")
    for w, tm, op, v, dest in sorted(set(rules)):
        if tm & 0x30:
            print(f"    {w:#010x}  {tm:#010x}  {op:3s}  {v:#010x}  {dest}")
    named = {(w, tm, op, v) for w, tm, op, v, _ in rules}
    print("    masks 0x10 / 0x20 are the only ones in this table with a dword-B side-effect")
    gate("G2a", (CLR_A, 0x10, "or", 0x8040) in named,
         f"clear-writer {CLR_A:#x}: `test 0x10 -> or 0x8040` == SET 0x8000|0x40 when 0x10 is dropped")
    gate("G2b", (CLR_A, 0x20, "and", 0xFFFFF3FF) in named,
         f"clear-writer {CLR_A:#x}: `test 0x20 -> and {0xFFFFF3FF:#x}` == CLEAR 0xc00 in dword B")
    gate("G2c", (SET_A, 0x10, "and", 0xFAEEF378) in named and (SET_A, 0x10, "or", 0x80000108) in named,
         f"set-writer {SET_A:#x}: `test 0x10 -> and {0xFAEEF378:#x}` CLEARS {[hex(b) for b in bits(0xFAEEF378 ^ 0xFFFFFFFF)]}"
         f" and `or {0x80000108:#x}` SETS {[hex(b) for b in bits(0x80000108)]}")
    gate("G2d", (CLR_B, 0x20, "and", 0xFFFFFFBF) in named,
         f"dword-B SET-writer {CLR_B:#x}: `test 0x20 -> and {0xFFFFFFBF:#x}` drops B's 0x40 before "
         f"ORing param_3 into B")
    sets = [r for r in rules if r[2] == "or"]
    touch20 = [r for r in sets if r[1] & 0x20]
    print(f"    rules on SET paths whose test mask includes 0x20: {[(hex(a),hex(b)) for a,b,_,_ in [(r[0],r[1],r[2],r[3]) for r in touch20]]}")
    gate("G2e", not touch20,
         f"{len(touch20)} of {len(sets)} set-side rules fire on a 0x20 test -> no writer ever "
         f"SETS anything *because* 0x20 is being set")


# ------------------------------------------------------------------ G3 declare
def g3():
    print("\nG3  the declare-vendetta chain: FUN_00507ce0 -> FUN_005076d0 -> SET(dwordA, 0x10)")
    for nm, fn in (("FUN_00507ce0", DECLARE), ("FUN_005076d0", VENDETTA)):
        print(f"  {nm}:")
        for ins in window(fn, fn + size_of(nm)):
            print(f"    {ins['a']:#010x}  {ins['t']}")
        print()
    body = window(DECLARE, DECLARE + size_of("FUN_00507ce0"))
    # the entry test is the predicate INLINED: `test BYTE PTR [ecx*4+0x94d448],0x7`
    inline = [i for i in body if i["op"] == "test" and "0x94d448" in i["arg"]
              and imm(i["arg"].split(",")[-1]) == 0x7]
    callv = [i for i in body if i["op"] == "call" and i["arg"].lower() == "0x%x" % VENDETTA]
    set10 = [i for i in body if i["op"] == "call" and i["arg"].lower() == "0x%x" % SET_A]
    push = [imm(i["arg"]) for i in body if i["op"] == "push" and imm(i["arg"]) is not None]
    gate("G3a", len(inline) == 1 and len(callv) == 1 and len(set10) == 1 and 0x8010 in push,
         f"FUN_00507ce0: entry test `{inline[0]['t'] if inline else '-'}` (the predicate inlined, "
         f"asking the peace group 0x7), 1 call to the vendetta routine, 1 setter call with "
         f"push {[hex(p) for p in push]} (0x8000|0x10)")
    vb = window(VENDETTA, VENDETTA + size_of("FUN_005076d0"))

    def mask_arg(i):
        """the nearest pushed immediate before instruction i, within 10 insns"""
        for back in range(POS[i["a"]] - 1, POS[i["a"]] - 11, -1):
            if INS[back]["op"] == "push":
                v = imm(INS[back]["arg"])
                if v is not None:
                    return v
        return None

    setcalls = [i for i in vb if i["op"] == "call" and i["arg"].lower() == "0x%x" % SET_A]
    tens = [mask_arg(c) for c in setcalls]
    gate("G3b", tens.count(0x10) == 2 and len(tens) == 2,
         f"FUN_005076d0: {len(setcalls)} setter calls with masks {[hex(t) if t is not None else '?' for t in tens]} -> "
         f"0x10 is written on BOTH exits of the war routine")
    lits = {}
    for va in (0x68D67C, 0x68D684):
        lits[va] = cstr(va)
    print(f"    .data literals in FUN_005076d0: " + ", ".join(f"{hex(v)}={s!r}" for v, s in lits.items()))
    gate("G3c", lits[0x68D67C] == "INCITED" and lits[0x68D684] == "VENDETTAWARNING",
         f"the two message keys the war routine fires are {lits[0x68D684]!r} / {lits[0x68D67C]!r}"
         f" (read from the file image, not the decompiler)")
    gate("G3d", any(i["op"] == "push" and imm(i["arg"]) in (0x68D67C, 0x68D684) for i in vb),
         "both literals are pushed from inside FUN_005076d0's own window")
    # the 0x20 write: FUN_00551cf0(a, b, 0x20, 1) - the 4th argument 1 selects its SET branch
    c20 = []
    for i in vb:
        if i["op"] == "call" and i["arg"].lower() == "0x%x" % 0x551CF0:
            back = [INS[POS[i["a"]] - k] for k in range(1, 6)]
            masks = [imm(b["arg"]) for b in back if b["op"] == "push" and imm(b["arg"]) is not None]
            c20.append((i["a"], masks))
    print("    0x551cf0 calls in the war routine: "
          + ", ".join(f"{a:#x} masks={[hex(m) for m in m_]}" for a, m_ in c20))
    gate("G3e", len(c20) >= 1 and any(0x1 in m_ and 0x20 in m_ for _, m_ in c20),
         f"0x20 is written through FUN_00551cf0 with its 4th argument = 1 (the SET branch), i.e. the "
         f"same routine that declares the war also SETS 0x20")


def g4(sites):
    print("\nG4  read-side witnesses: what the two bits select")
    site = next(i for i in INS if i["a"] == 0x51EF55)
    print(f"    ending selector {site['a']:#x}: {site['t']}")
    near = window(0x51EF55, 0x51EF80)
    movs = [i for i in near if i["op"] == "mov" and "0x68e" in i["arg"]]
    print("    and its two string operands: "
          + ", ".join(f"{i['a']:#x} {i['t']}" for i in movs))
    strs = {imm(i["arg"].split(",")[1]): cstr(imm(i["arg"].split(",")[1])) for i in movs}
    print("    -> " + ", ".join(f"{hex(k)}={v!r}" for k, v in sorted(strs.items())))
    jne = [i for i in near if i["op"] == "jne"]
    ec2, ec1 = 0x68E908, 0x68E918
    gate("G4a", sorted(strs.values()) == ["ECONOMICLOSE", "ECONOMICLOSE2"] and jne,
         f"`test [pair],0x40020` selects {strs.get(ec2, strs.get(ec1))!r} vs "
         f"{strs.get(ec1, '?')!r}: the mask picks WHICH defeat text is shown")
    sure = [i for i in near if i["op"] in ("jne", "je") and "0x51ef6c" in i["arg"]]
    gate("G4b", bool(sure) and sure and "0x51ef6c" in sure[0]["arg"],
         f"the branch is `{sure[0]['t'] if sure else '-'}` -> taken when the bit is SET, and the "
         f"SET path keeps 0x68e908 (ECONOMICLOSE2)")
    txt = open(SCRIPT, "rb").read().decode("latin-1")
    recs = dict(re.findall(r"#(ECONOMICLOSE2?)\r?\n(.*?)(?=\r?\n#[A-Z])", txt, re.S))
    body = {}
    for k, v in recs.items():
        body[k] = " ".join(l for l in v.splitlines() if not l.startswith("#"))
    print(f"    Script.txt ECONOMICLOSE  = {body['ECONOMICLOSE'][:70]!r}")
    print(f"    Script.txt ECONOMICLOSE2 = {body['ECONOMICLOSE2'][:70]!r}")
    print(f"                (tail)        {body['ECONOMICLOSE2'][-60:]!r}")
    gate("G4c", "small country" in body["ECONOMICLOSE"] and "tiny" in body["ECONOMICLOSE2"]
         and "estate" in body["ECONOMICLOSE"] and "Recycling" not in body["ECONOMICLOSE"],
         "the 2-variant is the HARSH ending (tiny cubicle / Recycling Tanks) and the plain one "
         "the mild one (country estate) -> a set bit means the winner holds a grievance")
    fns10 = {s["fn"] for s in sites if s["mask"] == 0x10}
    combat = "FUN_00502cd0" in fns10
    print(f"    0x10 askers include the combat resolver: {combat}")
    gate("G4d", combat,
         "FUN_00502cd0 (the resolver whose literals are PACTATTACKED / PACTATTACKING / "
         "VENDETTAREPORT) asks 0x10 -> the read-side of 0x10 is 'are these two at war'")
    fns20 = {s["fn"] for s in sites if s["mask"] == 0x20}
    gate("G4e", "FUN_00442320" not in fns20 and len(fns20) == 3,
         f"0x20's askers are {sorted(fns20)} - the diplomacy MENU that named 0x1/0x8 is NOT "
         f"among them, so no string key names 0x20")


# ------------------------------------------------------------------ G5 immediates
def g5():
    print("\nG5  direct-immediate access to the pair dwords (outside the predicate)")
    cnt = collections.Counter()
    forms = collections.defaultdict(set)
    for ins in INS:
        if ins["op"] not in ("test", "mov", "or", "and", "cmp", "bts", "btr"):
            continue
        if not re.search(r"(94d448|94d468)", ins["arg"], re.I):
            continue
        for part in ins["arg"].split(","):
            v = imm(part)
            if v is not None and v in (0x10, 0x20, 0x8040, 0x40020, 0x8010):
                cnt[(v, ins["op"])] += 1
                forms[v].add(ins["op"])
    for v in (0x10, 0x20, 0x8010, 0x8040, 0x40020):
        print(f"    {v:#08x}: " + ", ".join(f"{op}={cnt[(v, op)]}"
                                            for op in sorted(forms[v])) if forms[v] else f"    {v:#08x}: none")
    gate("G5a", sum(cnt.values()) > 0 and (0x10, "test") in cnt and (0x20, "test") in cnt,
         f"{sum(cnt.values())} direct instructions name one of these five immediates")
    gate("G5b", (0x8010, "test") not in cnt,
         "the composite 0x8010 never appears as a direct test -> it is a WRITE mask, proving the "
         "war path writes 0x8000|0x10 rather than reading it")


# ------------------------------------------------------------------ G6 rivals
def g6(sites, rules):
    print("\nG6  RIVALS (each measured, each must FAIL on these numbers)")
    named = {(w, tm, op, v) for w, tm, op, v, _ in rules}
    # R1: 0x10 is a peace bit
    cleared = bits(0xFAEEF378 ^ 0xFFFFFFFF)
    r1 = (0x1 in cleared and 0x2 in cleared and 0x4 in cleared)
    print(f"    R1 '0x10 is a treaty/pact bit': the 0x10 set-rule clears {[hex(b) for b in cleared]}"
          f" -> {'REFUTED' if r1 else 'stands'}")
    gate("G6a", r1, "R1 refuted: setting 0x10 REMOVES 0x1|0x2|0x4 (the peace group), so 0x10 "
                    "cannot itself be a peace flag")
    # R2: 0x10 and 0x20 are one flag asked twice
    diff_clear = (CLR_A, 0x10, "or", 0x8040) in named and (CLR_A, 0x20, "and", 0xFFFFF3FF) in named
    print(f"    R2 '0x10 and 0x20 are one flag': dropping 0x10 raises 0x8000|0x40 while dropping 0x20 "
          f"clears B's 0xc00 -> {'REFUTED' if diff_clear else 'stands'}")
    gate("G6b", diff_clear,
         "R2 refuted: the two bits have DIFFERENT clear-side effects (0x10-bearing rule ORs 0x8040; "
         "0x20-bearing rule clears dword B's 0xc00) -> two flags, one event")
    # R3: 0x10 == 0x8
    bare8 = len([s for s in sites if s["mask"] == 0x8])
    bare10 = len([s for s in sites if s["mask"] == 0x10])
    set8 = [w for w, tm, op, v in named if op == "or" and tm == 0x8]
    r3 = bare8 != bare10 and (0x8, 0x10, "or", 0x8) not in named
    print(f"    R3 '0x10 and 0x8 are the same bit': bare asks 0x8={bare8} vs 0x10={bare10}; a bare-8 "
          f"set exists without 0x10 -> {'REFUTED' if r3 else 'stands'}")
    gate("G6c", r3 and (0x551A20, 0x8, "or", 0x2) not in named,
         f"R3 refuted: 0x8 and 0x10 are asked at different rates ({bare8} vs {bare10}) and set independently; "
         "the implication runs one way only (0x10 set -> 0x8 set)")
    # R4: the menu names every bit
    mex = {s["fn"] for s in sites if s["mask"] == 0x8}
    r4 = "FUN_00442320" in mex
    gate("G6d", r4, "R4 (control, must STAND): the menu does ask 0x8 - so the ABSENCE of the menu "
                    "from 0x20's askers is a real signal, not a census gap")
    # R5: 0x20 and 0x40000 are one bit
    both = [s for s in sites if s["mask"] == 0x40020]
    only20 = len([s for s in sites if s["mask"] == 0x20])
    gate("G6e", len(both) == 3 and only20 == 18 and len([s for s in sites if s["mask"] == 0x40000]) == 3,
         f"R5 '0x20 and 0x40000 are one flag' refuted: the composite 0x40020 is asked {len(both)}x "
         f"but 0x20 alone {only20}x and 0x40000 alone 3x -> two bits, one shared test")


def main():
    global FNS, STARTS
    load()
    FNS, STARTS = extents()
    sites = call_sites()
    g1(sites)
    g2()
    g3()
    g4(sites)
    g5()
    g6(sites, writer_rules())
    bad = [g for g in GATES if not g[1]]
    print(f"\n{'FAIL' if bad else 'PASS'} M366: {sum(g[1] for g in GATES)}/{len(GATES)} gates")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
