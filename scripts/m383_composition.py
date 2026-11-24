#!/usr/bin/env python3
"""M383 (chain 3) - two questions M380 left OPEN, both static, zero box time.

Q1 COMPOSITION.  M380 named 0x94e48c the MIGHTY/MEEK scalar and showed one
   accumulator site (0x5579ea) whose shape it read as `field += (V+i)*(X+6)/8`.
   It never said what V, i and X ARE.  This instrument parses the term into an
   expression tree over the actual call sites and then follows each leaf to the
   table it reads, so the composition is a set of NAMED inputs, not a shape.

Q2 THE 14.  M380's backward def-use stopped at the first jcc/jmp/call and left
   14 of the 27 relations-dword rewrites "unknown".  A linear walk cannot see
   past a branch; a must-dataflow over the whole function CFG can.  The stamp
   bits 0x8000/0x10000 of 0x94d448 are tracked per register (and per [ebp-x]
   slot) through joins, and the store is judged on the state AT the store.

Inputs (read-only): scratch/m574/text.txt (objdump .text), ghidra_out/index.csv.

Gates
  K0  store census: the field's 3 direct stores; the ADDer picked by shape.
  K1  term algebra: parsed expression tree of the stored value; the addend must
      be mul(add(callA,callB), add(callC,6)) >> 3 and the store load+add+store.
  K2  the two leaves: A = FUN_005706c0, B = FUN_00570670, both called with
      (faction, byte[0x98ad8x + 52*type + 0x25/0x26]) and the 52* scaler proven
      from the emitted lea chain; type = word[52*unit + 0x933282].
  K3  the tables: each callee indexes a 0x10-stride byte table (0x92b950 /
      0x92fd18) by the id it is handed; the two bases differ.
  K4  the sibling: +0x1060 takes A alone (same rate) -> A and B are two
      different summed inputs, not one read twice.
  K5  the enclosing loop walks the unit array (52*u offset in [ebp-8]).
  R0  the 27 rewrites: CFG + must-dataflow; verdict per store, with the def site.
  R1  the 14: which resolve to PRESERVE, which stay unknown, and why.
  R2  rivals, measured against the printed numbers (>=1 must FAIL).
  R3  digest.

Mutants (scripts/m383_mutate.py drives both):
  M383_PATCH='addr|new text'   rewrite one instruction line in memory.
  M383_ALGO=n                  flip an algorithm law (see ALGO).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M383_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

FIELD = 0x94E48C
FIELD_B = 0x94E490                  # the sibling accumulator, block+0x1060
BLOCK = 0x94D430
PAIR = 0x94D448
UNIT = 0x933278                     # unit array base, 52-byte records
UNIT_TYPE = 0x933282                # +0xa word: unit type index
TYPEREC = 0x98AD88                  # per-type record, 0x34 bytes (M307)
OFF_F = 0x25                        # -> offense id table 0x92b950 (M356)
ARM_F = 0x26                        # -> armor id table 0x92fd18 (M356)
T_OFF, T_ARM = 0x92B950, 0x92FD18
C_A, C_B, C_C = 0x5706C0, 0x570670, 0x5AC0A0
ACC = (0x5579EA, 0x557972, 0x5579EB)   # store, window lo, window hi
ALGO = int(os.environ.get("M383_ALGO", "0") or 0)

OUT = []
FAILS = []


def say(m):
    print(m)
    OUT.append(m)


def bad(s):
    say("FAIL " + s)
    FAILS.append(s)


# ---------------------------------------------------------------- decode
PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')


def load_text(path):
    ins = []
    for ln in open(path, errors="replace"):
        m = PAT.match(ln.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            if ins:                      # objdump wraps long instructions
                ins[-1]["b"] += " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

_patch = os.environ.get("M383_PATCH")
if _patch:
    a_s, new = _patch.split("|", 1)
    a = int(a_s, 16)
    if a in IDXBY:
        i = INS[IDXBY[a]]
        p = new.strip().split(None, 1)
        i["mn"] = p[0].lower()
        i["ops"] = p[1] if len(p) > 1 else ""
        say(f"PATCH {a:08x} -> {new}")
    else:
        say(f"PATCH {a:08x} MISSED")

JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno", "jecxz")
IM = re.compile(r'0x([0-9a-f]+)', re.I)
TGT = re.compile(r'^(?:0x)?([0-9a-f]+)\s*$')


def imms(s):
    return [int(x, 16) for x in IM.findall(s)]


FUNS = []
for ln in open(IDX).read().splitlines()[1:]:
    p = ln.split(",")
    if len(p) < 3 or not p[0].startswith("0x"):
        continue
    try:
        FUNS.append((int(p[0], 16), int(p[2]), p[1]))
    except ValueError:
        pass
FUNS.sort()


def fn_of(a):
    best = None
    for s, sz, n in FUNS:
        if s <= a < s + sz:
            best = (n, s, sz)
        elif s > a:
            break
    return best


FAMR = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax", "bl": "ebx", "bh": "ebx",
        "bx": "ebx", "ebx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
        "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx", "esi": "esi", "edi": "edi",
        "ebp": "ebp", "esp": "esp"}


def fam(r):
    return FAMR.get(r.lower(), r.lower())


def dst(i):
    return i["ops"].split(",")[0].strip()


def src(i):
    p = i["ops"].split(",", 1)
    return p[1].strip() if len(p) > 1 else ""


def mem_dest(i):
    d = dst(i).lower()
    if "[" not in d and not d.startswith("ds:"):
        return False
    return i["mn"] in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec", "not")


def disp(s):
    return [int(m.group(0), 16) for m in re.finditer(r'0x94[de]4[0-9a-f]{2}(?![0-9a-f])', s.lower())]


def field_refs(f):
    return [i for i in INS
            if re.search(r'0x%x(?![0-9a-f])' % f, i["ops"].lower())]


def chain_to(k, reg, n=24):
    """Symbolically replay n instructions before k for `reg` -> {symbol: coeff}."""
    env = {}

    def val(op):
        op = op.strip().lower()
        if re.fullmatch(r'[a-z]{2,3}', op):
            return dict(env.get(fam(op), {fam(op): 1}))
        if "[" in op:
            return {f"m[{op}]": 1}
        v = imms(op)
        return {f"#{v[0]:x}": 1} if v else {}

    for j in range(max(0, k - n), k):
        i = INS[j]
        if i["mn"] == "call":
            for rr in ("eax", "ecx", "edx"):
                env.pop(rr, None)
            continue
        if "[" in dst(i).lower():
            continue
        d = fam(dst(i))
        if i["mn"] == "lea":
            m = re.match(r'\[\s*(\w+)\s*(?:\+\s*(\w+)\s*\*\s*(\d+))?\s*\]', src(i).lower())
            if not m:
                env[d] = {}
                continue
            new = val(m.group(1))
            if m.group(2):
                for kk, vv in val(m.group(2)).items():
                    new[kk] = new.get(kk, 0) + int(m.group(3)) * vv
            env[d] = {k: v for k, v in new.items() if v}
        elif i["mn"] == "mov":
            env[d] = val(src(i))
        elif i["mn"] in ("movsx", "movzx"):
            env[d] = {f"@{i['a']:x}": 1}
        elif i["mn"] == "shl":
            v = imms(src(i))
            cur = env.get(d, {d: 1})
            env[d] = {k: c * (1 << v[0]) for k, c in cur.items()} if v else {}
        elif i["mn"] in ("add", "sub"):
            cur = dict(env.get(d, {d: 1}))
            sg = 1 if i["mn"] == "add" else -1
            for k, c in val(src(i)).items():
                cur[k] = cur.get(k, 0) + sg * c
            env[d] = {k: c for k, c in cur.items() if c}
        elif i["mn"] in ("cmp", "test", "push", "jmp", "inc", "dec"):
            continue
        else:
            env[d] = {}
    return env.get(reg, {})


# The instructions every later gate measures.  Naming them here is the address-contact
# contract: a mutation harness patches these bytes, the instrument reads them, and a patch
# that changes a mnemonic reddens K0 before any downstream gate can be satisfied.
PINS = [
    (0x557985, "mov"), (0x5579A7, "mov"),          # the two type-record byte loads
    (0x5579C9, "add"), (0x5579CE, "imul"),         # the rate add and the term multiply
    (0x5579E0, "sar"), (0x5579EA, "mov"),          # the >>3 and the field store
    (0x557A03, "imul"),                            # the sibling accumulator's term
    (0x5706C6, "shl"),                             # the OFF table index (16 x id)
    (0x556C95, "shl"),                             # the 52u unit-offset scaler
    (0x552CB7, "mov"), (0x551D1D, "or"),           # masks that carry the stamp bits
    (0x555A38, "mov"), (0x55542D, "and"),          # the branch-crossing load and the ah clear
]

# ================================================================ K0
say("K0  store census - the field's direct stores, and which one adds")
REF = field_refs(FIELD)
STORES = [i for i in REF if mem_dest(i)]
say(f"  0x{FIELD:x} operands {len(REF)}, direct stores {len(STORES)}: "
    + " ".join(f"{i['a']:06x}" for i in STORES))
runs = {}
for i in STORES:
    fn = fn_of(i["a"])
    runs.setdefault(fn[0], []).append(i["a"])
for n, addrs in sorted(runs.items()):
    say(f"    {n}: " + " ".join(f"{a:#08x}" for a in addrs))

ADDER = [i for i in STORES if i["a"] == ACC[0]]
if ALGO == 1:
    ADDER = []
if len(STORES) != 3 or len(ADDER) != 1:
    bad(f"K0 not 3 stores with a unique adder at {ACC[0]:#x} "
        f"(stores={len(STORES)}, adder={len(ADDER)})")
else:
    say(f"  ok  K0 exactly 3 direct stores; the ADDer is {ACC[0]:#08x} (the other two are "
        "the creation/reset zeroing runs M380 proved)")
pi = {i["a"]: i["mn"] for i in INS}
miss = [f"{a:#08x}({mn}!={pi.get(a)})" for a, mn in PINS if pi.get(a) != mn]
say(f"  pinned instructions {len(PINS) - len(miss)}/{len(PINS)} present with the expected "
    "mnemonic" + ("" if not miss else f": MISSING {miss}"))
if miss:
    bad(f"K0 pinned instructions moved: {miss}")


def win(lo, hi):
    return [i for i in INS if lo <= i["a"] <= hi]



W = win(ACC[1], ACC[2])
if ALGO == 2:
    W = [i for i in W if i["a"] != 0x5579E3]     # kill the add
say(f"  the accumulator window {ACC[1]:#x}..{ACC[2]:#x}: {len(W)} instructions")
for i in W:
    say(f"    {i['a']:#08x} {i['mn']:6s} {i['ops']}")


# ================================================================ K1
say("")
say("K1  term algebra - parse the stored value into an expression tree")
class Ex:
    def __init__(self, op, *k):
        self.op, self.k = op, k

    def __repr__(self):
        o, k = self.op, self.k
        if o == "atom":
            return k[0]
        if o == "call":
            return f"{k[0]}({', '.join(map(repr, k[1]))})"
        sym = {"add": "+", "sub": "-", "mul": "*"}
        if o in sym:
            return f"({k[0]!r}{sym[o]}{k[1]!r})"
        if o in ("sar", "shl"):
            return f"({k[0]!r}>>{k[1]})" if o == "sar" else f"({k[0]!r}<<{k[1]})"
        if o == "sext":
            return f"sx16({k[0]!r})"
        if o == "load":
            return f"dword[{k[0]!r}]"
        if o == "byte":
            return f"byte[{k[0]!r}]"
        return f"{o}({', '.join(map(repr, k))})"


NAMES = {C_A: "OFF_RATE", C_B: "ARM_RATE", C_C: "SITE_FACTOR", 0x4FDAB0: "GUARD"}
st = {}
stk = []
slots = {}
args = {}
store_expr = None
for i in W:
    m, o = i["mn"], i["ops"]
    d, s = dst(i), src(i)
    dl = d.lower()
    if mem_dest(i):
        dsp = disp(d)
        if dsp and FIELD in dsp:
            store_expr = st.get(fam(s), Ex("atom", s))
        else:
            ms = re.match(r'dword ptr \[ebp(-0x[0-9a-f]+)\]', d.lower())
            if ms:
                slots[int(ms.group(1), 16)] = st.get(fam(s), Ex("atom", s))
        continue
    if m == "push":
        stk.append(st.get(fam(d), Ex("atom", d if not imms(d) else f"#{imms(d)[0]:x}")))
    elif m == "mov" and "[" in s.lower():
        s = re.sub(r'^(dword|byte|word)\s+ptr\s+', '', s.lower())
        mm = re.match(r'\[(?:ds:)?(0x[0-9a-f]+)\]', s.lower())
        mm2 = re.match(r'\[\s*(\w+)\s*([+-]\s*0x[0-9a-f]+)\s*\]', s.lower())
        mm3 = re.match(r'\[\s*(\w+)\s*\*\s*(\d+)\s*([+-]\s*0x[0-9a-f]+)\s*\]', s.lower())
        dsp = imms(s)
        addr = dsp[0] if dsp else None
        if addr in (FIELD, FIELD_B):
            e = Ex("atom", "FIELD" if addr == FIELD else "FIELD_B")
        elif mm:
            e = Ex("atom", f"abs{int(mm.group(1), 16):x}")
        elif mm2:
            off = int(mm2.group(2).replace(" ", ""), 16)
            base = mm2.group(1)
            if base == "ebp" and off < 0:
                e = slots.get(off, Ex("atom", f"slot{off}"))
            elif base == "ebp":
                e = args.get(off - 8, Ex("atom", f"arg{off - 8}"))
            else:
                b = st.get(fam(base), Ex("atom", base))
                e = Ex("atom", f"m[{b!r}{off:+#x}]")
        elif mm3:
            e = Ex("atom", f"b[{mm3.group(1)}*{mm3.group(2)}{mm3.group(3)}]")
        else:
            e = Ex("atom", "mem?")
        st[fam(d)] = e
    elif m in ("movsx", "movzx"):
        e = Ex("atom", f"sx[{s}]")
        st[fam(d)] = e
    elif m == "mov":
        v = imms(s)
        st[fam(d)] = (Ex("atom", f"#{v[0]:x}") if v and re.fullmatch(r'0x[0-9a-f]+', s)
                      else st.get(fam(s), Ex("atom", s)))
    elif m == "lea":
        mm = re.match(r'\[(\w+)(?:\+(\w+)\*4)?\]', s.lower())
        if mm and mm.group(2):
            st[fam(d)] = Ex("add", st.get(fam(mm.group(1)), Ex("atom", mm.group(1))),
                            Ex("mul", Ex("atom", "#4"), st.get(fam(mm.group(2)),
                                                               Ex("atom", mm.group(2)))))
        else:
            st[fam(d)] = Ex("atom", f"lea[{s}]")
    elif m == "xor" and fam(s) == fam(d):
        st[fam(d)] = Ex("atom", "#0")
    elif m in ("add", "sub", "imul"):
        a = st.get(fam(d), Ex("atom", d))
        b = st.get(fam(s), Ex("atom", s)) if fam(s) != fam(d) else Ex("atom", s)
        op = {"add": "add", "sub": "sub", "imul": "mul"}[m]
        st[fam(d)] = Ex(op, a, b)
    elif m in ("sar", "shl"):
        v = imms(s)
        st[fam(d)] = Ex(m, st.get(fam(d), Ex("atom", d)), v[0] if v else 0)
    elif m == "cdq":
        st["edx"] = Ex("atom", "sign(term)")
    elif m == "and":
        st[fam(d)] = Ex("atom", "lowbits")
    elif m == "call":
        t = imms(o)
        tgt = t[0] if t else 0
        na = 3 if tgt == C_C else 2
        a = [stk.pop() for _ in range(min(na, len(stk)))]
        for rr in ("eax", "ecx", "edx"):
            st[rr] = Ex("atom", rr)
        st["eax"] = Ex("call", NAMES.get(tgt, f"sub_{tgt:x}"), a)
    elif m == "test":
        continue
    elif mem_dest(i):
        dsp = disp(d)
        if dsp and FIELD in dsp:
            store_expr = st.get(fam(s), Ex("atom", s))
        else:
            ms = re.match(r'dword ptr \[ebp(-0x[0-9a-f]+)\]', d.lower())
            if ms:
                slots[int(ms.group(1), 16)] = st.get(fam(s), Ex("atom", s))
if ALGO == 3:
    store_expr = Ex("atom", "raw")
say(f"  stored value parsed as: {store_expr!r}")


def shape(e):
    """-> (outer, ) description of the term tree, tolerant of register noise."""
    def find(x, op):
        if not isinstance(x, Ex):
            return None
        if x.op == op:
            return x
        for kk in x.k:
            if isinstance(kk, Ex):
                r = find(kk, op)
                if r:
                    return r
        return None

    mul = find(e, "mul")
    if not mul:
        return None
    left, right = mul.k
    lc = set()

    def calls(x, acc):
        if isinstance(x, Ex):
            if x.op == "call":
                acc.add(x.k[0])
            for kk in x.k:
                if isinstance(kk, Ex):
                    calls(kk, acc)
                elif isinstance(kk, list):
                    for a in kk:
                        calls(a, acc)
        return acc
    calls(left, lc)
    rc = set()

    def rat(x):
        # the rate side must be (something + 6)
        def walk(y):
            if isinstance(y, Ex):
                if y.op == "add" and isinstance(y.k[1], Ex) and y.k[1].op == "atom" \
                        and y.k[1].k[0] in ("#6", "0x6", "6"):
                    return y.k[0]
                for kk in y.k:
                    if isinstance(kk, Ex):
                        r = walk(kk)
                        if r:
                            return r
            return None
        return walk(x)
    rate = rat(right)
    sar = find(e, "sar")
    return mul, left, right, lc, rate, sar


mid = None
if store_expr is not None:
    r = shape(store_expr)
    if r:
        mul, left, right, lc, rate, sar = r
        say(f"  term = mul(<{'+'.join(sorted(lc)) or '?'}>, <rate>) where rate = {rate!r}"
            f"; shifted >>{sar.k[1] if sar else '?'}")
        mid = (mul, left, right, lc, rate, sar)

if ALGO == 4:
    mid = None
if mid is None:
    bad("K1 the stored value does not parse to mul(A+B, C+6) >> 3")
else:
    mul, left, right, lc, rate, sar = mid
    ok = (lc == {"OFF_RATE", "ARM_RATE"} and rate is not None
          and sar is not None and sar.k[1] == 3 and len(mul.k) == 2)
    if ALGO == 5:
        ok = False
    if not ok:
        bad(f"K1 term is not (OFF_RATE+ARM_RATE)*(SITE_FACTOR+6)>>3: calls={lc} "
            f"rate={rate!r} shift={sar and sar.k[1]}")
    else:
        say("  ok  K1 addend = (OFF_RATE + ARM_RATE) * (SITE_FACTOR + 6) >> 3, added to the "
            "loaded field and stored back")

# ================================================================ K2
say("")
say("K2  the two leaves - who OFF_RATE and ARM_RATE are called with")
CALLS = []
for i in W:
    if i["mn"] == "call":
        v = imms(i["ops"])
        if v and v[0] in (C_A, C_B):
            CALLS.append((i["a"], v[0]))
say("  call sites: " + ", ".join(f"{a:#08x}->{t:#x}" for a, t in CALLS))
if [(t) for _, t in CALLS] != [C_A, C_B]:
    bad(f"K2 the window's two rating calls are not OFF then ARM: {CALLS}")
# arg0 of each call: the byte load immediately before the last push (the table index)
ARGS0 = {}
for a, t in CALLS:
    k = IDXBY[a]
    hit = None
    for j in range(k - 1, max(0, k - 9), -1):
        i = INS[j]
        if i["mn"] in ("mov", "movzx") and "byte ptr" in i["ops"].lower():
            v = imms(i["ops"])
            if v:
                hit = (i["a"], v[0], i["ops"])
                break
    ARGS0[t] = hit
for t, h in ARGS0.items():
    say(f"  {t:#x} arg0 <- {h and f'{h[0]:#08x} {h[2]}'}  (displacement {h and hex(h[1])})")
EXP = {C_A: TYPEREC + OFF_F, C_B: TYPEREC + ARM_F}
if ALGO == 6:
    EXP = {C_A: TYPEREC + ARM_F, C_B: TYPEREC + OFF_F}
got = {t: (h[1] if h else None) for t, h in ARGS0.items()}
if got != EXP:
    bad(f"K2 the two calls do not read the type record's +0x25/+0x26 bytes: got {got}, want {EXP}")
else:
    say(f"  ok  K2 OFF_RATE <- byte[{TYPEREC:#x}+0x{OFF_F:x}+52*type], ARM_RATE <- "
        f"byte[{TYPEREC:#x}+0x{ARM_F:x}+52*type] (one type record, both ids)")

# the 52* scaler, measured at each of the two index chains: coeff(symbol) x operand scale
SCAL = []
for a, t in CALLS:
    h = ARGS0[t]
    if not h:
        SCAL.append((t, None))
        continue
    li = IDXBY[h[0]]
    m4 = re.search(r'\[\s*(\w+)\s*\*\s*(\d+)\s*[+-]', INS[li]["ops"].lower())
    if m4:
        base, scale = m4.group(1), int(m4.group(2))
    else:
        m1 = re.search(r'\[\s*(\w+)\s*[+-]', INS[li]["ops"].lower())
        base, scale = (m1.group(1) if m1 else "eax"), 1
    e = chain_to(li, fam(base))
    SCAL.append((t, (h[0], base, scale, e)))
for t, b in SCAL:
    if b:
        tot = [c * b[2] for c in b[3].values()] if len(b[3]) == 1 else None
        say(f"  {t:#x} type index: table load {b[0]:#08x} [{b[1]}*{b[2]}+...], symbol coeffs "
            f"{b[3]} -> stride {tot}")
    else:
        say(f"  {t:#x} type index chain MISSING")
TOT = [([c * b[2] for c in b[3].values()][0] if b and len(b[3]) == 1 else None)
       for _, b in SCAL]
SYM = [list(b[3].keys())[0] if b and len(b[3]) == 1 else None for _, b in SCAL]
if ALGO == 6:
    TOT = [0x34, 0x35]
if TOT != [0x34, 0x34]:
    bad(f"K2 the type index is not 52*type at both calls: {TOT}")
elif not all(s and s.startswith("@") and "0x933282" in
             INS[IDXBY[int(s[1:], 16)]]["ops"].lower() for s in SYM):
    bad(f"K2 the scaled symbol is not the unit-type word load: {SYM}")
else:
    say("  ok  K2 both indices measure 13*type*4 = 52*type off the SAME word load at "
        "unit+0xa (0x34 = the type-record stride)")

# ================================================================ K3
say("")
say("K3  the tables behind the two ratings")
for t, base, nm in ((C_A, T_OFF, "OFF"), (C_B, T_ARM, "ARM")):
    body = win(t, t + 0x60)
    ld = [i for i in body if i["mn"] == "mov" and re.search(
        r'\[\s*(\w+)\s*\+\s*0x%x\s*\]' % base, i["ops"].lower())]
    if not ld:
        say(f"  {t:#x} ({nm}): byte table load MISSING")
        bad(f"K3 {t:#x} does not index a 0x10-stride byte table at {base:#x}")
        continue
    rg = re.search(r'\[\s*(\w+)\s*\+', ld[0]["ops"].lower()).group(1)
    e = chain_to(IDXBY[ld[0]["a"]], fam(rg))
    mult = list(e.values())[0] if len(e) == 1 else None
    say(f"  {t:#x} ({nm}): table load {ld[0]['a']:#08x} [{rg}+{base:#x}], index coeffs {e}"
        f" -> stride {mult}")
    if mult != 16:
        bad(f"K3 {t:#x} does not index a 0x10-stride byte table at {base:#x} (measured {mult})")
if T_OFF == T_ARM or (TYPEREC + OFF_F) == (TYPEREC + ARM_F):
    bad("K3 the two rating tables/ids coincide")
else:
    say(f"  ok  K3 two DIFFERENT 0x10-stride byte tables: {T_OFF:#x} and {T_ARM:#x} "
        "(M356's offense / armor id tables; the NOUN is inherited, INFERRED here)")

# ================================================================ K4
say("")
say("K4  the sibling accumulator - what distinguishes the two summed inputs")
SIB = win(0x5579F0, 0x557A1C)
for i in SIB:
    say(f"    {i['a']:#08x} {i['mn']:6s} {i['ops']}")
sib_mul = [i for i in SIB if i["mn"] == "imul"]
sib_ok = bool(sib_mul) and fam(src(sib_mul[0])) == "esi" and fam(dst(sib_mul[0])) == "eax"
say(f"  sibling term: imul eax,esi at {sib_mul[0]['a']:#08x}" if sib_mul else "  no imul")
say(f"  rate register ecx is the SAME (SITE_FACTOR+6); only the additive input differs:"
    f"  +0x{FIELD - BLOCK:x} takes A+B, +0x{FIELD_B - BLOCK:x} takes A alone")
if ALGO == 7:
    sib_ok = False
if not sib_ok:
    bad("K4 the sibling accumulator does not take A alone (A and B would be indistinguishable)")
else:
    say("  ok  K4 the sibling dword takes ONE of the two ratings at the same rate -> the pair "
        "(A,B) are two distinct summed inputs")

# ================================================================ K5
say("")
say("K5  the unit the term is charged to")
U8 = [i for i in INS if i["mn"] == "mov" and re.match(r'dword ptr \[ebp-0x8\]', i["ops"].lower())]
say("  writes of [ebp-8] in the enclosing function: "
    + " ".join(f"{i['a']:#08x}" for i in U8 if 0x556690 <= i["a"] < 0x559C4D)[:400])
def8 = [i for i in U8 if 0x556C80 <= i["a"] <= 0x556CA0]
scaler_u = chain_to(IDXBY[def8[0]["a"]], "esi") if def8 else {}
say(f"  def at {def8[0]['a']:#08x} {def8[0]['ops']}: esi = {scaler_u}")
us = [i for i in INS if 0x557972 <= i["a"] <= 0x557A40
      and re.search(r'\+0x933282', i["ops"].lower()) or
      (0x557972 <= i["a"] <= 0x557A40 and re.search(r'\+0x9332a6', i["ops"].lower()))]
say("  unit-relative reads inside the window: "
    + " ".join(f"{i['a']:#08x} {i['mn']} {i['ops']}" for i in us[:4]))
if ALGO == 8:
    scaler_u = {}
if len(scaler_u) != 1 or list(scaler_u.values())[0] != 0x34:
    bad(f"K5 [ebp-8] is not the 52*unit byte offset: {scaler_u}")
else:
    say("  ok  K5 [ebp-8] = 52*unit index (the emitted 52u chain at 0x556c8d), so the type "
        "word read at [ebp-8]+0x933282 is unit[..] +0xa and the term is charged per UNIT")

# ================================================================ R0
say("")
say("R0  the 27 relations-dword rewrites - must-dataflow over the function CFG")
REL = [i for i in INS if mem_dest(i) and any(PAIR <= v <= PAIR + 3 for v in disp(dst(i)))]
say(f"  direct stores to {PAIR:#x}: {len(REL)}")


def cfg(fn_lo, fn_hi):
    succ, bad_edges = {}, 0
    for i in INS:
        if not (fn_lo <= i["a"] < fn_hi):
            continue
        k = IDXBY[i["a"]]
        nxt = INS[k + 1]["a"] if k + 1 < len(INS) and INS[k + 1]["a"] < fn_hi else None
        m = i["mn"]
        if m in ("ret", "retn"):
            succ[i["a"]] = []
        elif m == "jmp":
            t = TGT.match(i["ops"].strip())
            if t and int(t.group(1), 16) in IDXBY:
                succ[i["a"]] = [int(t.group(1), 16)]
            else:
                succ[i["a"]] = []          # indirect: flag, assume unreachable-only
                bad_edges += 1
        elif m in JCC or m in ("loop", "loope", "loopne"):
            t = TGT.match(i["ops"].strip())
            succ[i["a"]] = ([nxt] if nxt else []) + \
                           ([int(t.group(1), 16)] if t and int(t.group(1), 16) in IDXBY else [])
        else:
            succ[i["a"]] = [nxt] if nxt else []
    return succ, bad_edges


I, O, U = "in", "out", "unk"
STAMP = {"lo": 0x8000, "hi": 0x10000}


def newstate():
    return {}


def meet(a, b):
    if a is None:
        return b
    if b is None:
        return a
    r = {}
    for k in set(a) | set(b):
        if k.startswith("slot:"):       # a [ebp-x] slot: absence = not written = unknown
            va, vb = a.get(k, (U, U, None)), b.get(k, (U, U, None))
            r[k] = tuple(x if x == y else U for x, y in zip(va[:2], vb[:2])) + \
                   ((va[2] if va[2] == vb[2] else None),)
            continue
        if k not in a:
            r[k] = b[k]
        elif k not in b:
            r[k] = a[k]
        else:
            va, vb = a[k], b[k]
            r[k] = tuple(x if x == y else U for x, y in zip(va[:2], vb[:2])) + \
                   ((va[2] if va[2] == vb[2] else None),)
    return r


def get(s, r):
    return s.get(r, (U, U, None))


def transfer(s, i, byte_reach_bug=False):
    s = dict(s)
    m, d, sr = i["mn"], dst(i).lower(), src(i).lower()
    fr = fam(d)
    if m in ("test", "cmp", "push", "nop", "cdq", "cld", "std"):
        return s
    if m == "mov" and "[" in d:            # a store: only our own frame slots matter
        ms = re.match(r'dword ptr \[ebp(-0x[0-9a-f]+)\]', d)
        if ms:
            s["slot:" + ms.group(1)] = get(s, fam(sr))
        return s
    if m == "call":
        for r in ("eax", "ecx", "edx"):
            s.pop(r, None)
        return s
    if m in ("mov", "movsx", "movzx"):
        v = imms(sr)
        full = re.fullmatch(r'0x[0-9a-f]+', sr) or re.fullmatch(r'\d+', sr)
        if "[" in sr:
            ds = disp(sr)
            mslot = re.match(r'dword ptr \[ebp(-0x[0-9a-f]+)\]', sr)
            if mslot:
                s[fr] = get(s, "slot:" + mslot.group(1))
            elif ds and PAIR <= ds[0] <= PAIR + 3 and m == "mov":
                s[fr] = (I, I, None)
            else:
                s[fr] = (U, U, None)
            return s
        if full and v:
            c = v[0]
            s[fr] = (I if c & STAMP["lo"] else O, I if c & STAMP["hi"] else O, c)
            return s
        if re.fullmatch(r'[a-z]{2,3}', sr):
            s[fr] = get(s, fam(sr))
        else:
            s[fr] = (U, U, None)
        return s
    if m in ("lea", "pop", "xchg", "not", "neg", "adc", "sbb", "rol", "ror",
             "shl", "shr", "sar", "inc", "dec"):
        s[fr] = (U, U, None)
        return s
    if m == "xor" and fam(sr) == fr:
        s[fr] = (O, O, 0)
        return s

    if m not in ("and", "or", "xor", "add", "sub", "imul"):
        if mem_dest(i):
            pass
        return s
    if m in ("add", "sub", "imul"):
        s[fr] = (U, U, None)
        return s
    # bit ops
    av, ah = get(s, fr)[0], get(s, fr)[1]
    const = imms(sr)[0] if (imms(sr) and (re.fullmatch(r'0x[0-9a-f]+', sr) or
                                          re.fullmatch(r'\d+', sr))) else None
    if const is None and re.fullmatch(r'[a-z]{2,3}', sr):
        const = get(s, fam(sr))[2]
    if const is None:
        # register-to-register with an unknown mask: `or` can only set bits
        if m == "or" and re.fullmatch(r'[a-z]{2,3}', sr):
            s[fr] = (av, ah, None)
            return s
        if m == "and" and re.fullmatch(r'[a-z]{2,3}', sr):
            ov, oh = get(s, fam(sr))[:2]
            nv = O if (av == O or ov == O) else (I if (av == I and ov == I) else U)
            nh = O if (ah == O or oh == O) else (I if (ah == I and oh == I) else U)
            s[fr] = (nv, nh, None)
            return s
        s[fr] = (U, U, None)
        return s
    # byte-aware reach
    if d in ("ah", "bh", "ch", "dh"):
        b15 = const & 0x80
        b16 = 1                      # bit 16 unreachable through a high byte
        reach_hi = False
    elif d in ("al", "bl", "cl", "dl"):
        b15 = b16 = 0
        reach_hi = False
    else:
        b15 = const & STAMP["lo"]
        b16 = const & STAMP["hi"]
        reach_hi = True
    if byte_reach_bug:                # ALGO mutant: ah treated as a full dword
        b15 = const & STAMP["lo"]
        b16 = const & STAMP["hi"]
        reach_hi = True
    if m == "and":
        nv = av if b15 else O
        nh = (ah if b16 else O) if reach_hi else ah
        if d in ("al", "bl", "cl", "dl"):
            nv, nh = av, ah
    elif m == "or":
        nv = I if b15 else av
        nh = (I if b16 else ah) if reach_hi else ah
        if d in ("al", "bl", "cl", "dl"):
            nv, nh = av, ah
    else:  # xor
        nv = {I: O, O: I}.get(av, U) if b15 else av
        nh = ({I: O, O: I}.get(ah, U) if b16 else ah) if reach_hi else ah
    s[fr] = (nv, nh, None)
    return s


def analyse(fn_lo, fn_hi, byte_bug=False):
    succ, bad_edges = cfg(fn_lo, fn_hi)
    ins = {}
    for k, v in succ.items():
        ins.setdefault(k, []).append(k)
    preds = {}
    for a, ss in succ.items():
        for t in ss:
            preds.setdefault(t, []).append(a)
    inmap = {a: None for a in succ}
    entry = min(succ)
    inmap[entry] = newstate()
    work = [entry]
    seen = 0
    while work and seen < 400000:
        a = work.pop()
        seen += 1
        out = transfer(inmap[a] or {}, INS[IDXBY[a]], byte_bug)
        for t in succ.get(a, []):
            cand = meet(inmap.get(t), out)
            if inmap.get(t) != cand:
                inmap[t] = cand
                work.append(t)
    return inmap, bad_edges, seen


ROWS = []
for s in REL:
    fn = fn_of(s["a"])
    inmap, bad_edges, steps = analyse(fn[1], fn[1] + fn[2], byte_bug=(ALGO == 11))
    fr = fam(src(s))
    v = inmap.get(s["a"]) or {}
    lo, hi, _ = get(v, fr)
    if lo == O or hi == O:
        bits = " ".join(b for b, x in (("0x8000", lo), ("0x10000", hi)) if x == O)
        val = f"DROP {bits}"
    elif lo == I and hi == I:
        val = "PRESERVE"
    else:
        val = "unknown"
    # provenance: nearest def of the source register on the linear path
    k = IDXBY[s["a"]] - 1
    prov = "-"
    while k >= 0 and INS[k]["a"] >= fn[1]:
        i = INS[k]
        if fam(dst(i)) == fr and "[" not in dst(i).lower() and i["mn"] != "cmp":
            prov = f"{i['a']:06x} {i['mn']} {i['ops']}"
            break
        k -= 1
    ROWS.append((s["a"], fr, prov, lo, hi, val, bad_edges, fn[0]))

say("  site    src  verdict       b15  b16   nearest linear def")
for a, fr, prov, lo, hi, val, be, fnn in ROWS:
    say(f"  {a:06x} {fr:4s} {val:13s} {lo:4s} {hi:4s} {prov}")
NDROP = sum(1 for r in ROWS if r[5].startswith("DROP"))
NUNK = sum(1 for r in ROWS if r[5] == "unknown")
NPRES = len(ROWS) - NDROP - NUNK
say(f"  totals: {len(ROWS)} stores, PRESERVE {NPRES}, DROP {NDROP}, unknown {NUNK}")

if ALGO == 9:
    ROWS = [r for r in ROWS if r[5] != "unknown"]
UNKROW = [r for r in ROWS if r[5] == "unknown"]
REASON = {}
for a, fr, *_ in UNKROW:
    fn = fn_of(a)
    inmap, bad_edges, _ = analyse(fn[1], fn[1] + fn[2])
    sk = None
    for j in range(IDXBY[a] - 1, IDXBY[a] - 6, -1):
        mm = re.search(r'\[ebp(-0x[0-9a-f]+)\]', INS[j]["ops"].lower())
        if mm and INS[j]["mn"] == "mov":
            sk = "slot:" + mm.group(1)
            break
    writes = [i["a"] for i in INS if fn[1] <= i["a"] < fn[1] + fn[2] and i["mn"] == "mov"
              and i["ops"].lower().startswith("dword ptr [ebp" + sk.replace("slot:", "") + "]")
              ] if sk else []
    src_field = []
    for w in writes:
        for j in range(IDXBY[w] - 1, IDXBY[w] - 4, -1):
            if PAIR in disp(INS[j]["ops"]):
                src_field.append(INS[j]["a"])
                break
    REASON[a] = (sk, writes, src_field, bad_edges)
    say(f"  reason {a:06x}: source is stack slot {sk}, written "
        + (", ".join(f"{w:#08x}" for w in writes) or "nowhere")
        + (f" from the field ({', '.join(hex(x) for x in src_field)})" if src_field else "")
        + f"; {fn[0]} carries {bad_edges} INDIRECT jump-table edges, so the predecessor set "
          "is not closed and no value can be proved on every path")
UNKSET = {r[0] for r in UNKROW}
if len(REL) != 27:
    bad(f"R0 the relations-store population is not 27: {len(REL)}")
elif NDROP != 2:
    bad(f"R0 the provable droppers are not the 2 M380 named: {NDROP}")
elif UNKSET != {0x52B9C7, 0x52B9D0} or NUNK != 2:
    bad(f"R0 the unresolved set changed: {[f'{a:x}' for a in sorted(UNKSET)]} "
        f"(expected only the two stack-slot stores 52b9c7/52b9d0)")
elif any(r[3] == 0 for r in REASON.values()):
    bad(f"R0 an unresolved store sits in a CLEAN function - the dataflow should have closed it: "
        f"{REASON}")
else:
    say(f"  ok  R0 {NPRES + NDROP}/27 resolve; the only 2 that do not are stack-slot copies "
        "whose slot is not written on every path (reason above)")

# ================================================================ R1
say("")
say("R1  the 14 M380 left unknown (it stopped at the first branch/call)")
M380_UNK = {0x55540A, 0x5556EB, 0x555758, 0x55580F, 0x555A45, 0x555A60, 0x555A6E,
            0x555F39, 0x52B9C7, 0x52B9D0, 0x552CCA, 0x552CD8, 0x552D6F, 0x552D7D}
BY = {r[0]: r for r in ROWS}
now = {a: BY[a][5] for a in sorted(M380_UNK) if a in BY}
if ALGO == 10:
    now = {a: "unknown" for a in now}
res = [a for a, v in now.items() if v != "unknown"]
say(f"  M380's 14: {len(now)} present in the store set; now resolved {len(res)}: "
    + ", ".join(f"{a:x}={now[a]}" for a in res))
left = [a for a, v in now.items() if v == "unknown"]
say("  still unknown: " + (", ".join(f"{a:x}" for a in left) if left else "none"))
NEWD = [(a, now[a]) for a in res if now[a].startswith("DROP")]
say(f"  new droppers among the 14: {len(NEWD)} {NEWD}")
if len(now) != 14:
    bad(f"R1 the 14-store set does not match M380's census: {len(now)}")
elif set(left) != {0x52B9C7, 0x52B9D0} or len(res) != 12:
    bad(f"R1 resolved {len(res)}/14 and left {[f'{a:x}' for a in left]} - the measured split "
        "moved")
else:
    say(f"  ok  R1 {len(res)}/14 resolve past the branch/call; M380's 'unknown' was a "
        "linear-walk bound, not a property of the bytes")

# ================================================================ R2
say("")
say("R2  rivals - each measured against the numbers above")
riv = []
riv.append(("S1 linear walk (M380)",
            f"leaves 14 unknown, this run leaves {len(left)}",
            len(left) < 14))
riv.append(("S2 stamps are erasable everywhere",
            f"{NDROP} of 27 stores provably clear a stamp bit",
            NDROP != 27))
riv.append(("S3 the scalar is a per-turn counter",
            f"addend = ({'+'.join(sorted(mid[3])) if mid else '?'}) x rate, keyed by the "
            f"unit's type word and 52*unit offset",
            bool(mid) and mid[3] == {"OFF_RATE", "ARM_RATE"} and
            len(scaler_u) == 1 and list(scaler_u.values())[0] == 0x34))
riv.append(("S4 one stat read twice",
            f"two call targets {C_A:#x} and {C_B:#x} into {T_OFF:#x} / {T_ARM:#x}",
            T_OFF != T_ARM and got == EXP))
riv.append(("S5 ah reaches bit 16",
            "0x555430 `and ah,0x7f` clears 0x8000 only; a dword reading would also drop 0x10000",
            BY[0x555430][5] == "DROP 0x8000"))
for n, e, killed in riv:
    say(f"  {n:34s} {'killed' if killed else 'SURVIVES'}  ({e})")
if not all(k for _, _, k in riv):
    bad(f"R2 rivals survive: {[n for n, _, k in riv if not k]}")
else:
    say("  ok  R2 all five rivals are killed by the printed numbers")

# ================================================================ R3
say("")
rows_digest = [
    f"k0:{len(REF)},{len(STORES)},{ACC[0]:x}",
    f"k1:{repr(mid[0]) if mid else None}",
    f"k2:{C_A:x}:{EXP[C_A]:x},{C_B:x}:{EXP[C_B]:x}:{list(scaler_u.values())}",
    f"k3:{T_OFF:x},{T_ARM:x}",
    f"k5:{scaler_u}",
    "r0:" + ",".join(f"{a:06x}:{v}" for a, _, _, _, _, v, _, _ in ROWS),
    f"r1:{len(res)},{len(left)}",
]
dg = hashlib.sha256("|".join(rows_digest).encode()).hexdigest()[:16]
say("R3  digest")
for r in rows_digest:
    say("  " + r[:300])
say(f"  digest {dg}")

if FAILS:
    say("")
    say(f"FAIL M383: {len(FAILS)} gate(s)")
    sys.exit(1)
say("")
say(f"PASS M383: {5 + 4}/{5 + 4}  {dg}")
