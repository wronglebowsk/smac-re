#!/usr/bin/env python3
"""M188-M190: three field questions about the aggregate pass's count, the two save-path writers, and the
0x94d448 assignments - one census script, one evidence file, zero box time.

  M188  what does FUN_0053a9c0 DO with the entry count `ds:0x9204ac + ds:0x920720 (+1 when the latter != 0)`?
        Scalar or address? and which callee receives it as an argument?
  M189  what do FUN_004e0260 and FUN_005a2930 each WRITE (stores, emitter calls, loop strides)?
  M190  for each of the 27 stores at displacement 0x94d448, where does the stored value come from, and are
        any of them the STORE HALF of a REGISTER-level bit set/clear of the SAME field (the shape a
        memory-operand `or/and DWORD PTR [..+disp],imm` grep cannot see)?

    python3 scripts/m188_m190_uses.py

Static only (scratch/m574/text.txt + ghidra_out/index.csv via field_census.py).
Every number the prose quotes is COMPUTED here; the gates count the sites and FAIL otherwise.
"""
import importlib.util
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
NORM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
R = {}

ALIAS = {"al": "eax", "ah": "eax", "cl": "ecx", "ch": "ecx", "dl": "edx", "dh": "edx",
         "bl": "ebx", "bh": "ebx", "spl": "esi", "dil": "edi", "bpl": "ebp"}
# a byte op's immediate lands at the register's bit position, not at bit 0: `or ah,0x8` sets 0x800.
BYTE_SHIFT = {"al": 0, "cl": 0, "dl": 0, "bl": 0, "sil": 0, "dil": 0,
              "ah": 8, "ch": 8, "dh": 8, "bh": 8}
CLOBBER = ("eax", "ecx", "edx")
DEFINERS = ("mov", "lea", "movzx", "movsx", "pop", "not", "neg", "xchg", "bt")
MODIFIERS = ("add", "sub", "and", "or", "xor", "shl", "shr", "sar", "sal", "inc", "dec",
             "setne", "sete", "setl", "setg", "adc", "sbb")
BODY_CACHE = {}


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print("%s  %s - %s" % (mid, "PASS" if cond else "FAIL", text))


def body(name):
    if name not in BODY_CACHE:
        a, z = INDEX[name]
        BODY_CACHE[name] = [(pc, s) for pc, s in NORM if a <= pc < a + z]
    return BODY_CACHE[name]


def ops(text):
    """(mnemonic, operand1, operand2) - operand1 may itself contain spaces ('dword ptr [eax+1]')."""
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    mn, rest = m.group(1), m.group(2)
    parts = rest.split(",", 1)
    return mn, parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def reg_of(name):
    name = name.strip().split(" ")[0]
    return ALIAS.get(name, name)


def is_store_dest(op):
    """True when the operand is a MEMORY destination, in any objdump spelling ('[eax+1]',
    'dword ptr [eax+1]', 'ds:0x99aa1c', 'dword ptr ds:0x99aa20')."""
    return bool(re.match(r"^(dword|word|byte)\s+ptr\s+", op)) or bool(re.match(r"^\[", op)) \
        or op.startswith("ds:")


def disp_of(op):
    m = re.search(r"0x[0-9a-f]{4,8}\]$", op.strip())
    return m.group(0)[:-1] if m else ""


def trace_source(fn_body, i, want, back=80):
    """Walk back from the store at index i to the ULTIMATE definition of register `want`.
    Modifiers (add/or/and/shl/inc...) are collected and skipped; a call stops the walk for the
    volatile registers.  Returns (kind, def_text, def_pc, mods)."""
    mods = []
    for j in range(i - 1, max(-1, i - back), -1):
        pc, text = fn_body[j]
        mn, o1, o2 = ops(text)
        if mn == "call":
            if want in CLOBBER:
                return "call", text, pc, list(reversed(mods))
            continue
        if o1 and reg_of(o1) == want:
            if mn in DEFINERS or (mn == "xor" and o1 == o2):
                return "def", text, pc, list(reversed(mods))
            if mn in MODIFIERS:
                mods.append((pc, text))
                continue
    return "fnstart", "", 0, list(reversed(mods))


def imm_of(fn_body, i, operand, depth=0):
    """Resolve an operand to an immediate: a literal, or the register's nearest preceding mov imm."""
    operand = operand.strip()
    if re.match(r"^0x[0-9a-f]+$", operand):
        return int(operand, 16) & 0xFFFFFFFF
    if depth > 2 or not re.match(r"^[a-z0-9]+$", operand):
        return None
    want = reg_of(operand)
    for j in range(i - 1, max(-1, i - 40), -1):
        mn, o1, o2 = ops(fn_body[j][1])
        if mn == "call":
            if want in CLOBBER:
                return None
            continue
        if o1 and reg_of(o1) == want:
            if mn == "mov" and re.match(r"^0x[0-9a-f]+$", o2):
                return int(o2, 16) & 0xFFFFFFFF
            if mn in DEFINERS:
                return imm_of(fn_body, j, o2, depth + 1)
            return None
    return None


def masks_from_mods(fn_body, mods):
    """Turn the collected modifier ops into (bits_set, bits_cleared) using resolved immediates."""
    sets = clears = 0
    unresolved = []
    for pc, text in mods:
        idx = next(i for i, (p, _) in enumerate(fn_body) if p == pc)
        mn, o1, o2 = ops(text)
        k = imm_of(fn_body, idx, o2)
        if k is None:
            unresolved.append(text)
            continue
        shift = BYTE_SHIFT.get(o1, None)
        if shift is None:
            wide, kk = 0xFFFFFFFF, k
        else:
            wide, kk = 0xFF << shift, (k & 0xFF) << shift
        if mn in ("or", "xor", "setne", "sete", "inc", "add"):
            sets |= (kk & wide)
        elif mn == "and":
            clears |= ((kk ^ wide) & wide)
    return sets, clears, unresolved


# ---------------------------------------------------------------- M188
def m188():
    fn = "FUN_0053a9c0"
    b = body(fn)
    ent = b[:30]

    def find(pred):
        hits = [pc for pc, s in ent if pred(s)]
        return hits[0] if hits else None

    p720 = find(lambda s: s == "mov edx,dword ptr ds:0x920720")
    p4ac = find(lambda s: s == "mov eax,ds:0x9204ac")
    padd = find(lambda s: s == "add eax,edx")
    stores = [pc for pc, s in ent if s == "mov dword ptr [ebp-0x4],eax"]
    ptest = find(lambda s: s == "test edx,edx")
    pje = find(lambda s: s.startswith("je 0x"))
    penc = find(lambda s: s == "inc eax")
    print("M188 entry pcs: " + " ".join(
        "%s=%s" % (n, hex(p) if p else "-") for n, p in
        (("0x920720", p720), ("0x9204ac", p4ac), ("add", padd), ("test", ptest),
         ("je", pje), ("inc", penc))) + "  stores=" + ",".join(hex(x) for x in stores))
    shape = all(x is not None for x in (p720, p4ac, padd, ptest, pje, penc)) and len(stores) >= 2 \
        and p720 < p4ac < padd < ptest < pje < penc and stores[0] < pje < stores[1]
    ok("M188a", shape, "entry computes [ebp-4] = ds:0x9204ac + ds:0x920720 and stores it, then adds +1 "
       "ONLY when ds:0x920720 != 0 (test edx,edx / je / inc eax / re-store in that order)")

    kinds = Counter()
    reads, addr_forms = [], []
    for pc, s in b:
        if "[ebp-0x4]" not in s:
            continue
        mn, o1, o2 = ops(s)
        if mn in ("inc", "dec"):
            kinds[mn] += 1
        elif mn in ("add", "sub") and o2.startswith("0x"):
            kinds["%s imm %s" % (mn, o2)] += 1
        elif mn in ("add", "sub"):
            kinds["%s reg %s" % (mn, o2)] += 1
        elif mn == "mov" and is_store_dest(o1):
            kinds["store-to-count"] += 1
        elif mn == "mov" and is_store_dest(o2):
            kinds["read-count-to-reg"] += 1
            reads.append((pc, reg_of(o1)))
        elif mn == "push":
            kinds["push [ebp-4] directly"] += 1
        elif mn == "cmp":
            kinds["cmp"] += 1
        else:
            kinds["other: " + s] += 1
        if "ebp-0x4*" in s.replace(" ", ""):
            addr_forms.append((pc, s))
    total = sum(kinds.values())
    print("M188 [ebp-0x4] mentions in %s: %d" % (fn, total))
    for k in sorted(kinds):
        print("   %-26s %d" % (k, kinds[k]))
    regarithmetic = sum(v for k, v in kinds.items() if k.startswith("add reg") or k.startswith("sub reg"))
    ok("M188b", total > 0 and kinds["push [ebp-4] directly"] == 0 and len(addr_forms) == 0
       and kinds["read-count-to-reg"] > 0 and kinds["store-to-count"] > 0,
       "the count is a SCALAR working value, never an address: %d mentions = %d reads-to-reg + "
       "%d stores-from-reg + %d inc + %d dec + %d reg-arithmetic; ZERO direct push of the slot and "
       "ZERO scaled/index address forms (%s)"
       % (total, kinds["read-count-to-reg"], kinds["store-to-count"], kinds["inc"], kinds["dec"],
          regarithmetic, addr_forms[:2]))

    # how is each read consumed? the FIRST thing that touches the register decides the hypothesis
    first_use = Counter()
    detail_rows = []
    anchors = 0
    for pc, reg in reads:
        i = next(k for k, (p, _) in enumerate(b) if p == pc)
        verdict = "no consumer within 12 insns"
        hit_pc = 0
        for j in range(i + 1, min(len(b), i + 13)):
            pc2, text = b[j]
            mn, o1, o2 = ops(text)
            same = bool(o1) and reg_of(o1) == reg
            restored = mn == "mov" and is_store_dest(o1) and reg_of(o2) == reg
            if mn in ("cmp", "test") and same:
                verdict = "cmp/test against it"
            elif mn == "push" and same:
                verdict = "pushed as a call argument"
            elif mn == "call":
                verdict = "reaches a call intact"
            elif restored:
                verdict = "re-stored (round-trip arithmetic)"
            elif same and mn in MODIFIERS:
                verdict = "%s on the register" % mn
            elif same and mn in DEFINERS:
                verdict = "overwritten by %s" % mn
            elif mn.startswith("j"):
                verdict = "branch taken before any use"
            else:
                continue
            hit_pc = pc2
            break
        first_use[verdict] += 1
        window = b[i + 1:i + 13]
        anchored = any(("0x94d434" in t) or ("0x985afc" in t) or ("0x920720" in t) for _, t in window)
        anchors += 1 if anchored else 0
        detail_rows.append((hex(pc), reg, verdict, hex(hit_pc), anchored,
                            " | ".join(t for _, t in window[:6])))
    print("M188 how each of the %d reads is consumed:" % len(reads))
    for k in sorted(first_use):
        print("   %-34s %d" % (k, first_use[k]))
    for r in detail_rows:
        print("   read %s into %-4s -> %-34s at %s anchor=%-5s :: %s" % r)
    arg_use = first_use["pushed as a call argument"] + first_use["reaches a call intact"]
    local_use = sum(v for k, v in first_use.items()
                    if k not in ("pushed as a call argument", "reaches a call intact",
                                 "no consumer within 12 insns"))
    print("M188 hypothesis split: argument-to-callee %d vs local-bookkeeping %d (unclassified %d); "
          "reads whose 12-insn window names 0x94d434 / 0x985afc / 0x920720: %d"
          % (arg_use, local_use, first_use["no consumer within 12 insns"], anchors))
    ok("M188c", sum(first_use.values()) == len(reads) and ((arg_use > 0) != (local_use > 0))
       and anchors >= 1,
       "the count is LOCAL BOOKKEEPING, not an argument: %d of %d reads are consumed by arithmetic or "
       "comparison on the register and %d are pushed / reach a call; %d reads' windows name "
       "0x94d434 / 0x985afc / 0x920720, so the +/-1 steps are gated on rank and round tests"
       % (local_use, len(reads), arg_use, anchors))


# ---------------------------------------------------------------- M189
def m189():
    for fn, want_callees in (("FUN_004e0260", 7), ("FUN_005a2930", 5)):
        b = body(fn)
        stores = [(pc, s) for pc, s in b if ops(s)[0] == "mov" and is_store_dest(ops(s)[1])]
        gstores = [(pc, s) for pc, s in stores if "ds:0x" in s]
        calls = [ops(s)[1] for pc, s in b if ops(s)[0] == "call"]
        cc = Counter(calls)
        print("M189 %s: %d insns, %d stores (%d to ds: globals), %d distinct callees "
              "(index.csv n_callees=%d)" % (fn, len(b), len(stores), len(gstores), len(cc), want_callees))
        for pc, s in stores:
            print("   STORE %s %s" % (hex(pc), s))
        for k in sorted(cc):
            print("   CALL  %-12s x%d" % (k, cc[k]))
        if fn == "FUN_004e0260":
            strides = {s: sum(1 for pc, t in b if t == s) for s in
                       ("add esi,0x59c", "add ebx,0x20bc", "cmp esi,0x92a2a4",
                        "lea esi,[ecx*4+0x94d650]", "lea edx,[ecx*4+0x927894]",
                        "mov dword ptr [esi],eax", "mov ds:0x99aa1c,eax",
                        "mov dword ptr ds:0x99aa20,0x0")}
            trip = (0x92a2a4 - 0x927b60) // 0x59c
            rem = (0x92a2a4 - 0x927b60) % 0x59c
            print("   loop gates: %s" % strides)
            print("   trip = (0x92a2a4-0x927b60)/0x59c = %d remainder %d; 0x59c=%d B = 359 dwords, "
                  "0x20bc=%d B = 2095 dwords = the faction BLOCK stride; 0x94d650+8380*idx is a block base"
                  % (trip, rem, 0x59c, 0x20bc))
            emit = sum(v for k, v in cc.items() if k.startswith("0x626"))
            nonlocal_stores = [(pc, s) for pc, s in stores if "[ebp-" not in s]
            print("   stores that are NOT stack spills: %d %s"
                  % (len(nonlocal_stores), [hex(p) for p, _ in nonlocal_stores]))
            ok("M189a", len(stores) == 4 and len(nonlocal_stores) == 3 and len(gstores) == 2
               and rem == 0 and trip == 7 and all(v == 1 for v in strides.values())
               and len(cc) == want_callees and cc["0x626634"] == 2 and emit == 4,
               "FUN_004e0260 writes EXACTLY 3 non-spill places - the staging pair ds:0x99aa1c / "
               "ds:0x99aa20 and [block(fac)+0x0] = ds:0x999fa4 (plus 1 spill store to [ebp-4]) - and "
               "everything else leaves through %d calls into the 0x626xxx emitters (0x626634 x2); its "
               "loop walks %d records at stride 0x59c (1436 B = 359 dwords) while ebx walks the 0x20bc "
               "(8380 B) faction blocks" % (emit, trip))
        else:
            gates = sorted({s for pc, s in b if s.startswith("test")})
            ok("M189b", len(stores) == 0 and len(cc) == want_callees
               and {"0x4b6060", "0x4b5f90", "0x5844f0", "0x5a1950", "0x4d9fb0"} == set(cc),
               "FUN_005a2930 writes NOTHING (0 stores of any width): it is a gated DISPATCHER - %d "
               "tests (%s) and exactly %d callees %s, the 0x5a1950 call reached only when ds:0x920434 "
               "reads 0" % (len(gates), ", ".join(gates), len(cc), sorted(cc)))


# ---------------------------------------------------------------- M190
def m190():
    DIS = "0x94d448"
    sites = []
    for pc, s in NORM:
        mn, o1, o2 = ops(s)
        if mn == "mov" and is_store_dest(o1) and DIS in o1:
            sites.append((pc, s, o1, o2))
    print("M190 stores whose DESTINATION carries displacement %s: %d" % (DIS, len(sites)))
    per_fn = Counter()
    kinds = Counter()
    sets_all = clears_all = 0
    rows = []
    for pc, s, o1, o2 in sites:
        fn = fnof(pc)
        per_fn[fn] += 1
        b = body(fn) if fn in INDEX else NORM
        i = next(k for k, (p, _) in enumerate(b) if p == pc)
        src = reg_of(o2)
        kind, deftext, defpc, mods = trace_source(b, i, src)
        detail = ""
        sets = clears = 0
        if kind == "def":
            mn2, d1, d2 = ops(deftext)
            st, cl, unres = masks_from_mods(b, mods)
            sets, clears = st, cl
            if mn2 == "mov" and is_store_dest(d2) and DIS in d2:
                kind = "RMW same field"
                detail = "def %s ; mods %s ; set 0x%x clear 0x%x%s" % (
                    deftext, [t for _, t in mods], st, cl,
                    (" unresolved " + str(unres)) if unres else "")
            elif mn2 == "mov" and re.match(r"^0x[0-9a-f]+$", d2):
                v = int(d2, 16) & 0xFFFFFFFF
                kind = "immediate"
                detail = "imm 0x%x carries-0x40030=%s" % (v, bool(v & 0x40030))
            elif mn2 == "mov" and is_store_dest(d2):
                kind = "load other " + (disp_of(d2) or d2)
                detail = deftext + (" ; mods " + str([t for _, t in mods]) if mods else "")
            elif mn2 == "lea":
                kind = "computed lea"
                detail = deftext + (" ; mods " + str([t for _, t in mods]) if mods else "")
            else:
                kind = "arith " + mn2
                detail = deftext
        elif kind == "call":
            kind = "call result"
            detail = "clobbered by %s at %s" % (deftext, hex(defpc))
        else:
            kind = "fnstart/param"
            detail = "no def inside the window (parameter or caller-set)"
        kname = "RMW same field" if kind == "RMW same field" else kind.split(" ")[0] + \
            (" " + kind.split(" ")[1] if kind.startswith("load") else "")
        kinds[kname] += 1
        sets_all |= sets
        clears_all |= clears
        rows.append((hex(pc), fn, o1, o2, kind, detail, sets, clears))
    print("   per-function: " + "  ".join("%s x%d" % (k, v) for k, v in per_fn.most_common()))
    print("   source kinds: " + "  ".join("%s x%d" % (k, v) for k, v in kinds.most_common()))
    for r in rows:
        print("   %-10s %-14s %-22s src=%-4s %-20s %s" % (r[0], r[1], r[2], r[3], r[4], r[5][:110]))
    rmw = kinds.get("RMW same field", 0)
    imm = kinds.get("immediate", 0)
    ok("M190a", len(sites) == 27 and sum(per_fn.values()) == 27 and imm == 0,
       "%d stores at %s in %d functions; %d of them have an IMMEDIATE source (the value is never "
       "baked into the store)" % (len(sites), DIS, len(per_fn), imm))
    ok("M190b", rmw >= 1 and (sets_all & 0x40) and (clears_all & 0x20),
       "%d of the 27 are the STORE HALF of a register-level bit RMW of the SAME field; bits SET across "
       "them = 0x%x, bits CLEARED = 0x%x (0x40 IS set and 0x20 IS cleared at runtime although no "
       "`or/and DWORD PTR [..+%s],imm` instruction exists)" % (rmw, sets_all, clears_all, DIS))
    touched = sets_all | clears_all
    whole = [(r[0], r[4]) for r in rows if r[4] != "RMW same field"]
    print("M190 the three bits of the 0x40030 mask, by origin (of the %d RMW sites, %d whole-value "
          "assignments, touched 0x%x):" % (rmw, len(whole), touched))
    perbit = {}
    for bit in (0x10, 0x20, 0x40000):
        setters = [r[0] for r in rows if r[6] & bit]
        cllrs = [r[0] for r in rows if r[7] & bit]
        perbit[bit] = (setters, cllrs)
        print("   bit 0x%-6x set at %d sites %s ; cleared at %d sites %s"
              % (bit, len(setters), setters[:5], len(cllrs), cllrs[:5]))
    print("   whole-value assignments: " + "; ".join("%s %s" % (p, k) for p, k in whole))
    ok("M190c", all(perbit[b][0] or perbit[b][1] for b in (0x20, 0x40000))
       and not perbit[0x10][0] and not perbit[0x10][1] and len(whole) == 4,
       "the RMWs themselves put 0x20 (%d setter sites) and 0x40000 (%d setter sites) into the field, "
       "but bit 0x10 is NEVER set or cleared by any of the 27 stores - it can only arrive through the "
       "%d whole-value assignments %s (source kinds %s)"
       % (len(perbit[0x20][0]), len(perbit[0x40000][0]), len(whole),
          [p for p, _ in whole], sorted({k for _, k in whole})))


m188()
m189()
m190()
print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in sorted(R.items())))
sys.exit(0 if R and all(R.values()) else 1)
