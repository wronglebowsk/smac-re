#!/usr/bin/env python3
# M326: block+0x224 - the DEBT SIBLING of ENERGY (M325's carried OPEN).
# QUESTION: what is the per-faction field at block+0x224 (0x94d430+k*0x20bc+0x224),
# who writes/reads it, and what are its settle/add/clamp laws? M325 pinned the
# settle path @520b1c/b30 (field220 -= field224, field224 = 0, clamp) and an
# add-leg @41a543. STATIC, zero box. Footing: NAMED ## M325 (ENERGY, currency
# pins), ## M324 (raw carry), ## M320 (block layout), ## M316 (stride/base).
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers;
# digest hashes the MEASURED detail; declared sets MEASURED not authored.
# Resolver: IDENTICAL to the reviewed M325 resolver (linear backward def-walk
# <=300 instrs depth<=4, affine over opaque runtime leaves, linear stack-slot
# forwarding with call-crossings enumerated, LIFO-sound pop pairing,
# register-address forward scan stops at redefinition; calls clobber eax/ecx/edx).
# Mutants: M326_PATCH addr|mn ops, M326_PE_PATCH addr|hex, M326_ALGO 1=provenance
# off 2=disp-match widened 3=forward-scan off 4=shl-blind 6=old-pop-pairing,
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
IMG_BASE = 0x400000

STORE_MN = {"mov", "xchg", "add", "adc", "sub", "sbb", "inc", "dec", "or", "and",
            "xor", "not", "neg", "movnti", "pop", "cmpxchg", "xadd", "bts", "btr", "btc"}
RMW1 = {"inc", "dec", "not", "neg"}
REGW = {"eax": 4, "ebx": 4, "ecx": 4, "edx": 4, "esi": 4, "edi": 4, "ebp": 4, "esp": 4,
        "ax": 2, "bx": 2, "cx": 2, "dx": 2, "si": 2, "di": 2, "bp": 2, "sp": 2,
        "al": 1, "bl": 1, "cl": 1, "dl": 1, "ah": 1, "bh": 1, "ch": 1, "dh": 1}
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

# ---- affine backward evaluator (verbatim M325 reviewed resolver) ----
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
        if dest != reg: continue
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

def addr_seeds():
    seeds = []
    if ALGO == "3":
        return seeds
    for a in ADDRS:
        mn, ops = INS[a]
        parts = split_ops(ops)
        if len(parts) != 2: continue
        dest = reg_of(parts[0])
        if not dest: continue
        if mn == "mov":
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
            if m and int(m.group(1), 16) in FADDRS:
                seeds.append((a, dest, ("BLKCONST", int(m.group(1), 16))))
        elif mn == "lea":
            mi = memref(parts[1])
            if mi and mi[0] == "brk" and mi[2] in FADDRS:
                tag, det = base_tag(a, mi)
                seeds.append((a, dest, (tag, det)))
    return seeds

def forward_stores(seed_a, reg):
    out = []
    o = owner(seed_a)
    i = AIDX[seed_a]
    budget = 300
    while i + 1 < len(ADDRS) and budget > 0:
        i += 1; budget -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        parts = split_ops(ops)
        if not parts: continue
        if mn == "call":
            if reg in CALLER_SAVED: break
            continue
        if mn in ("movs", "movsb", "movsw", "movsd", "stos", "stosb", "stosw", "stosd",
                  "scas", "scasb", "scasw", "scasd", "cmps", "cmpsb", "cmpsw", "cmpsd",
                  "lods", "lodsb", "lodsw", "lodsd") and reg in ("esi", "edi"):
            break
        w, r, width, mi, src = classify(b)
        if (w or r) and mi and mi[0] == "brk" and mi[3] == reg and mi[4] is None and mi[2] == 0:
            out.append((b, w, width, src))
        dest = reg_of(parts[0])
        if dest == reg and mn not in ("cmp", "test"):
            break
        if mn == "pop" and parts[0] == reg:
            break
    return out

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

def scan_strings(substrs, lo=None, hi=None):
    """All printable-ASCII runs >=4 chars in data sections whose VA is in
    [lo,hi) (if given) and that contain one of substrs (case-insensitive)."""
    pe, secs = pe_sections()
    out = []
    for name, va, vs, rp, rs in secs:
        if name not in (".rdata", ".data"): continue
        blob = pe[rp:rp + rs]
        for m in re.finditer(rb"[\x20-\x7e]{4,}", blob):
            sva = IMG_BASE + va + m.start()
            if lo is not None and not (lo <= sva < hi): continue
            s = m.group(0)
            if substrs and not any(t.encode() in s.upper() for t in substrs): continue
            out.append((sva, s))
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
        if mn in ("push", "mov"):
            m = re.search(r"0x([0-9a-f]+)", ops)
            if m and int(m.group(1), 16) == va and (mn == "push" or ops.startswith("e")):
                out.append((a, mn, ops))
    return out

def dump_window(lo, hi, label):
    print("-- window %s [%s,%s) owner=%s --" % (label, hex(lo), hex(hi), owner(lo)))
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = INS[a]
        print("  %s: %s %s" % (hex(a), mn, ops))

def save_values():
    m = ds.parse(SAVE)
    rows, notes = ds.walk(m["data"])
    blk = [r for r in rows if r[2] == "block A"]
    if len(blk) != 1: return None
    off = blk[0][0]
    d = m["data"]
    vals = [struct.unpack_from("<I", d, off + k * STRIDE + OFF)[0] for k in range(NBLK)]
    evals = [struct.unpack_from("<I", d, off + k * STRIDE + ENERGY_OFF)[0] for k in range(NBLK)]
    sha = hashlib.sha256(d).hexdigest()[:16]
    return {"off": off, "vals": vals, "energy": evals, "sha": sha, "size": len(d),
            "year": m["year"], "round": struct.unpack_from("<I", d, 0x50)[0]}

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
    seeds = addr_seeds()
    regwr, regrd = [], []
    for sa, reg, stag in seeds:
        for b, w, width, src in forward_stores(sa, reg):
            (regwr if w else regrd).append((sa, reg, b, width, src, stag[0]))
    print("T3 addr-seeds=%d register-addr writers=%d readers=%d" % (
        len(seeds), len(regwr), len(regrd)))
    for sa, reg, b, width, src, st in regwr + regrd:
        print("  seed %s (%s, %s) -> %s %s w=%s src=%s owner=%s" % (
            hex(sa), reg, st, "W" if (sa, reg, b, width, src, st) in regwr else "R",
            hex(b), width, src, owner(b)))
    ts = turnfn_stores()
    print("T4 turnfn stores=%d (M325 cross-check: expect 16, 0 block-region)" % len(ts))
    dump_window(0x520ac0, 0x520b70, "settle")
    dump_window(0x41a500, 0x41a590, "addleg")
    strs = scan_strings(["DEBT", "LOAN", "ARREAR", "OWE", "CREDIT"])
    print("T7 noun candidates (%d):" % len(strs))
    for va, s in strs:
        print("  %s %r refs=%s" % (hex(va), s, [(hex(a), mn) for a, mn, _ in push_refs(va)]))
    print("T7b EDITOR cluster [68c800,68cb00):")
    for va, s in scan_strings([], 0x68c800, 0x68cb00):
        print("  %s %r" % (hex(va), s))
    sv = save_values()
    print("T8 save: %s" % sv)
    print("== M326 SKELETON (gates pending measurement) ==")
    return 0

if __name__ == "__main__":
    sys.exit(main())