#!/usr/bin/env python3
# M326: block+0x224 - the DEBT SIBLING of ENERGY (M325's carried OPEN).
# ANSWER measured here: the per-faction DEFERRED HURRY-PRODUCTION PAYMENT
# accumulator ("energy debt"): the HURRY dialog FUN_00419c30 adds a cost into
# block+0x224 when phase globals 0x920434/0x91c62c are both non-zero (else it
# pays ENERGY immediately); every reader computes ENERGY(220) - field224 =
# AVAILABLE energy; per-faction upkeep FUN_005208f0 settles ENERGY -= field224,
# field224 := 0, ENERGY floored at 0; RESET FUN_0059ec90 zeroes it. The noun
# HURRY is byte-pinned (HURRY/HURRYOPTIONS/HURRYPAYMENT pushed ONLY inside the
# writer function); no DEBT/ARREAR string exists; LOAN strings belong to OTHER
# functions (the inter-faction loan mechanism writes ENERGY directly, M325).
# STATIC, zero box. Footing: NAMED ## M325 / M324 / M320 / M316.
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers;
# digest hashes the MEASURED detail; declared sets MEASURED not authored.
# Resolver: M325's reviewed resolver PLUS one FIX measured this round:
# partial-register writes (mov al/ax/ah, ...) are OPAQUE definitions of the
# full register (the old walk skipped them and over-proved const-0 through
# `xor eax,eax; mov al,[rec+4]` - both BLKCONST tags of the skeleton run were
# that artifact; ALGO=7 restores the old blindness as a mutant). Other limits
# unchanged (DECLARED): linear backward def-walk <=300 instrs depth<=4, affine
# over opaque runtime leaves, linear stack-slot forwarding (most recent store
# wins; call crossings enumerated; a callee holding a pointer to the slot could
# rewrite it), LIFO-sound pop pairing, forward scan stops at redefinition
# (calls clobber eax/ecx/edx). No CFG dataflow proof: branch paths that
# re-assign a base register are not distinguished (the 419c30 fold also has
# 419de9/419e1f mov esi,[ebx+0x40] paths; the linear model takes 419e5a).
# Mutants: M326_PATCH addr|mn ops, M326_PE_PATCH addr|hex, M326_ALGO 1=prov off
# 2=disp widened 3=seed-scan off 4=shl-blind 6=old-pop-pairing 7=subreg-blind,
# M326_SAVE=<file>, M326_EVIDENCE_ROOT=<dir>.
import bisect, csv, hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
PE = os.path.join(ROOT, "programs/terran.exe")
EV = os.environ.get("M326_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M326_ALGO", "0")
SAVE = os.environ.get("M326_SAVE", os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import decode_save as ds

BLKBASE, STRIDE, NBLK, OFF = 0x94d430, 0x20bc, 8, 0x224
FADDRS = [BLKBASE + OFF + k * STRIDE for k in range(NBLK)]
BLKBASES = [BLKBASE + k * STRIDE for k in range(NBLK)]
BLKEND = BLKBASE + NBLK * STRIDE
TURNFN = 0x51f320
ENERGY_OFF = 0x220
EADDRS = [BLKBASE + ENERGY_OFF + k * STRIDE for k in range(NBLK)]
IMG_BASE = 0x400000

STORE_MN = {"mov", "xchg", "add", "adc", "sub", "sbb", "inc", "dec", "or", "and",
            "xor", "not", "neg", "movnti", "pop", "cmpxchg", "xadd", "bts", "btr", "btc"}
RMW1 = {"inc", "dec", "not", "neg"}
REGW = {"eax": 4, "ebx": 4, "ecx": 4, "edx": 4, "esi": 4, "edi": 4, "ebp": 4, "esp": 4,
        "ax": 2, "bx": 2, "cx": 2, "dx": 2, "si": 2, "di": 2, "bp": 2, "sp": 2,
        "al": 1, "bl": 1, "cl": 1, "dl": 1, "ah": 1, "bh": 1, "ch": 1, "dh": 1}
PARTIALS = {"eax": {"al", "ah", "ax"}, "ebx": {"bl", "bh", "bx"},
            "ecx": {"cl", "ch", "cx"}, "edx": {"dl", "dh", "dx"},
            "esi": {"si"}, "edi": {"di"}, "ebp": {"bp"}, "esp": {"sp"}}
CALLER_SAVED = {"eax", "ecx", "edx"}
STACK_CALL_CROSSINGS = []
CUR_SITE = None

def load_ins():
    ins = {}
    lin = re.compile(r"^\s*([0-9a-f]{6,8}):\s[0-9a-f ]+\t(\w+)\s*(.*)$")
    for ln in open(TEXT):
        m = lin.match(ln)
        if m:
            ins[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())
    p = os.environ.get("M326_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M326_PATCH address not in .text cache: %s" % addr)
            if ins[a] == (mn, ops.strip()):
                raise SystemExit("M326_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M326_PATCH applied to nothing")
    return ins

INS = load_ins()
ADDRS = sorted(INS)
AIDX = {a: i for i, a in enumerate(ADDRS)}
funcs = []
with open(IDX) as f:
    for r in csv.DictReader(f):
        funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"] or 0)))
funcs.sort()
FSTARTS = [a for a, _, _ in funcs]
FNAME = {a: n for a, n, _ in funcs}
FSIZE = {a: s for a, _, s in funcs}

def owner(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    if i >= 0 and a < funcs[i][0] + max(funcs[i][2], 1):
        return funcs[i][1]
    return "?"

def split_ops(ops):
    return [o.strip() for o in ops.split(",")] if ops.strip() else []

def memref(op):
    m = re.search(r"(BYTE|WORD|DWORD|QWORD) PTR ", op)
    width = {"BYTE": 1, "WORD": 2, "DWORD": 4, "QWORD": 8}[m.group(1)] if m else None
    m = re.search(r"ds:0x([0-9a-f]+)", op)
    if m and "[" not in op:
        return ("abs", int(m.group(1), 16), None, None, None, None, width)
    m = re.search(r"\[([^\]]+)\]", op)
    if not m:
        return None
    disp, base, index, scale = 0, None, None, 1
    for term in re.findall(r"[+-]?[^+-]+", m.group(1)):
        term = term.strip()
        neg = term.startswith("-")
        t = term.lstrip("+-").strip()
        mm = re.fullmatch(r"(\w+)\*(\d+)", t)
        if mm:
            r, s = mm.group(1), int(mm.group(2))
            if r in ("eiz", "riz"): continue
            if s == 1:
                if base is None: base = r
                else: index, scale = r, 1
            else:
                index, scale = r, s
        elif re.fullmatch(r"0x[0-9a-f]+|\d+", t):
            v = int(t, 16) if t.startswith("0x") else int(t)
            disp += -v if neg else v
        elif t in REGW:
            if base is None: base = t
            else: index, scale = t, 1
        else:
            return ("brk", None, None, None, None, None, width)
    return ("brk", None, disp, base, index, scale, width)

def reg_of(op):
    t = op.strip()
    return t if t in REGW else None

def classify(a):
    mn, ops = INS[a]
    parts = split_ops(ops)
    if not parts:
        return (False, False, None, None, None)
    if mn in RMW1:
        mi = memref(parts[0])
        if mi: return (True, True, mi[6] or 4, mi, None)
        return (False, False, None, None, None)
    if mn == "pop":
        mi = memref(parts[0])
        if mi: return (True, False, mi[6] or 4, mi, "pop")
        return (False, False, None, None, None)
    if mn == "xchg":
        for i, p in enumerate(parts):
            mi = memref(p)
            if mi:
                other = parts[1 - i] if len(parts) == 2 else None
                return (True, True, mi[6] or (REGW.get(other, 4) if other else 4), mi, other)
        return (False, False, None, None, None)
    if mn in ("cmp", "test", "push", "fld", "fild", "bt"):
        for p in parts:
            mi = memref(p)
            if mi: return (False, True, mi[6] or 4, mi, None)
        return (False, False, None, None, None)
    if mn in ("movzx", "movsx", "imul"):
        for p in parts[1:]:
            mi = memref(p)
            if mi: return (False, True, mi[6] or REGW.get(parts[0], 4), mi, None)
        return (False, False, None, None, None)
    if mn == "lea":
        return (False, False, None, None, None)
    if mn in ("fst", "fstp", "fistp"):
        mi = memref(parts[0])
        if mi: return (True, False, mi[6] or 4, mi, "fpu")
        return (False, False, None, None, None)
    if mn in STORE_MN:
        mi = memref(parts[0])
        if mi:
            src = parts[1] if len(parts) > 1 else None
            w = mi[6] or (REGW.get(src, 4) if src else 4)
            rd = mn != "mov"
            return (True, rd, w, mi, src)
        for p in parts[1:]:
            mi = memref(p)
            if mi: return (False, True, mi[6] or REGW.get(parts[0], 4), mi, None)
    return (False, False, None, None, None)

def field_hit(mi):
    if mi is None: return None
    kind, ab, disp, base, index, scale, width = mi
    if kind == "abs":
        if ab in FADDRS: return "ABS%d" % FADDRS.index(ab)
        if ab is not None and any(ab in (f + 1, f + 2, f + 3) for f in FADDRS):
            return "SUB"
        return None
    if ALGO == "2":
        return "DISP_ANY" if disp is not None else None
    if disp == OFF: return "DISP224"
    if disp == FADDRS[0]: return "DISP94D654"
    if disp in FADDRS: return "ABSBRK%d" % FADDRS.index(disp)
    if disp is not None and any(disp in (f + 1, f + 2, f + 3) for f in FADDRS):
        return "SUB"
    return None

# ---- affine backward evaluator (M325 reviewed resolver + subreg fix) ----
def aff_add(x, y):
    if x[0] == "const" and y[0] == "const": return ("const", x[1] + y[1])
    if x[0] == "const": x, y = y, x
    if y[0] == "const": return ("lin", x[1], x[2] + y[1], x[3])
    if x[3] == y[3]: return ("lin", x[1] + y[1], x[2] + y[2], x[3])
    return None

def aff_mul(x, k):
    if x[0] == "const": return ("const", x[1] * k)
    return ("lin", x[1] * k, x[2] * k, x[3])

def stack_source(a, disp, budget):
    o = owner(a)
    i = AIDX[a]
    while i > 0 and budget[0] > 0:
        i -= 1; budget[0] -= 1
        b = ADDRS[i]
        if owner(b) != o: return None
        mn, ops = INS[b]
        parts = split_ops(ops)
        if mn == "call" and "esp" not in ops:
            STACK_CALL_CROSSINGS.append((CUR_SITE, disp, b))
            continue
        if not parts:
            if mn == "leave": return None
            continue
        mi = memref(parts[0])
        if mi and mi[0] == "brk" and mi[3] == "ebp" and mi[4] is None and mi[2] == disp:
            if mn in STORE_MN and len(parts) > 1:
                return (b, parts[1])
            return None
        if reg_of(parts[0]) == "ebp" and mn not in ("cmp", "test", "push"):
            return None
    return None

def pop_source(a, reg, budget):
    o = owner(a)
    i = AIDX[a]
    balance = 1
    if ALGO == "6":
        while i > 0 and budget[0] > 0:
            i -= 1; budget[0] -= 1
            b = ADDRS[i]
            if owner(b) != o: return None
            mn, ops = INS[b]
            if mn == "push" and ops.strip() == reg:
                return (b, reg)
            if mn == "pop" and ops.strip() == reg:
                return None
        return None
    while i > 0 and budget[0] > 0:
        i -= 1; budget[0] -= 1
        b = ADDRS[i]
        if owner(b) != o: return None
        mn, ops = INS[b]
        if mn == "push":
            balance -= 1
            if balance == 0:
                return (b, ops.strip())
        elif mn == "pop":
            balance += 1
    return None

def value_of(a, reg, depth=0, budget=None):
    if budget is None: budget = [1500]
    if depth > 4 or budget[0] <= 0: return ("lin", 1, 0, ("arg", reg))
    o = owner(a)
    i = AIDX[a]
    while i > 0 and budget[0] > 0:
        i -= 1; budget[0] -= 1
        b = ADDRS[i]
        if owner(b) != o:
            return ("lin", 1, 0, ("arg", reg))
        mn, ops = INS[b]
        parts = split_ops(ops)
        if not parts:
            if mn == "leave" and reg in ("ebp", "esp"):
                return ("lin", 1, 0, ("arg", reg))
            if mn == "cdq" and reg == "edx":
                return ("lin", 1, 0, ("arg", reg))
            if mn in ("movs", "movsb", "movsw", "movsd", "stos", "stosb", "stosw",
                      "stosd", "scas", "scasb", "scasw", "scasd", "cmps", "cmpsb",
                      "cmpsw", "cmpsd", "lods", "lodsb", "lodsw", "lodsd") and reg in (
                          "esi", "edi", "eax", "ax", "al"):
                return ("lin", 1, 0, ("arg", reg))
            continue
        if mn == "call":
            if reg in CALLER_SAVED:
                return ("lin", 1, 0, ("arg", reg))
            continue
        if mn in ("push", "cmp", "test", "bt", "nop", "ret") or mn.startswith("j"):
            continue
        dest = reg_of(parts[0])
        if dest != reg:
            # M326 FIX: a partial-register write is an OPAQUE definition of the
            # full register - the old walk skipped it and over-proved constants
            # (xor eax,eax; mov al,[rec+4] read as eax=0). ALGO=7 = old blindness.
            if ALGO != "7" and dest in PARTIALS.get(reg, ()):
                return ("lin", 1, 0, ("arg", reg))
            continue
        if mn in ("inc", "dec") and len(parts) == 1:
            v = value_of(b, reg, depth, budget)
            return aff_add(v, ("const", 1 if mn == "inc" else -1))
        if mn in ("movzx", "movsx") and len(parts) == 2:
            r = reg_of(parts[1])
            if r: return value_of(b, r, depth + 1, budget)
            return ("lin", 1, 0, ("arg", reg))
        if mn == "mov":
            src = parts[1] if len(parts) > 1 else ""
            r = reg_of(src)
            if r: return value_of(b, r, depth + 1, budget)
            m = re.fullmatch(r"0x([0-9a-f]+)", src.strip())
            if m: return ("const", int(m.group(1), 16))
            mi = memref(src)
            if mi:
                if mi[0] == "abs":
                    return ("lin", 1, 0, ("ptr", ("abs", mi[1])))
                if mi[3] == "ebp" and mi[4] is None:
                    ss = stack_source(b, mi[2], budget)
                    if ss:
                        sb, ssrc = ss
                        r2 = reg_of(ssrc)
                        if r2: return value_of(sb, r2, depth + 1, budget)
                        m2 = re.fullmatch(r"0x([0-9a-f]+)", ssrc.strip())
                        if m2: return ("const", int(m2.group(1), 16))
                return ("lin", 1, 0, ("ptr", ("brk", mi[2], mi[3], mi[4], mi[5])))
            return ("lin", 1, 0, ("arg", reg))
        if mn == "lea":
            mi = memref(parts[1]) if len(parts) > 1 else None
            if mi and mi[0] == "brk" and mi[2] is not None:
                tot = ("const", mi[2])
                if mi[3]:
                    v = value_of(b, mi[3], depth + 1, budget)
                    tot = aff_add(tot, v)
                    if tot is None: return ("lin", 1, 0, ("arg", reg))
                if mi[4]:
                    v = value_of(b, mi[4], depth + 1, budget)
                    v = aff_mul(v, mi[5])
                    tot = aff_add(tot, v)
                    if tot is None: return ("lin", 1, 0, ("arg", reg))
                return tot
            return ("lin", 1, 0, ("arg", reg))
        if mn == "imul":
            if len(parts) == 3:
                m = re.fullmatch(r"0x([0-9a-f]+)", parts[2].strip())
                r = reg_of(parts[1])
                if m and r:
                    v = value_of(b, r, depth + 1, budget)
                    return aff_mul(v, int(m.group(1), 16))
            if len(parts) == 2:
                m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
                if m:
                    v = value_of(b, reg, depth, budget)
                    return aff_mul(v, int(m.group(1), 16))
            return ("lin", 1, 0, ("arg", reg))
        if mn == "shl":
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip()) if len(parts) > 1 else None
            if m and ALGO != "4":
                v = value_of(b, reg, depth, budget)
                return aff_mul(v, 1 << int(m.group(1), 16))
            return ("lin", 1, 0, ("arg", reg))
        if mn == "sar":
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip()) if len(parts) > 1 else None
            if m:
                v = value_of(b, reg, depth, budget)
                k = 1 << int(m.group(1), 16)
                if v[0] == "const" and v[1] % k == 0: return ("const", v[1] // k)
                if v[0] == "lin" and v[1] % k == 0 and v[2] % k == 0:
                    return ("lin", v[1] // k, v[2] // k, v[3])
            return ("lin", 1, 0, ("arg", reg))
        if mn == "xor" and len(parts) == 2 and parts[0] == parts[1]:
            return ("const", 0)
        if mn in ("add", "sub") and len(parts) == 2:
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
            if m:
                v = value_of(b, reg, depth, budget)
                d = int(m.group(1), 16)
                return aff_add(v, ("const", d if mn == "add" else -d))
            r = reg_of(parts[1])
            if r:
                v1 = value_of(b, reg, depth, budget)
                v2 = value_of(b, r, depth + 1, budget)
                t = aff_add(v1, v2) if mn == "add" else aff_add(v1, aff_mul(v2, -1))
                if t: return t
            return ("lin", 1, 0, ("arg", reg))
        if mn == "pop":
            ps = pop_source(b, reg, budget)
            if ps is not None:
                pb, preg = ps
                if reg_of(preg):
                    return value_of(pb, preg, depth + 1, budget)
            return ("lin", 1, 0, ("arg", reg))
        return ("lin", 1, 0, ("arg", reg))
    return ("lin", 1, 0, ("arg", reg))

def base_tag(a, mi):
    global CUR_SITE
    CUR_SITE = a
    if ALGO == "1":
        return ("OFF", None)
    kind, ab, disp, base, index, scale, width = mi
    tot = ("const", disp)
    if base:
        tot = aff_add(tot, value_of(a, base))
    if index:
        v = aff_mul(value_of(a, index), scale)
        tot = aff_add(tot, v)
    if tot is None:
        return ("UNPROVEN", "mixed-leaves")
    if tot[0] == "const":
        v = tot[1]
        if v in FADDRS: return ("BLKCONST", v)
        return ("OUT", v)
    m, c, leaf = tot[1], tot[2], tot[3]
    if m == STRIDE and c in FADDRS:
        return ("STRIDE", (m, c, leaf))
    return ("UNPROVEN", (m, c, leaf))

def census():
    hits = []
    for a in ADDRS:
        w, r, width, mi, src = classify(a)
        if mi is None: continue
        tag = field_hit(mi)
        if tag is None: continue
        if not (w or r): continue
        hits.append((a, w, r, width, tag, mi, src))
    return hits

# ---- seed scan: BOTH sibling families, sibling-offset accesses ----
def seed_scan():
    """Seeds computing a 220- or 224-family field address (lea disp in family
    addrs, or mov reg,imm in family addrs); forward accesses [reg+d], d in
    {-4,0,4}, attributed to seed_target+d. Catches register-address stores the
    disp census misses, INCLUDING sibling-offset paths (a 220-seed writing
    [reg+4] hits 224). ALGO=3 disables the whole scan."""
    seeds, accesses = [], []
    if ALGO == "3":
        return seeds, accesses
    fams = {ENERGY_OFF: EADDRS, OFF: FADDRS}
    for a in ADDRS:
        mn, ops = INS[a]
        parts = split_ops(ops)
        if len(parts) != 2: continue
        dest = reg_of(parts[0])
        if not dest: continue
        tgt = None
        if mn == "mov":
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
            if m:
                v = int(m.group(1), 16)
                for off, addrs in fams.items():
                    if v in addrs: tgt = (off, v, "BLKCONST")
        elif mn == "lea":
            mi = memref(parts[1])
            if mi and mi[0] == "brk" and mi[2] is not None:
                for off, addrs in fams.items():
                    if mi[2] in addrs:
                        tag, det = base_tag(a, mi)
                        tgt = (off, mi[2], tag)
        if tgt is None: continue
        seeds.append((a, dest, tgt))
        off, sv, stag = tgt
        o = owner(a)
        i = AIDX[a]
        budget = 300
        while i + 1 < len(ADDRS) and budget > 0:
            i += 1; budget -= 1
            b = ADDRS[i]
            if owner(b) != o: break
            mn2, ops2 = INS[b]
            parts2 = split_ops(ops2)
            if not parts2: continue
            if mn2 == "call":
                if dest in CALLER_SAVED: break
                continue
            if mn2 in ("movs", "movsb", "movsw", "movsd", "stos", "stosb", "stosw",
                       "stosd", "scas", "scasb", "scasw", "scasd", "cmps", "cmpsb",
                       "cmpsw", "cmpsd", "lods", "lodsb", "lodsw", "lodsd") and dest in ("esi", "edi"):
                break
            w, r, width, mi, src = classify(b)
            if (w or r) and mi and mi[0] == "brk" and mi[3] == dest and mi[4] is None \
                    and mi[2] in (-4, 0, 4):
                ea = sv + mi[2]
                hit_off = None
                for off2, addrs2 in fams.items():
                    if stag == "BLKCONST":
                        if ea in addrs2: hit_off = off2
                    else:
                        # stride-family seed: constant part shifts by d
                        if mi[2] != 0 and (sv + mi[2]) in addrs2: hit_off = off2
                        elif mi[2] == 0 and sv in addrs2: hit_off = off2
                accesses.append((a, dest, b, w, width, mi[2], ea, hit_off, src, stag))
            d2 = reg_of(parts2[0])
            if d2 == dest and mn2 not in ("cmp", "test"):
                break
            if mn2 == "pop" and parts2[0] == dest:
                break
    return seeds, accesses

def turnfn_stores():
    out = []
    lo, hi = TURNFN, TURNFN + FSIZE[TURNFN]
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        w, r, width, mi, src = classify(a)
        if w and mi:
            out.append((a, width, mi, src))
    return out

def turnfn_stringops():
    out = []
    lo, hi = TURNFN, TURNFN + FSIZE[TURNFN]
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = INS[a]
        if mn in ("movs", "movsb", "movsw", "movsd", "stos", "stosb", "stosw", "stosd",
                  "rep", "repe", "repne", "scas", "cmps"):
            out.append((a, mn, ops))
    return out

def turnfn_blkstores(ts):
    out = []
    for a, width, mi, src in ts:
        kind, ab, disp, base, index, scale, _ = mi
        if kind == "abs":
            if ab is not None and BLKBASE <= ab < BLKEND: out.append(a)
        elif disp is not None:
            if disp in FADDRS or disp == OFF:
                out.append(a)
            else:
                tag, det = base_tag(a, mi)
                if tag in ("BLKCONST", "STRIDE") or (
                        isinstance(det, int) and BLKBASE <= det < BLKEND):
                    out.append(a)
    return out

def pe_bytes(addr, n):
    pe = open(PE, "rb").read()
    p = os.environ.get("M326_PE_PATCH")
    if p:
        pe = bytearray(pe)
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            a, hx = chunk.split("|", 1)
            a = int(a, 16)
            off = a - IMG_BASE
            raw = bytes.fromhex(hx)
            pe[off:off + len(raw)] = raw
        pe = bytes(pe)
    e = struct.unpack_from("<I", pe, 0x3c)[0]
    opt = e + 24
    nsec = struct.unpack_from("<H", pe, e + 6)[0]
    secoff = opt + struct.unpack_from("<H", pe, e + 20)[0]
    rva = addr - IMG_BASE
    for i in range(nsec):
        o = secoff + i * 40
        vs, va, rs, rp = struct.unpack_from("<IIII", pe, o + 8)
        if va <= rva < va + max(vs, rs):
            return pe[rp + (rva - va):rp + (rva - va) + n]
    return None

def pe_cstr(addr):
    b = pe_bytes(addr, 64)
    return b.split(b"\0")[0] if b else None

def pe_sections():
    pe = open(PE, "rb").read()
    e = struct.unpack_from("<I", pe, 0x3c)[0]
    opt = e + 24
    nsec = struct.unpack_from("<H", pe, e + 6)[0]
    secoff = opt + struct.unpack_from("<H", pe, e + 20)[0]
    out = []
    for i in range(nsec):
        o = secoff + i * 40
        name = pe[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vs, va, rs, rp = struct.unpack_from("<IIII", pe, o + 8)
        out.append((name, va, vs, rp, rs))
    return pe, out

def scan_strings(substrs):
    pe, secs = pe_sections()
    out = []
    for name, va, vs, rp, rs in secs:
        if name not in (".rdata", ".data"): continue
        blob = pe[rp:rp + rs]
        for m in re.finditer(rb"[\x20-\x7e]{4,}", blob):
            s = m.group(0)
            if any(t.encode() in s.upper() for t in substrs):
                out.append((IMG_BASE + va + m.start(), s))
    return out

def callers_of(target):
    out = []
    for a in ADDRS:
        mn, ops = INS[a]
        if mn == "call":
            m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            if m and int(m.group(1), 16) == target:
                out.append(a)
    return out

def push_refs(va):
    out = []
    for a in ADDRS:
        mn, ops = INS[a]
        if mn == "push" and re.fullmatch(r"0x%x" % va, ops.strip()):
            out.append(a)
    return out

def slot_stores(fn, disp):
    out = []
    lo, hi = fn, fn + FSIZE[fn]
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = INS[a]
        parts = split_ops(ops)
        if not parts: continue
        mi = memref(parts[0])
        if mi and mi[0] == "brk" and mi[3] == "ebp" and mi[4] is None \
                and mi[2] == disp and mn in STORE_MN:
            out.append(a)
    return out

def reg_defs_between(lo, hi, reg):
    out = []
    for a in ADDRS:
        if a <= lo or a > hi: continue
        mn, ops = INS[a]
        parts = split_ops(ops)
        if not parts: continue
        d = reg_of(parts[0])
        if (d == reg or d in PARTIALS.get(reg, ())) and mn not in ("cmp", "test", "push"):
            out.append((a, mn, ops))
    return out

def save_values():
    m = ds.parse(SAVE)
    rows, notes = ds.walk(m["data"])
    blk = [r for r in rows if r[2] == "block A"]
    if len(blk) != 1: return None
    off = blk[0][0]
    d = m["data"]
    vals = [struct.unpack_from("<I", d, off + k * STRIDE + OFF)[0] for k in range(NBLK)]
    evals = [struct.unpack_from("<I", d, off + k * STRIDE + ENERGY_OFF)[0] for k in range(NBLK)]
    gap = [r for r in rows if r[0] == off - 4]
    sha = hashlib.sha256(d).hexdigest()[:16]
    return {"off": off, "vals": vals, "energy": evals, "sha": sha, "size": len(d),
            "year": m["year"], "round": struct.unpack_from("<I", d, 0x50)[0],
            "gap": gap[0] if gap else None,
            "gapval": struct.unpack_from("<I", d, off - 4)[0]}

def m325_crosscheck():
    """Re-run M325's census pipeline with the subreg fix applied to ITS resolver
    (source transform, same two lines) and diff against the unmodified module.
    Measures whether M325's published +0x220 numbers move under the fix."""
    import importlib.util
    src_path = os.path.join(ROOT, "scripts", "m325_block220_census.py")
    src = open(src_path).read()
    old = "        dest = reg_of(parts[0])\n        if dest != reg: continue\n"
    new = ("        dest = reg_of(parts[0])\n        if dest != reg:\n"
           "            if dest in PARTIALS.get(reg, ()):\n"
           "                return (\"lin\", 1, 0, (\"arg\", reg))\n"
           "            continue\n")
    if src.count(old) != 1:
        return {"error": "anchor count %d" % src.count(old)}
    fixed_src = src.replace(old, new)
    fixed_src = fixed_src.replace("PARTIALS = {", "PARTIALS = {")  # no-op guard
    # inject PARTIALS (M325 source lacks it)
    fixed_src = fixed_src.replace(
        "CALLER_SAVED = {\"eax\", \"ecx\", \"edx\"}",
        "CALLER_SAVED = {\"eax\", \"ecx\", \"edx\"}\n"
        "PARTIALS = {\"eax\": {\"al\", \"ah\", \"ax\"}, \"ebx\": {\"bl\", \"bh\", \"bx\"},\n"
        "            \"ecx\": {\"cl\", \"ch\", \"cx\"}, \"edx\": {\"dl\", \"dh\", \"dx\"},\n"
        "            \"esi\": {\"si\"}, \"edi\": {\"di\"}, \"ebp\": {\"bp\"}, \"esp\": {\"sp\"}}")
    spec = importlib.util.spec_from_loader("m325_fixed", loader=None)
    assert spec is not None
    fx = importlib.util.module_from_spec(spec)
    fx.__file__ = src_path
    exec(compile(fixed_src, src_path + " (subreg-fixed)", "exec"), fx.__dict__)
    import m325_block220_census as orig
    diffs = []
    ho, hf = orig.census(), fx.census()
    so = {a: (w, r, wd, t) for a, w, r, wd, t, _, _ in ho}
    sf = {a: (w, r, wd, t) for a, w, r, wd, t, _, _ in hf}
    if so != sf:
        diffs.append(("census-hits", sorted(set(so) ^ set(sf))))
    po = {a: orig.base_tag(a, mi) for a, w, r, wd, t, mi, s in ho}
    pf = {a: fx.base_tag(a, mi) for a, w, r, wd, t, mi, s in hf}
    for a in sorted(set(po) | set(pf)):
        if po.get(a) != pf.get(a):
            diffs.append(("prov", hex(a), str(po.get(a)), str(pf.get(a))))
    ro, rf = [], []
    for sa, reg, stag in orig.addr_seeds():
        for b, w, wd, s in orig.forward_stores(sa, reg):
            (ro if w else rf).append((sa, reg, b, wd, s, stag[0]))
    xo, xf = [], []
    for sa, reg, stag in fx.addr_seeds():
        for b, w, wd, s in fx.forward_stores(sa, reg):
            (xo if w else xf).append((sa, reg, b, wd, s, stag[0]))
    if sorted(ro) != sorted(xo): diffs.append(("regwr", len(ro), len(xo)))
    if sorted(rf) != sorted(xf): diffs.append(("regrd", len(rf), len(xf)))
    if len(orig.addr_seeds()) != len(fx.addr_seeds()):
        diffs.append(("seeds", len(orig.addr_seeds()), len(fx.addr_seeds())))
    return {"diffs": diffs, "hits": len(hf), "regwr": len(xo), "regrd": len(xf),
            "seeds": len(fx.addr_seeds())}

def main():
    print("== M326: block+0x224 census (STATIC) ==")
    print("T0 field=%s stride=%s nblk=%d" % (
        ",".join(hex(x) for x in FADDRS), hex(STRIDE), NBLK))
    hits = census()
    rows = []
    for a, w, r, width, tag, mi, src in hits:
        kind, ab, disp, base, index, scale, _ = mi
        if kind == "abs":
            prov, det = ("ABS", ab)
        else:
            prov, det = base_tag(a, mi)
        rows.append({"a": a, "w": w, "r": r, "width": width, "tag": tag,
                     "prov": prov, "det": det, "src": src, "owner": owner(a), "mi": mi})
    writers = [x for x in rows if x["w"]]
    readers = [x for x in rows if x["r"] and not x["w"]]
    wr_unprov = [x for x in writers if x["prov"] in ("UNPROVEN", "OFF", "OUT")]
    print("T1 hits=%d writers=%d readers=%d wr_unproven=%d" % (
        len(hits), len(writers), len(readers), len(wr_unprov)))
    for x in rows:
        det = x["det"]
        if isinstance(det, int):
            ds_ = hex(det)
        elif isinstance(det, tuple) and len(det) == 3 and isinstance(det[0], int):
            ds_ = "%d*leaf+%s leaf=%s" % (det[0], hex(det[1]), det[2])
        else:
            ds_ = str(det)
        print("  %s %s%s w=%s %s prov=%s det=%s src=%s owner=%s" % (
            hex(x["a"]), "W" if x["w"] else "-", "R" if x["r"] else "-", x["width"],
            x["tag"], x["prov"], ds_, x["src"], x["owner"]))
    wowners = sorted(set(x["owner"] for x in writers))
    print("T2 writer owners (%d): %s" % (len(wowners), ",".join(wowners)))
    seeds, accesses = seed_scan()
    s220 = [s for s in seeds if s[2][0] == ENERGY_OFF]
    s224 = [s for s in seeds if s[2][0] == OFF]
    sib224 = [x for x in accesses if x[7] == OFF and x[5] != 0]
    regwr = [x for x in accesses if x[7] == OFF and x[5] == 0 and x[3]]
    regrd = [x for x in accesses if x[7] == OFF and x[5] == 0 and not x[3]]
    print("T3 seeds220=%d seeds224=%d accesses=%d sibling-offset-into-224=%d regwr224=%d regrd224=%d" % (
        len(s220), len(s224), len(accesses), len(sib224), len(regwr), len(regrd)))
    for a, dest, b, w, wd, d, ea, hit, src, stag in accesses:
        if hit == OFF or (d != 0):
            print("  seed %s (%s,%s) -> %s %s d=%+d ea=%s hit=%s src=%s owner=%s" % (
                hex(a), dest, stag, "W" if w else "R", hex(b), d, hex(ea),
                hex(hit) if hit else "-", src, owner(b)))
    ts = turnfn_stores()
    tso = turnfn_stringops()
    blkstores = turnfn_blkstores(ts)
    print("T4 turnfn stores=%d stringops=%d block-region stores=%d" % (
        len(ts), len(tso), len(blkstores)))
    # ---- settle law (FUN_005208f0) ----
    fold_sites = [0x520afc, 0x520afe, 0x520b01, 0x520b03, 0x520b06, 0x520b09, 0x520b0b]
    fold = {hex(a): INS.get(a) for a in fold_sites}
    fold_val = value_of(0x520b0e, "eax")
    settle = {"read224": INS.get(0x520b0e), "read220": INS.get(0x520b14),
              "sub": INS.get(0x520b1a), "store220": INS.get(0x520b1c),
              "zero224": INS.get(0x520b22), "clamp_cmp": INS.get(0x520b28),
              "clamp_jcc": INS.get(0x520b2e), "clamp_store": INS.get(0x520b30),
              "esi_zero": INS.get(0x520ada)}
    esidefs = reg_defs_between(0x520ada, 0x520b30, "esi")
    print("T5 settle fold=%s fold_val=%s" % (fold, fold_val))
    print("T5b settle=%s esidefs=%s" % (settle, esidefs))
    # ---- HURRY naming + add-leg gate (FUN_00419c30) ----
    strs = {hex(a): pe_cstr(a) for a in (0x689990, 0x6899a4, 0x6899c0)}
    hurry_pushes = {hex(va): [(hex(a), owner(a)) for a in push_refs(va)]
                    for va in (0x689990, 0x6899a4, 0x6899c0)}
    addleg = {"gate1_load": INS.get(0x41a530), "gate1_test": INS.get(0x41a535),
              "gate1_jcc": INS.get(0x41a537), "gate2_load": INS.get(0x41a539),
              "gate2_test": INS.get(0x41a53f), "gate2_jcc": INS.get(0x41a541),
              "add": INS.get(0x41a543), "skip": INS.get(0x41a549),
              "pay_read220": INS.get(0x41a54b), "pay_read91c64c": INS.get(0x41a551),
              "pay_sub220": INS.get(0x41a557), "pay_sub91c64c": INS.get(0x41a559),
              "pay_store220": INS.get(0x41a55d), "pay_store91c64c": INS.get(0x41a563)}
    bytechain = {"rec_ptr": INS.get(0x419d89), "xor": INS.get(0x419d8f),
                 "byte_load": INS.get(0x419d91), "slot_store": INS.get(0x419d94),
                 "slot_use1": INS.get(0x419e5a), "slot_use2": INS.get(0x419f6a),
                 "fold": [INS.get(a) for a in (0x419f68, 0x419f6d, 0x419f70,
                                                0x419f72, 0x419f75, 0x419f78, 0x419f7a)]}
    slot20 = slot_stores(0x419c30, -0x20)
    slotc = slot_stores(0x416730, -0xc)
    bytechain2 = {"xor": INS.get(0x4168ff), "byte_load": INS.get(0x416901),
                  "slot_store": INS.get(0x41690d), "slot_use": INS.get(0x416984)}
    phase = {"f1": INS.get(0x520c99), "turncall": INS.get(0x520ca3),
             "f2": INS.get(0x520cf8), "upkeepcall": INS.get(0x520d02),
             "fclear": INS.get(0x520d1d), "upk_set": INS.get(0x5208fa),
             "upk_clear": INS.get(0x520b55)}
    g920 = sum(1 for a in ADDRS if re.search(r"ds:0x920434\b", INS[a][1]))
    g62c = sum(1 for a in ADDRS if re.search(r"ds:0x91c62c\b", INS[a][1]))
    print("T6 strings=%s pushes=%s" % (strs, hurry_pushes))
    print("T6b addleg=%s" % addleg)
    print("T6c bytechain=%s slot20stores=%s" % (bytechain, [hex(a) for a in slot20]))
    print("T6d bytechain2=%s slotcstores=%s" % (bytechain2, [hex(a) for a in slotc]))
    print("T6e phase=%s refs920434=%d refs91c62c=%d" % (phase, g920, g62c))
    # ---- reader law: every reader computes 220-224 ----
    triples = [(0x4169a6, 0x4169ac, 0x4169b2), (0x419f7d, 0x419f83, 0x419f89),
               (0x419ffa, 0x41a000, 0x41a006), (0x41a100, 0x41a106, 0x41a10c),
               (0x41a3cc, 0x41a3d2, 0x41a3d8), (0x41a3e8, 0x41a3ee, 0x41a3f4),
               (0x41a4d4, 0x41a4da, 0x41a4e6), (0x440b8f, 0x440b95, 0x440b95),
               (0x462368, 0x46236e, 0x46236e), (0x520b14, 0x520b0e, 0x520b1a)]
    tl = []
    for l220, l224, sub in triples:
        tl.append((hex(l220), INS.get(l220), hex(l224), INS.get(l224), hex(sub), INS.get(sub)))
    itoa = {"base": INS.get(0x416987), "call": INS.get(0x4169b5)}
    cap = {"g999_load": INS.get(0x41a4e0), "guard1": INS.get(0x41a4e8),
           "guard1_jcc": INS.get(0x41a4ea), "guard2": INS.get(0x41a4ec),
           "guard2_jcc": INS.get(0x41a4ee), "cmp": INS.get(0x41a4f0),
           "jcc": INS.get(0x41a4f2), "take_eax": INS.get(0x41a4f4),
           "take_ecx": INS.get(0x41a4f9), "zero": INS.get(0x41a4fe)}
    # MIN derived: jle jumps to take_ecx when ecx<=eax -> result=min(ecx,eax)
    capdir = "SHAPE-CHANGED"
    if cap["jcc"] and cap["cmp"] and cap["take_ecx"] and cap["take_eax"]:
        tgt = int(cap["jcc"][1], 16)
        if cap["cmp"][0] == "cmp" and cap["cmp"][1] == "ecx,eax" and tgt == 0x41a4f9:
            capdir = {"jle": "MIN", "jg": "MAX", "jl": "MAX", "jge": "MIN"}.get(
                cap["jcc"][0], "SHAPE-CHANGED")
    print("T7 reader-triples=%s" % tl)
    print("T7b itoa=%s cheatcap=%s dir=%s" % (itoa, cap, capdir))
    # ---- reset + save ----
    reset = {"xor": INS.get(0x59f0bf), "store": INS.get(0x59f0c1),
             "owner": owner(0x59f0c1)}
    sv = save_values()
    leg = {"sz_push": INS.get(0x596a7e), "dst_push": INS.get(0x596a83),
           "read_branch": INS.get(0x596a88), "read_call": INS.get(0x596a91),
           "write_call": INS.get(0x596a8a)}
    print("T8 reset=%s save=%s" % (reset, sv))
    print("T8b codec-leg=%s field-file-offsets=%s" % (
        leg, [hex(0x32c + k * STRIDE + OFF) for k in range(NBLK)]))
    loan_strs = {hex(va): pe_cstr(va) for va in (0x676944, 0x676950, 0x68fe24,
                                                 0x6901e8, 0x690468, 0x690b1c, 0x690d10)}
    loan_owners = sorted(set(owner(a) for va in
                             (0x676944, 0x676950, 0x68fe24, 0x6901e8, 0x690468, 0x690b1c, 0x690d10)
                             for a in push_refs(va)))
    debt_strs = scan_strings(["DEBT", "ARREAR"])
    print("T9 loan=%s owners=%s debt-strings=%d" % (loan_strs, loan_owners, len(debt_strs)))
    xc = m325_crosscheck()
    print("T10 M325-subreg-fix crosscheck: %s" % xc)
    cross_sites = sorted(set(s for s, _, _ in STACK_CALL_CROSSINGS if s is not None))
    print("T11 stack-forward call-crossings (DECLARED linear limit): events=%d sites=%d" % (
        len(STACK_CALL_CROSSINGS), len(cross_sites)))
    # ---- gates ----
    G = []
    def gate(name, ok, detail):
        G.append(ok)
        print("%s %s %s" % (name, "PASS" if ok else "FAIL", detail))
    n_abs = sum(1 for x in rows if x["mi"][0] == "abs")
    n_224 = sum(1 for x in rows if x["tag"] == "DISP224")
    n_sub = sum(1 for x in rows if x["tag"] == "SUB")
    n_dw = sum(1 for x in rows if x["width"] == 4)
    exp_wrsites = [0x41a543, 0x520b22, 0x59f0c1]
    exp_rdsites = [0x4169ac, 0x419f83, 0x41a000, 0x41a106, 0x41a3d2, 0x41a3ee,
                   0x41a4da, 0x440b95, 0x46236e, 0x520b0e]
    gate("G1", len(hits) == 13 and len(writers) == 3 and len(readers) == 10
         and n_abs == 0 and n_224 == 0 and n_sub == 0 and n_dw == len(rows)
         and sorted(x["a"] for x in writers) == exp_wrsites
         and sorted(x["a"] for x in readers) == exp_rdsites,
         "hits=%d W=%d R=%d abs=%d disp224=%d sub=%d dw=%d/%d wrsites=%s rdsites-pinned=%d" % (
             len(hits), len(writers), len(readers), n_abs, n_224, n_sub, n_dw,
             len(rows), [hex(a) for a in sorted(x["a"] for x in writers)], len(exp_rdsites)))
    # G2: provenance under the FIXED resolver + the byte-load chains
    exp_prov = {
        0x4169ac: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x419f83: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a000: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a106: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a3d2: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a3ee: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a4da: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x41a543: ("STRIDE", (8380, 0x94d654, ("arg", "eax"))),
        0x440b95: ("STRIDE", (8380, 0x94d654, ("ptr", ("abs", 0x91b5b4)))),
        0x46236e: ("STRIDE", (8380, 0x94d654, ("ptr", ("abs", 0x91b5b4)))),
        0x520b0e: ("STRIDE", (8380, 0x94d654, ("ptr", ("brk", 8, "ebp", None, 1)))),
        0x520b22: ("STRIDE", (8380, 0x94d654, ("ptr", ("brk", 8, "ebp", None, 1)))),
        0x59f0c1: ("STRIDE", (8380, 0x94d654, ("ptr", ("brk", 8, "ebp", None, 1)))),
    }
    prov_ok = all((x["prov"], x["det"]) == exp_prov.get(x["a"]) for x in rows) \
        and len(rows) == len(exp_prov)
    bc_ok = (bytechain["rec_ptr"] == ("mov", "edx,DWORD PTR ds:0x8f0d60")
             and bytechain["xor"] == ("xor", "eax,eax")
             and bytechain["byte_load"] == ("mov", "al,BYTE PTR [edx+0x4]")
             and bytechain["slot_store"] == ("mov", "DWORD PTR [ebp-0x20],eax")
             and bytechain["slot_use1"] == ("mov", "esi,DWORD PTR [ebp-0x20]")
             and bytechain["slot_use2"] == ("mov", "ebx,DWORD PTR [ebp-0x20]")
             and slot20 == [0x419d94]
             and bytechain2["xor"] == ("xor", "eax,eax")
             and bytechain2["byte_load"] == ("mov", "al,BYTE PTR [ecx+0x4]")
             and bytechain2["slot_store"] == ("mov", "DWORD PTR [ebp-0xc],eax")
             and bytechain2["slot_use"] == ("mov", "ecx,DWORD PTR [ebp-0xc]")
             and slotc == [0x41690d])
    gate("G2", prov_ok and bc_ok and len(wr_unprov) == 0,
         "prov-pinned=%s (13 STRIDE, 0 BLKCONST/UNPROVEN) bytechains=%s slot20=%s slotc=%s" % (
             prov_ok, bc_ok, [hex(a) for a in slot20], [hex(a) for a in slotc]))
    gate("G3", len(s224) == 0 and len(regwr) == 0 and len(regrd) == 0
         and len(s220) == 30 and len(sib224) == 0,
         "seeds220=%d (M325 cross-check=30) seeds224=%d regwr=%d regrd=%d sibling-offset-into-224=%d accesses=%d" % (
             len(s220), len(s224), len(regwr), len(regrd), len(sib224), len(accesses)))
    fold_ok = (fold == {"0x520afc": ("mov", "eax,edi"), "0x520afe": ("shl", "eax,0x6"),
                        "0x520b01": ("add", "eax,edi"), "0x520b03": ("lea", "eax,[edi+eax*2]"),
                        "0x520b06": ("shl", "eax,0x4"), "0x520b09": ("sub", "eax,edi"),
                        "0x520b0b": ("shl", "eax,0x2")}
               and fold_val == ("lin", STRIDE, 0, ("ptr", ("brk", 8, "ebp", None, 1))))
    settle_ok = (settle["read224"] == ("mov", "ecx,DWORD PTR [eax+0x94d654]")
                 and settle["read220"] == ("mov", "edx,DWORD PTR [eax+0x94d650]")
                 and settle["sub"] == ("sub", "edx,ecx")
                 and settle["store220"] == ("mov", "DWORD PTR [eax+0x94d650],edx")
                 and settle["zero224"] == ("mov", "DWORD PTR [eax+0x94d654],esi")
                 and settle["clamp_cmp"] == ("cmp", "DWORD PTR [eax+0x94d650],esi")
                 and settle["clamp_jcc"] == ("jge", "0x520b36")
                 and settle["clamp_store"] == ("mov", "DWORD PTR [eax+0x94d650],esi")
                 and settle["esi_zero"] == ("xor", "esi,esi")
                 and esidefs == []
                 and 0x520b2e < 0x520b30 < 0x520b36)
    gate("G4", fold_ok and settle_ok,
         "fold=%s fold_val=%s settle=%s esidefs=%s (ENERGY-=224; 224:=0; ENERGY=max(ENERGY,0))" % (
             fold_ok, fold_val, settle_ok, esidefs))
    rel_ok = (strs == {"0x689990": b"HURRY", "0x6899a4": b"HURRYOPTIONS",
                       "0x6899c0": b"HURRYPAYMENT"}
              and hurry_pushes == {"0x689990": [("0x419fa6", "FUN_00419c30")],
                                   "0x6899a4": [("0x41a014", "FUN_00419c30")],
                                   "0x6899c0": [("0x41a402", "FUN_00419c30")]}
              and owner(0x41a543) == "FUN_00419c30")
    addleg_ok = (addleg["gate1_load"] == ("mov", "eax,ds:0x920434")
                 and addleg["gate1_test"] == ("test", "eax,eax")
                 and addleg["gate1_jcc"] == ("je", "0x41a54b")
                 and addleg["gate2_load"] == ("mov", "ecx,DWORD PTR ds:0x91c62c")
                 and addleg["gate2_test"] == ("test", "ecx,ecx")
                 and addleg["gate2_jcc"] == ("je", "0x41a54b")
                 and addleg["add"] == ("add", "DWORD PTR [esi+0x94d654],edi")
                 and addleg["skip"] == ("jmp", "0x41a577")
                 and addleg["pay_read220"] == ("mov", "ecx,DWORD PTR [esi+0x94d650]")
                 and addleg["pay_read91c64c"] == ("mov", "edx,DWORD PTR ds:0x91c64c")
                 and addleg["pay_sub220"] == ("sub", "ecx,edi")
                 and addleg["pay_sub91c64c"] == ("sub", "edx,edi")
                 and addleg["pay_store220"] == ("mov", "DWORD PTR [esi+0x94d650],ecx")
                 and addleg["pay_store91c64c"] == ("mov", "DWORD PTR ds:0x91c64c,edx")
                 and 0x41a537 < 0x41a543 < 0x41a549 < 0x41a54b < 0x41a577)
    phase_ok = (phase["f1"] == ("mov", "DWORD PTR ds:0x91c62c,0x1")
                and phase["turncall"] == ("call", "0x51f320")
                and phase["f2"] == ("mov", "DWORD PTR ds:0x91c62c,0x1")
                and phase["upkeepcall"] == ("call", "0x5208f0")
                and phase["fclear"] == ("mov", "DWORD PTR ds:0x91c62c,edi")
                and phase["upk_set"] == ("mov", "DWORD PTR ds:0x91c628,0x1")
                and phase["upk_clear"] == ("mov", "DWORD PTR ds:0x91c628,esi")
                and 0x520c99 < 0x520ca3 and 0x520cf8 < 0x520d02)
    gate("G5", rel_ok and addleg_ok and phase_ok,
         "HURRY-relation=%s addleg=%s phase=%s (defer iff 920434!=0 AND 91c62c!=0; refs=%d/%d)" % (
             rel_ok, addleg_ok, phase_ok, g920, g62c))
    triples_ok = True
    for l220, l224, sub in triples:
        i220, i224, isub = INS.get(l220), INS.get(l224), INS.get(sub)
        if l224 == sub:  # fused sub eax,[edx+224]
            ok = (i220 and i220[0] == "mov" and "0x94d650" in i220[1]
                  and isub and isub[0] == "sub" and "0x94d654" in isub[1])
        else:
            ok = (i220 and i220[0] == "mov" and "0x94d650" in i220[1]
                  and i224 and i224[0] == "mov" and "0x94d654" in i224[1]
                  and isub and isub[0] == "sub")
        triples_ok = triples_ok and ok
    cap_ok = (cap["g999_load"] == ("mov", "ecx,DWORD PTR ds:0x999fa4")
              and cap["guard1"] == ("test", "ecx,ecx") and cap["guard1_jcc"] == ("jl", "0x41a4fe")
              and cap["guard2"] == ("test", "eax,eax") and cap["guard2_jcc"] == ("jl", "0x41a4fe")
              and cap["cmp"] == ("cmp", "ecx,eax") and cap["jcc"] == ("jle", "0x41a4f9")
              and cap["take_eax"] == ("mov", "DWORD PTR [ebp-0x14],eax")
              and cap["take_ecx"] == ("mov", "DWORD PTR [ebp-0x14],ecx")
              and cap["zero"] == ("mov", "DWORD PTR [ebp-0x14],0x0")
              and capdir == "MIN"
              and itoa["base"] == ("push", "0xa") and itoa["call"] == ("call", "0x64f980"))
    gate("G6", triples_ok and len(triples) == len(readers) and cap_ok,
         "all %d readers compute 220-224=%s itoa=%s cheatcap-MIN=%s (g999fa4 consumer @41a4e0)" % (
             len(readers), triples_ok, itoa, capdir))
    gate("G7", reset["xor"] == ("xor", "eax,eax")
         and reset["store"] == ("mov", "DWORD PTR [ebx+0x94d654],eax")
         and reset["owner"] == "FUN_0059ec90"
         and len(ts) == 16 and len(tso) == 0 and len(blkstores) == 0,
         "reset=%s turnfn stores=%d stringops=%d blkstores=%d (M325 G4 cross-check)" % (
             reset, len(ts), len(tso), len(blkstores)))
    gate("G8", sv is not None and sv["off"] == 0x32c
         and sv["vals"] == [0] * 8
         and sv["energy"] == [10, 28, 112, 69, 229, 60, 102, 37]
         and sv["sha"] == "74d0f44ab9b9290b" and sv["size"] == 242539
         and sv["year"] == 2150 and sv["round"] == 50
         and sv["gap"] == (808, 4, "own player", "DAT_0091b5b4") and sv["gapval"] == 3
         and leg["sz_push"] == ("push", "0x105e0")
         and leg["dst_push"] == ("push", "0x94d430")
         and leg["read_branch"] == ("je", "0x596a91")
         and leg["read_call"] == ("call", "0x64cc00")
         and leg["write_call"] == ("call", "0x64c9a0")
         and 0x105e0 == NBLK * STRIDE and OFF < STRIDE,
         "save=%s leg=%s (raw block carry; gap=own-player idx; file@550+k*20bc)" % (sv, leg))
    r1 = sv is not None and all(sv["vals"][k] == sv["energy"][k] for k in range(NBLK))
    r2 = len(blkstores) > 0
    r3 = settle["sub"] is not None and settle["sub"][0] == "add"
    r4 = not (addleg["gate1_jcc"] and addleg["gate1_jcc"][0] == "je")
    r5 = bool(set(loan_owners) & set(wowners))
    r6 = len(debt_strs) > 0
    gate("G9", (not r1) and (not r2) and (not r3) and (not r4) and (not r5) and (not r6),
         "R1 energy-copy=%s R2 turnfn-writes=%s R3 settle-adds=%s R4 unconditional-defer=%s "
         "R5 LOAN-noun-in-writers=%s R6 DEBT-string-exists=%s (all must be False; loan_owners=%s)" % (
             r1, r2, r3, r4, r5, r6, loan_owners))
    # digest over measured detail
    d = hashlib.sha256()
    for x in rows:
        d.update(repr((x["a"], x["w"], x["r"], x["width"], x["tag"], x["prov"],
                       str(x["det"]), x["src"], x["owner"])).encode())
    d.update(repr((len(s220), len(s224), len(accesses),
                   sorted((a, b, dd, ea, h) for a, _, b, _, _, dd, ea, h, _, _ in accesses))).encode())
    d.update(repr((fold, str(fold_val), settle, esidefs)).encode())
    d.update(repr((strs, hurry_pushes, addleg, bytechain, slot20, bytechain2,
                   slotc, phase, g920, g62c)).encode())
    d.update(repr((tl, itoa, cap, capdir)).encode())
    d.update(repr((reset, len(ts), len(tso), sorted(blkstores))).encode())
    d.update(repr((sv, leg)).encode())
    d.update(repr((loan_strs, loan_owners, len(debt_strs))).encode())
    d.update(repr(xc).encode())
    d.update(repr((len(STACK_CALL_CROSSINGS), cross_sites)).encode())
    print("DIGEST %s" % d.hexdigest()[:16])
    print("== M326: %d/%d ==" % (sum(G), len(G)))
    return 0 if all(G) else 1

if __name__ == "__main__":
    sys.exit(main())