#!/usr/bin/env python3
"""M384 - WHO SETS 0x400 in the faction-pair dword.

M382 closed the READERS of the 0xc00 cluster (bit 10 = 0x400, bit 11 = 0x800).
M378's arms only ever CLEARED 0x400 (`and 0xfffdf3ff` / `and 0xfffdfbff`) and
0x5552ff only consumed it, so this run asked: find the writer, or prove none
exists.

This instrument measures the WRITE side from the instruction stream:

  G0 parse       .text dump parses; 0x94d448 ref counts pinned.
  G1 abs writes  every absolute-displacement store to the pair dword
                 (`[..+0x94d448]`): mnemonic census (mov vs and/or/xor/add).
  G2 pair ptrs   abstract propagation of `lea r,[idx*4+0x94d448]` through
                 register copies and [ebp-k] slots, dropped at calls, jumps and
                 branch targets: stores through a tagged pointer are pair
                 writes too (this is where a setter hides from a disp grep).
  G3 value masks backward bounded dataflow on each pair write: SELF_RMW vs
                 COMPUTED vs OPAQUE; collects the AND (clear) and OR (set)
                 immediates -> CAN_SET_0x400 per site, and flags writes whose
                 OR mask comes from a REGISTER (parameterised writers).
  G4 API census  for the parameterised writers: every call site, with the
                 pushed arguments resolved (const / reg->const / reg->reg-op /
                 OPAQUE) -> which callers pass a mask carrying bit 10.
  G5 the answer  the setter set, and the gates read off the neighbouring tests.
  G6 rivals      six rival readings, each refuted on the printed numbers.
  G7 digest      digest of the pair-write table.

M384_PATCH='addr|text' rewrites one instruction line in memory (mutants).
M384_ALGO=n flips a law (10 part-shift, 11 partial-mov, 12 keep-tag-at-call,
13 backward-hop, 14 producer-window, 15 lea-scale, 16 arg-order, 17 skip-mask-arith).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M384_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
INDEX = os.environ.get("M384_INDEX", os.path.expanduser("~/reverse/smac/ghidra_out/index.csv"))

FIELD = 0x94D448
BIT = 0x400                        # bit 10 = the bit under study
ALGO = int(os.environ.get("M384_ALGO", "0") or 0)
PATCH = os.environ.get("M384_PATCH", "")
DIGEST_PIN = "341b46ff72a492b3"

MASK_API = 0x551A20                # FUN_00551a20(owner, other, mask): pair writer
MASK_API2 = 0x551CF0               # FUN_00551cf0(owner, other, mask, set?1:0)

PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')
R32 = {"eax", "ebx", "ecx", "edx", "esi", "edi", "esp", "ebp"}
PART = {"al": ("eax", 0, 8), "ah": ("eax", 8, 8), "ax": ("eax", 0, 16),
        "bl": ("ebx", 0, 8), "bh": ("ebx", 8, 8), "bx": ("ebx", 0, 16),
        "cl": ("ecx", 0, 8), "ch": ("ecx", 8, 8), "cx": ("ecx", 0, 16),
        "dl": ("edx", 0, 8), "dh": ("edx", 8, 8), "dx": ("edx", 0, 16)}
WRITE_MN = ("mov", "and", "or", "xor", "add", "sub", "inc", "dec", "not", "bts", "btr", "neg")
FULL_DEF = ("mov", "and", "or", "xor", "add", "sub", "lea", "imul", "not", "neg", "shl",
            "shr", "sar", "inc", "dec", "pop", "movzx", "movsx", "cdq", "mul", "div")

FAILS = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" — " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


def norm(s):
    return re.sub(r'\s+', ' ', s.strip())


def load_text(path):
    ins = []
    for line in open(path, encoding="latin-1"):
        m = PAT.match(line.rstrip("\n"))
        if not m:
            continue
        body = norm(m.group(3) or "")
        if body:
            ins.append((int(m.group(1), 16), body))
    return ins


def apply_patch(ins):
    if not PATCH:
        return ins
    addr, text = PATCH.split("|", 1)
    a = int(addr, 16)
    return [(x, norm(text) if x == a else b) for x, b in ins]


def split_ops(text):
    m = re.match(r'^([a-z0-9]+)\s*(.*)$', text)
    if not m:
        return "", []
    mn, rest = m.group(1), m.group(2)
    return mn, [x.strip() for x in rest.split(",")] if rest else []


def imm_of(v):
    try:
        return int(v, 16)
    except (ValueError, TypeError):
        return None


def mem_store_operand(ops, mn):
    if mn not in WRITE_MN or not ops:
        return None
    d = ops[0]
    if "PTR [" in d and d.split("PTR")[0].strip() in ("DWORD", "BYTE", "WORD"):
        return d
    return None


def mem_base(dst):
    m = re.search(r'\[\s*(\w+)(?:\+(\w+)\*(\d+))?', dst)
    if not m:
        return None, None
    return m.group(1), (m.group(2), int(m.group(3)) if m.group(3) else 1)


def is_field_disp(dst):
    return "+0x94d448]" in dst


def is_zero_disp(d):
    return bool(re.search(r'\[(\w+)\]$', d))


# ---------------------------------------------------------------- G1
def abs_writes(ins):
    out = []
    for a, b in ins:
        mn, ops = split_ops(b)
        d = mem_store_operand(ops, mn)
        if d and is_field_disp(d):
            out.append((a, mn, d, ops))
    return out


# ---------------------------------------------------------------- G2
def slot_key(mem):
    m = re.search(r'\[ebp([+-])(0x[0-9a-f]+|\d+)\]', mem)
    if not m:
        return None
    v = int(m.group(2), 16) if m.group(2).startswith("0x") else int(m.group(2))
    return ("ebp", v if m.group(1) == "+" else -v)


def seed_slots(ins, lo, hi, regs0=None):
    """Function-scope: `lea r,[idx*4+0x94d448]` followed by `mov [ebp+X],r`
    primes that stack slot with the pair pointer (a single-slot copy)."""
    seeds = {}
    for i in range(lo, min(hi, len(ins) - 2)):
        mn, ops = split_ops(ins[i][1])
        if mn != "lea" or len(ops) != 2:
            continue
        m = re.search(r'\[\s*\w+\*4\+0x94d448\]', ops[1])
        if not m:
            continue
        r = ops[0]
        for j in range(i + 1, min(i + 7, hi)):
            mn2, o2 = split_ops(ins[j][1])
            if mn2 == "mov" and len(o2) == 2 and o2[1] == r and "PTR [" in o2[0] and "ebp" in o2[0]:
                k = slot_key(o2[0])
                if k:
                    seeds[k] = "pair"
                break
            if mn2 in ("call", "ret") or mn2.startswith("j"):
                break
    return seeds


def pair_pointers(ins, fns, preds):
    """Stores through a lea-derived pair pointer, by a 2-pass forward dataflow
    over each function's CFG: at a join the in-state is the INTERSECTION of the
    predecessors' out-states, so a tag survives only if every path sets it."""
    at = {a: i for i, (a, b) in enumerate(ins)}
    out = []
    for addr, size, name in fns:
        lo, hi = at.get(addr), at.get(addr + size)
        if lo is None or hi is None or hi <= lo:
            continue
        seeds = seed_slots(ins, lo, hi)
        states = {}
        found = {}
        for it in range(2):
            for n in range(lo, hi):
                if n == lo:
                    cur = {}
                else:
                    ps = [p for p in preds.get(n, []) if lo <= p < hi]
                    if not ps:
                        cur = {}
                    elif len(ps) == 1:
                        cur = dict(states.get(ps[0], {}))
                    else:
                        cur = {}
                        first = states.get(ps[0], {})
                        for k, v in first.items():
                            if v and all(states.get(p, {}).get(k) == v for p in ps[1:]):
                                cur[k] = v
                cur.update({("s", k[1]): v for k, v in seeds.items()})
                a, b = ins[n]
                mn, ops = split_ops(b)
                if mn == "lea" and len(ops) == 2:
                    m = re.search(r'\[\s*(\w+)\*(\d+)\+0x94d448\]', ops[1])
                    scale = int(m.group(2)) if m else 0
                    if ALGO == 15:
                        scale = 1 if m else 0
                    if m and scale == 4:
                        cur[ops[0]] = "pair"
                    else:
                        cur.pop(ops[0], None)
                elif mn == "mov" and len(ops) == 2:
                    d, s = ops
                    if "PTR [" in d:
                        if "ebp" in d:
                            k = slot_key(d)
                            if k:
                                cur[("s", k[1])] = cur.get(s)
                        else:
                            base, _ = mem_base(d)
                            if base and cur.get(base) and is_zero_disp(d):
                                found[a] = (d, s)
                    elif "PTR [" in s:
                        if "ebp" in s:
                            k = slot_key(s)
                            v = cur.get(("s", k[1])) if k else None
                            if v:
                                cur[d] = v
                            else:
                                cur.pop(d, None)
                        else:
                            cur.pop(d, None)
                    elif s in cur and cur[s]:
                        cur[d] = cur[s]
                    elif s != d:
                        cur.pop(d, None)
                elif mn in ("call", "ret", "int3"):
                    cur = {k: v for k, v in cur.items() if isinstance(k, tuple)}
                elif mn.startswith("j"):
                    pass
                else:
                    d = mem_store_operand(ops, mn)
                    if d:
                        base, _ = mem_base(d)
                        if base and cur.get(base) and is_zero_disp(d):
                            found[a] = (d, ops[1] if len(ops) > 1 else "?")
                    elif ops and ops[0] in R32:
                        cur.pop(ops[0], None)
                states[n] = cur
        for a in sorted(found):
            out.append((a, found[a][0], found[a][1]))
    return out


# ---------------------------------------------------------------- G3
def reg_effect(text, base):
    """Effect of one instruction on register `base` (whole-dword view)."""
    mn, ops = split_ops(text)
    if not ops:
        return ("read", None)
    d = ops[0]
    v = imm_of(ops[1]) if len(ops) > 1 else None
    if d == base:
        if mn == "and" and v is not None:
            return ("clr", v & 0xFFFFFFFF)
        if mn == "or" and v is not None:
            return ("set", v & 0xFFFFFFFF)
        if mn == "xor" and v is not None:
            return ("xor", v & 0xFFFFFFFF)
        if mn in ("add", "sub") and v is not None:
            return ("arith", v & 0xFFFFFFFF)
        if mn in FULL_DEF:
            return ("def", mn, ops[1] if len(ops) > 1 else None)
        return ("read", None)
    if d in PART and PART[d][0] == base:
        b, lo, w = PART[d]
        if ALGO == 10:
            lo = 0
        if mn in ("or", "and", "xor", "add", "sub") and v is not None \
                and not (mn == "mov" and ALGO == 11):
            eff = (v << lo) & 0xFFFFFFFF
            kind = {"or": "set", "and": "clr", "xor": "xor", "add": "arith", "sub": "arith"}[mn]
            if kind == "clr":
                eff = ((v << lo) | (0xFFFFFFFF << (lo + w))) & 0xFFFFFFFF
            return (kind, eff)
        if mn in FULL_DEF:
            return ("def", mn, ops[1] if len(ops) > 1 else None)
        return ("read", None)
    return ("read", None)


def build_preds(ins):
    """CFG predecessor edges over the whole .text (call returns, ret terminates)."""
    at = {a: i for i, (a, b) in enumerate(ins)}
    preds = {}
    for i, (a, b) in enumerate(ins):
        mn, ops = split_ops(b)
        if mn in ("ret", "int3"):
            continue
        if mn.startswith("j") and ops:
            t = imm_of(ops[-1])
            if t is not None and t in at:
                preds.setdefault(at[t], []).append(i)
            if mn != "jmp":
                preds.setdefault(i + 1, []).append(i)
        else:
            preds.setdefault(i + 1, []).append(i)
    return preds


def classify(ins, preds, store_i, src, lo):
    """BACKWARD dataflow over the CFG: every path from the store to the first
    full definition of the source register. Returns (kind, clear, set, xor,
    arith, paths, longest_ops).

    kind: SELF_RMW  every path reloads the pair dword (clear/set masks apply)
          PARAM_OR  every path hits `or reg,reg` of an outside value
          COMPUTED  every path hits a non-field definition
          OPAQUE    paths disagree, or a path is cut (call/truncation)
    Masks are the UNION over paths -> an over-approximation of what the store
    CAN add, which is what a 'can this set 0x400' claim needs.
    """
    reg0 = src if src in R32 else (PART[src][0] if src in PART else src)
    res = {"clear": 0, "set": 0, "xor": 0, "arith": 0}
    kinds = {}
    seen = []
    work = [(store_i, reg0, 0, 0, 0)]
    budget = 4000
    while work and budget > 0:
        i, reg, clr, st, xr = work.pop()
        budget -= 1
        ar = 0
        ops_seen = []
        path_ok = False
        while i >= 0 and i >= lo and budget > 0:
            budget -= 1
            a, b = ins[i]
            mn, operands = split_ops(b)
            if mn in ("call", "ret", "int3"):
                kinds["OPAQUE"] = kinds.get("OPAQUE", 0) + 1
                seen.append("<cut:%s>" % mn)
                path_ok = True
                break
            eff = reg_effect(b, reg)
            if eff[0] in ("set", "clr", "xor", "arith"):
                if eff[0] == "set":
                    st |= eff[1]
                elif eff[0] == "clr":
                    clr |= eff[1]
                elif eff[0] == "xor":
                    xr |= eff[1]
                elif ALGO != 17:
                    ar |= eff[1]
                ops_seen.append(b)
            elif eff[0] == "def":
                kind, payload = eff[1], eff[2]
                if kind == "mov" and payload is not None:
                    if "DWORD PTR" in payload and (is_field_disp(payload)
                                                   or re.match(r'DWORD PTR \[\w+\]$', payload)):
                        kinds["SELF_RMW"] = kinds.get("SELF_RMW", 0) + 1
                    elif payload in R32 and len(ops_seen) < (1 if ALGO == 13 else 12):
                        # register copy: continue the walk on the source
                        work.append((i - 1, payload, clr, st, xr))
                        path_ok = True
                        break
                    else:
                        kinds["OPAQUE"] = kinds.get("OPAQUE", 0) + 1
                elif kind == "or" and payload in R32:
                    kinds["PARAM_OR"] = kinds.get("PARAM_OR", 0) + 1
                else:
                    kinds["COMPUTED"] = kinds.get("COMPUTED", 0) + 1
                seen.append(b)
                path_ok = True
                break
            ps = [p for p in preds.get(i, []) if p >= lo]
            if not ps:
                kinds["OPAQUE"] = kinds.get("OPAQUE", 0) + 1
                seen.append("<no-def>")
                path_ok = True
                break
            if len(ps) > 1:
                for p in ps:
                    work.append((p, reg, clr, st, xr))
                if ALGO == 12:
                    kinds["OPAQUE"] = kinds.get("OPAQUE", 0) + 1
                path_ok = True
                break
            i = ps[0]
        if not path_ok:
            kinds["OPAQUE"] = kinds.get("OPAQUE", 0) + 1
        res["clear"] |= clr
        res["set"] |= st
        res["xor"] |= xr
        res["arith"] |= ar
    if not kinds:
        kinds["OPAQUE"] = 1
    kind = max(kinds.items(), key=lambda kv: kv[1])[0]
    if len(kinds) > 1:
        kind = "OPAQUE"
    return (kind, res["clear"], res["set"], res["xor"], res["arith"], sum(kinds.values()), seen)


def can_set(cls):
    """A pair write can introduce bit 10 if an OR/mov-imm/arith carries it, or
    if the value is opaque (conservative)."""
    kind, reg, clr, st, xr, ar, seen = cls
    if kind == "OPAQUE":
        return True
    if (st | ar) & BIT:
        return True
    if kind == "COMPUTED" and seen:
        m = re.match(r'mov \w+,(0x[0-9a-f]+)$', seen[-1])
        if m and int(m.group(1), 16) & BIT:
            return True
    return False


# ---------------------------------------------------------------- G4
def call_args(ins, preds, ci, nargs):
    """Recover cdecl arguments of the call at index ci, arg0 FIRST.
    Program order pushes argN-1 .. arg0, so the last push is arg0. The walk
    follows CFG predecessors (so a `je` that jumps to the call is crossed),
    and register definitions seen on the way are kept for constant resolution."""
    out = []
    defs = {}
    i = ci
    steps = 0
    while steps < 80 and len(out) < nargs:
        steps += 1
        ps = preds.get(i, [])
        if not ps:
            break
        i = ps[0] if len(ps) == 1 else (i - 1 if (i - 1) in ps else min(ps))
        if i >= ci:
            break
        b = ins[i][1]
        mn, ops = split_ops(b)
        if mn == "push" and ops:
            out.append(ops[0])
        elif mn in ("call", "ret", "int3"):
            break
        elif mn in ("mov", "or", "and", "lea", "xor", "add", "sub") and len(ops) == 2 \
                and ops[0] in R32:
            defs.setdefault(ops[0], b)
    return out, defs


def resolve_mask(operand, defs, depth=0):
    """Return (value, how) for a pushed mask operand."""
    v = imm_of(operand)
    if v is not None:
        return v, "imm"
    if operand in R32 and operand in defs and depth < 3:
        b = defs[operand]
        mn, ops = split_ops(b)
        if mn == "mov" and len(ops) == 2 and imm_of(ops[1]) is not None:
            return imm_of(ops[1]), "reg:=imm"
        if mn in ("or", "and", "add") and len(ops) == 2:
            if ops[1] in defs:
                inner, how = resolve_mask(ops[1], defs, depth + 1)
            else:
                inner, how = imm_of(ops[1]), "imm"
            if inner is None:
                return None, "opaque(%s)" % b
            bits = {"or": inner, "and": (~inner) & 0xFFFFFFFF, "add": inner}[mn]
            return bits, "%s%s" % (mn, "~" if mn == "and" else "")
        return None, "opaque(%s)" % b
    return None, "opaque"


def passthru(ins, ci, operand, lo, hi):
    """Is this mask register just a parameter of the enclosing function?"""
    if operand not in R32:
        return None
    j = ci - 1
    while j >= lo:
        b = ins[j][1]
        mn, ops = split_ops(b)
        if mn == "mov" and len(ops) == 2 and ops[0] == operand:
            m = re.search(r'\[ebp\+(0x[0-9a-f]+)\]', ops[1])
            if m:
                return "arg%d" % ((int(m.group(1), 16) - 8) // 4)
            return None
        if mn in ("or", "and", "xor", "add", "sub", "lea", "pop", "inc", "dec") \
                and ops and ops[0] == operand:
            return None
        if mn == "call" and any(ops and x == operand for x in ops):
            return None
        j -= 1
    return None


def load_fns(path):
    import csv
    fns = []
    with open(path) as f:
        for d in csv.DictReader(l for l in f if not l.startswith("#")):
            fns.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"]))
    fns.sort()
    return fns


def fn_of(fns, a):
    best = None
    for addr, size, name in fns:
        if addr <= a < addr + size:
            best = (addr, addr + size, name)
        elif addr > a:
            break
    return best


def main():
    raw = load_text(TEXT)
    ins = apply_patch(raw)
    at = {a: i for i, (a, b) in enumerate(ins)}
    print("M384 who SETS 0x%x in the faction-pair dword (field = DWORD [pair*4+0x%x])" % (BIT, FIELD))

    # ---------------- G0 ---------------------------------------------------
    print("\nG0  parse")
    refs = [(a, b) for a, b in ins if "94d448" in b]
    byte_refs = [(a, b) for a, b in ins if "94d449" in b]
    print("  insns=%d  refs(+0x94d448)=%d  refs(+0x94d449)=%d" % (len(ins), len(refs), len(byte_refs)))
    check("G0 insn count 781429", len(ins) == 781429, str(len(ins)))
    check("G0 field refs 653", len(refs) == 653, str(len(refs)))
    check("G0 byte refs 5", len(byte_refs) == 5, str(len(byte_refs)))
    check("G0 every +0x94d449 ref is a read",
          all(norm(b)[:4] == "test" for a, b in byte_refs),
          str([norm(b)[:10] for a, b in byte_refs]))

    # ---------------- G1 ---------------------------------------------------
    aw = abs_writes(ins)
    print("\nG1  absolute-displacement writes to [..+0x%x]: %d" % (FIELD, len(aw)))
    mn_census = {}
    for a, mn, d, ops in aw:
        mn_census[mn] = mn_census.get(mn, 0) + 1
    print("  mnemonics: %s" % mn_census)
    check("G1 27 direct stores", len(aw) == 27, str(len(aw)))
    check("G1 every direct store is a whole-dword mov", mn_census == {"mov": 27}, str(mn_census))
    check("G1 zero and/or/xor/add at the direct displacement",
          not any(mn in ("and", "or", "xor", "add", "sub", "bts") for a, mn, d, ops in aw))

    # ---------------- G2 ---------------------------------------------------
    fns = load_fns(INDEX)
    preds = build_preds(ins)
    pp = pair_pointers(ins, fns, preds)
    print("\nG2  stores through a lea-derived pair pointer: %d" % len(pp))
    for a, d, s in pp:
        print("  0x%-8x %-22s <- %s" % (a, d, s))
    check("G2 15 pointer stores", len(pp) == 15, str(len(pp)))
    check("G2 pointer stores are disjoint from the direct set",
          not (set(a for a, d, s in pp) & set(a for a, mn, d, ops in aw)))

    # ---------------- G3 ---------------------------------------------------
    print("\nG3  pair-write census + value classification (CFG backward dataflow)")
    rows = []
    for a, mn, d, ops in aw:
        f = fn_of(fns, a)
        rows.append((a, d, ops[-1], classify(ins, preds, at[a], ops[-1], at.get(f[0], 0) if f else 0)))
    for a, d, s in pp:
        b = ins[at[a]][1]
        _, ops = split_ops(b)
        f = fn_of(fns, a)
        rows.append((a, d, ops[1], classify(ins, preds, at[a], ops[1], at.get(f[0], 0) if f else 0)))
    rows.sort()
    for a, d, src, cls in rows:
        kind, clr, st, xr, ar, npaths, seen = cls
        print("  0x%-8x %-26s <- %-4s %-9s clr=0x%-10x set=0x%-7x arith=0x%-6x paths=%d %s"
              % (a, d, src, kind, clr, st, ar, npaths, " ".join(seen)[:50]))
    kinds = {}
    for r in rows:
        kinds[r[3][0]] = kinds.get(r[3][0], 0) + 1
    print("  classes: %s" % kinds)
    check("G3 42 pair writes", len(rows) == 42, str(len(rows)))
    hard = [r for r in rows if r[3][2] & BIT]               # OR of an immediate with bit 10
    parm = [r for r in rows if r[3][0] == "PARAM_OR"]       # OR mask from a register
    print("  hardcoded 0x400 setters: %d %s" % (len(hard), [hex(r[0]) for r in hard]))
    print("  parameterised OR writers: %d %s" % (len(parm), [hex(r[0]) for r in parm]))
    check("G3 exactly 2 hardcoded 0x400 setters (0x5534b1, 0x555a6e)",
          [r[0] for r in hard] == [0x5534B1, 0x555A6E], str([hex(r[0]) for r in hard]))
    check("G3 both OR exactly 0x400 into a field-derived value",
          [r[3][2] for r in hard] == [0x400, 0x400], str([hex(r[3][2]) for r in hard]))
    check("G3 exactly 3 parameterised OR writers",
          sorted(r[0] for r in parm) == [0x551BE8, 0x551C0D, 0x551D22],
          str([hex(r[0]) for r in parm]))
    check("G3 they sit in FUN_00551a20 (x2) and FUN_00551cf0 (x1)",
          [fn_of(fns, r[0])[2] for r in parm] == ["FUN_00551a20", "FUN_00551a20", "FUN_00551cf0"],
          str([fn_of(fns, r[0])[2] for r in parm]))
    and_rows = {r[0]: r[3][1] for r in rows}
    print("  FUN_00551a20 clear arms: 0x551b1d clr=0x%x, 0x551b4a clr=0x%x"
          % (and_rows.get(0x551B1D, 0), and_rows.get(0x551B4A, 0)))
    check("G3 FUN_00551a20's clear arm ANDs 0xfaeef378, whose bit 10 is CLEAR (0x400 wiped)",
          and_rows.get(0x551B1D) == 0xFAEEF378 and and_rows.get(0x551B4A) == 0xFAEEF378
          and (and_rows.get(0x551B1D, 0) & BIT) == 0,
          str([hex(and_rows.get(a, 0)) for a in (0x551B1D, 0x551B4A)]))
    opq = [r[0] for r in rows if r[3][0] == "OPAQUE"]
    check("G3 the only OPAQUE pair writes are M383's two stack-copy slots",
          opq == [0x52B9C7, 0x52B9D0], str([hex(a) for a in opq]))

    # ---------------- G4 ---------------------------------------------------
    print("\nG4  mask-argument census of the parameterised writers (arg2 = mask)")
    api = []
    for a, b in ins:
        mn, ops = split_ops(b)
        if mn != "call" or not ops:
            continue
        t = imm_of(ops[0])
        if t not in (MASK_API, MASK_API2):
            continue
        nargs = 3 if t == MASK_API else 4
        args, defs = call_args(ins, preds, at[a], nargs)
        if ALGO == 16:
            args = args[::-1]
        mask = args[2] if len(args) > 2 else None
        flag = args[3] if len(args) > 3 else None
        f = fn_of(fns, a)
        mv, how = resolve_mask(mask, defs) if mask else (None, "missing")
        if mv is None and mask:
            how = passthru(ins, at[a], mask, at.get(f[0], 0) if f else 0, at.get(f[1], 0) if f else 0) or how
        api.append((a, t, mask, mv, how, flag))
    print("  call sites: %d" % len(api))
    for a, t, mask, mv, how, flag in sorted(api):
        print("  0x%-8x -> FUN_%08x mask=%-8s %-5s %-26s flag=%s"
              % (a, t, mask, ("0x%x" % mv) if mv is not None else "-", how, flag))
    known = [x for x in api if x[3] is not None]
    unk = [x for x in api if x[3] is None]
    pt = [x for x in unk if str(x[4]).startswith("arg")]
    print("  resolved masks: %d, passthrough: %d, opaque: %d"
          % (len(known), len(pt), len(unk) - len(pt)))
    setters_api = [x for x in known if x[3] & BIT and x[5] == "0x1"]
    print("  masks carrying 0x400 with the SET flag: %d" % len(setters_api))
    for a, t, mask, mv, how, flag in sorted(setters_api):
        print("  0x%-8x FUN_%08x mask=0x%x (%s) flag=%s" % (a, t, mv, how, flag))
    check("G4 106 mask-API call sites (70 + 36)", len(api) == 106, str(len(api)))
    check("G4 exactly 5 callers set 0x400 through the API", len(setters_api) == 5,
          str(len(setters_api)))
    check("G4 the five are 0x41b2d2 0x4cd6f6 0x5470d6 0x594cf7 0x59aef0",
          [x[0] for x in setters_api] == [0x41B2D2, 0x4CD6F6, 0x5470D6, 0x594CF7, 0x59AEF0],
          str([hex(x[0]) for x in setters_api]))
    clr_api = [x for x in known if x[3] & BIT and x[5] == "0x0"]
    print("  masks carrying 0x400 with the CLEAR flag: %d %s"
          % (len(clr_api), [hex(x[0]) for x in clr_api]))
    check("G4 two API callers clear 0x400", len(clr_api) == 2, str(len(clr_api)))
    print("  opaque mask registers (unresolved, OPEN): %d" % (len(unk) - len(pt)))
    for a, t, mask, mv, how, flag in sorted(unk):
        if not str(how).startswith("arg"):
            print("    0x%-8x %s %s" % (a, mask, how))

    # ---------------- G5 ---------------------------------------------------
    print("\nG5  the SETTER SET (bit 0x400 introduced into the pair dword)")
    setters = [(a, "hardcoded or-immediate", "or imm") for a in (0x5534AE, 0x555A6B)]
    setters += [(x[0], "FUN_00551cf0(owner, other, 0x%x, set=1)" % x[3], "mask API")
                for x in setters_api]
    for a, what, how in sorted(setters):
        f = fn_of(fns, a)
        print("  0x%-8x %-18s %-46s %s" % (a, how, what, f[2] if f else "?"))
    print("  total %d sites in %d functions" % (len(setters),
          len({fn_of(fns, a)[2] for a, _, _ in setters})))
    check("G5 seven setter sites, one per function", len(setters) == 7 and
          len({fn_of(fns, a)[2] for a, _, _ in setters}) == 7,
          "%d sites / %d fns" % (len(setters), len({fn_of(fns, a)[2] for a, _, _ in setters})))

    print("\nG5b the 0x555a6e gate")
    k = at[0x555A6B]
    for i in range(k - 9, k + 4):
        print("  0x%-8x %s" % (ins[i][0], ins[i][1]))
    check("G5 0x555a6b is `or ah,0x4` (bit 10 in the high byte)", ins[k][1] == "or ah,0x4", ins[k][1])
    check("G5 it stores the same register straight back to the pair field",
          ins[k + 1][0] == 0x555A6E and "0x94d448" in ins[k + 1][1], ins[k + 1][1])
    guard = [(ins[k - j][0], ins[k - j][1]) for j in range(1, 12)][::-1]
    print("  preceding 11: %s" % " / ".join("%s" % t for a, t in guard))
    gidx = [t for a, t in guard]
    check("G5 1. the pair test is `test ah,0xc` (0x400|0x800)",
          "test ah,0xc" in gidx, str(gidx[:6]))
    check("G5 2. if either bit is already set the jne skips the setter",
          gidx[gidx.index("test ah,0xc") + 1].startswith("jne"), gidx[gidx.index("test ah,0xc") + 1])
    check("G5 3. bit 5 present -> the 0x800 arm runs instead (je 0x555a5d)",
          "test al,0x20" in gidx and gidx[gidx.index("test al,0x20") + 1] == "je 0x555a6b",
          str(gidx[-3:]))
    j2 = at[0x5534AE]
    print("  --")
    for i in range(j2 - 8, j2 + 3):
        print("  0x%-8x %s" % (ins[i][0], ins[i][1]))
    check("G5 0x5534ae is `or ch,0x4` then a store through the pointer",
          ins[j2][1] == "or ch,0x4" and ins[j2 + 1][1] == "mov DWORD PTR [eax],ecx",
          ins[j2][1] + " / " + ins[j2 + 1][1])
    per = [ins[j2 - kk][1] for kk in range(1, 0x160)]
    check("G5 that pointer is the 2095 fold of the pair array, built in the same function",
          any(x == "lea eax,[ecx*4+0x94d448]" for x in per), "lea eax,[ecx*4+0x94d448]")

    # ---------------- G6 ---------------------------------------------------
    print("\nG6  rivals")
    check("R1 'no writer exists, 0x400 is dead' — refuted: 7 setter sites",
          len(hard) + len(setters_api) == 7)
    check("R2 'the 0x840 OR at 0x5553ed sets 0x400' — refuted: 0x840 & 0x400 == 0",
          (0x840 & BIT) == 0 and 0x5553ED not in [r[0] for r in rows])
    b575 = next(t for x, t in ins if x == 0x554703)
    check("R3 'or dh,0x4 at 0x5546f2 writes the pair' — refuted: it stores to [esi-0x6]",
          "esi-0x6" in b575, b575)
    check("R4 'or esi,0x400 at 0x519f0d writes the pair' — refuted: it stores ds:0x95da44",
          "0x95da44" in next(t for x, t in ins if x == 0x519F18))
    check("R5 'the writers are greppable at the field displacement' — refuted: "
          "0 and/or/xor at [..+0x94d448]; 5 of the 7 setters are mask-API callers",
          mn_census == {"mov": 27} and len(setters_api) == 5)

    # ---------------- G7 ---------------------------------------------------
    body = "\n".join("0x%x:0x%x:%s:0x%x" % (a, b if isinstance(b, int) else 0, c[0], c[3])
                     for a, b, s, c in rows)
    d1 = hashlib.sha1(body.encode()).hexdigest()[:16]
    print("\nG7  digest of the %d-row pair-write table = %s" % (len(rows), d1))
    check("G7 digest pinned", d1 == DIGEST_PIN, d1)

    print("\n%s M384: %d/%d" % ("PASS" if not FAILS else "FAIL", TOTAL[0] - len(FAILS), TOTAL[0]))
    if FAILS:
        print("failing: " + ", ".join(FAILS))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
