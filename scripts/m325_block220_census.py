#!/usr/bin/env python3
# M325: block+0x220 WRITER CENSUS (M324's carried OPEN). QUESTION: does FUN_0051f320's
# turn advance set the per-faction field at block+0x220 (blocks 0x94d430+k*0x20bc),
# and who else writes it? ANSWER measured here: the field is the per-faction ENERGY
# balance - pinned by the "EDITORENERGY" cheat handler writing exactly this field.
# STATIC, zero box. Footing: NAMED ## M324 (raw carry, feed), ## M323 (round/year
# writers), ## M320 (block layout), ## M316 (stride/base).
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers; digest
# hashes the MEASURED detail; declared sets MEASURED not authored.
# Mutants: M325_PATCH addr|mn ops (disassembly rewrite), M325_PE_PATCH addr|hex
# (PE byte rewrite), M325_ALGO 1=provenance off 2=disp-match widened 3=forward-scan
# off 4=shl-blind affine 5=feed-direction flipped, M325_SAVE=<file>,
# M325_EVIDENCE_ROOT=<dir>.
# Resolver limits (DECLARED): base provenance = LINEAR backward def-walk within the
# owning function (<=300 instrs, depth<=4), affine over an opaque runtime leaf;
# stack-slot forwarding is linear (most recent store to the same [ebp+disp] wins);
# register-address forward scan stops at the base's next redefinition (calls clobber
# only eax/ecx/edx). Pointer-from-memory bases that are not stack slots stay UNPROVEN
# and are counted. No CFG dataflow proof.
import bisect, csv, hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
PE = os.path.join(ROOT, "programs/terran.exe")
EV = os.environ.get("M325_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M325_ALGO", "0")
SAVE = os.environ.get("M325_SAVE", os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import decode_save as ds

BLKBASE, STRIDE, NBLK, OFF = 0x94d430, 0x20bc, 8, 0x220
FADDRS = [BLKBASE + OFF + k * STRIDE for k in range(NBLK)]
BLKBASES = [BLKBASE + k * STRIDE for k in range(NBLK)]
BLKEND = BLKBASE + NBLK * STRIDE
TURNFN, FEEDFN = 0x51f320, 0x442320
G999, ROUND, YEAR, YEARBASE = 0x999fa4, 0x985afc, 0x985b00, 0x92bf68
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
    p = os.environ.get("M325_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M325_PATCH address not in .text cache: %s" % addr)
            if ins[a] == (mn, ops.strip()):
                raise SystemExit("M325_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M325_PATCH applied to nothing")
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
    if disp == OFF: return "DISP220"
    if disp == FADDRS[0]: return "DISP94D650"
    if disp in FADDRS: return "ABSBRK%d" % FADDRS.index(disp)
    if disp is not None and any(disp in (f + 1, f + 2, f + 3) for f in FADDRS):
        return "SUB"
    return None

# ---- affine backward evaluator ----
# value = ('const', v) | ('lin', m, c, leaf) meaning m*leaf + c
# leaf  = ('reg', name, addr) opaque runtime value | ('ptr', memexpr) | ('arg', name)
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
    """Most recent store to [ebp+disp] before a, linear within the function.
    DECLARED limit: calls are crossed (a callee holding a pointer to the slot
    could rewrite it); every crossing is recorded in STACK_CALL_CROSSINGS and
    printed, so call-dependent provenance is enumerated, not hidden."""
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
        # a write to ebp itself invalidates the frame walk
        if reg_of(parts[0]) == "ebp" and mn not in ("cmp", "test", "push"):
            return None
    return None

def pop_source(a, reg, budget):
    """LIFO-sound push matching for a pop reg: walk backward with a slot balance.
    The matching push is the one that created the slot this pop consumes - it may
    be a push of a DIFFERENT register (push eax; push ebx; pop eax takes ebx's
    value). Returns (push_addr, pushed_reg) or None."""
    o = owner(a)
    i = AIDX[a]
    balance = 1  # our pop consumes one slot
    if ALGO == "6":
        # mutant: the OLD unsound pairing (most recent push of the SAME reg)
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
    trace = os.environ.get("M325_TRACE") in ("%x:%s" % (a, reg), "all")
    if budget is None: budget = [1500]
    if depth > 4 or budget[0] <= 0: return ("lin", 1, 0, ("arg", reg))
    o = owner(a)
    i = AIDX[a]
    while i > 0 and budget[0] > 0:
        i -= 1; budget[0] -= 1
        b = ADDRS[i]
        if owner(b) != o:
            if trace: print("TRACE %x:%s EDGE at %x" % (a, reg, b))
            return ("lin", 1, 0, ("arg", reg))
        mn, ops = INS[b]
        parts = split_ops(ops)
        if not parts:
            # implicit writers: leave/cdq/string ops conservatively opaque
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
                if trace: print("TRACE %x:%s CLOBBER at %x" % (a, reg, b))
                return ("lin", 1, 0, ("arg", reg))
            continue
        if mn in ("push", "cmp", "test", "bt", "nop", "ret") or mn.startswith("j"):
            continue  # read-only: never a register definition
        dest = reg_of(parts[0])
        if dest != reg: continue
        if trace: print("TRACE %x:%s def at %x: %s %s (depth=%d)" % (a, reg, b, mn, ops, depth))
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
    """Classify a disp-form hit's effective address = m*leaf + c.
    Field family <=> m == STRIDE and c in FADDRS (runtime faction index),
    or a constant in FADDRS. The disp is PART OF c (no double count)."""
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

# ---- register-address forward scan ----
def addr_seeds():
    """Sites computing a field address into a register: lea reg,[...+0x94d650]
    (any base provenance - tagged, not filtered) or mov reg, imm in FADDRS."""
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
    """Loads/stores through [reg+0] after seed_a until reg is redefined (linear)."""
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
            break  # implicit index advance: address no longer pinned
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

def pe_bytes(addr, n):
    pe = open(PE, "rb").read()
    p = os.environ.get("M325_PE_PATCH")
    if p:
        pe = bytearray(pe)
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            a, hx = chunk.split("|", 1)
            a = int(a, 16)
            off = a - IMG_BASE  # .data/.rdata identity-mapped sections (va==raw)
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

def callers_of(target):
    out = []
    for a in ADDRS:
        mn, ops = INS[a]
        if mn == "call":
            m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            if m and int(m.group(1), 16) == target:
                out.append(a)
    return out

def feed_direction():
    """MIN/MAX DERIVED from measured bytes, not hardcoded:
    (1) edx <- g999fa4 @44261f; (2) cmp edx,[field] @442625; (3) jcc @44262b must
    SKIP OVER the store @442642 (jcc_addr < store_addr < jump target); (4) the store
    writes g999fa4 <- edx, and edx was reloaded FROM THE FIELD @44263c.
    jle skips when edx <= field, so the store runs when field < edx: the global
    takes the SMALLER value => MIN. Any geometry break => SHAPE-CHANGED."""
    l = INS.get(0x44261f)
    c = INS.get(0x442625)
    j = INS.get(0x44262b)
    r2 = INS.get(0x44263c)
    s = INS.get(0x442642)
    shape = (l, c, j, r2, s)
    if not (l and c and j and r2 and s):
        return ("SHAPE-CHANGED", shape)
    ok = (l == ("mov", "edx,DWORD PTR ds:0x999fa4")
          and c[0] == "cmp" and c[1].startswith("edx,") and "0x94d650" in c[1]
          and j[0] in ("jle", "jg", "jl", "jge")
          and r2 == ("mov", "edx,DWORD PTR [ecx+0x94d650]")
          and s == ("mov", "DWORD PTR ds:0x999fa4,edx"))
    if not ok:
        return ("SHAPE-CHANGED", shape)
    tgt = int(j[1], 16)
    if not (0x44262b < 0x442642 < tgt):
        return ("SHAPE-CHANGED", shape)  # jcc no longer skips over the store
    # store executes when the jcc condition is FALSE
    cond = j[0]
    if cond == "jle":    # skip when edx <= field -> store when field < edx -> MIN
        d = "MIN"
    elif cond == "jg":   # skip when edx > field -> store when field >= edx -> MAX
        d = "MAX"
    elif cond == "jl":
        d = "MAX"
    else:                # jge: skip when edx >= field -> store when field < edx
        d = "MIN"
    if ALGO == "5":
        d = "MAX" if d == "MIN" else "MIN"
    return (d, shape)

def save_values():
    m = ds.parse(SAVE)
    rows, notes = ds.walk(m["data"])
    blk = [r for r in rows if r[2] == "block A"]
    if len(blk) != 1: return None
    off = blk[0][0]
    d = m["data"]
    vals = [struct.unpack_from("<I", d, off + k * STRIDE + OFF)[0] for k in range(NBLK)]
    sha = hashlib.sha256(d).hexdigest()[:16]
    return {"off": off, "vals": vals, "sha": sha, "size": len(d), "notes": notes,
            "year": m["year"], "round": struct.unpack_from("<I", d, 0x50)[0]}

def main():
    print("== M325: block+0x220 writer census (STATIC) ==")
    print("T0 field=%s stride=%s nblk=%d turnfn=%s size=%s" % (
        ",".join(hex(x) for x in FADDRS), hex(STRIDE), NBLK, hex(TURNFN), hex(FSIZE[TURNFN])))
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
    tso = turnfn_stringops()
    blkstores = []
    for a, width, mi, src in ts:
        kind, ab, disp, base, index, scale, _ = mi
        if kind == "abs":
            if ab is not None and BLKBASE <= ab < BLKEND: blkstores.append(a)
        elif disp is not None:
            # conservative: any field-family disp counts, proven or not (the
            # turnfn is small and its full inventory is printed above)
            if disp in FADDRS or disp == OFF:
                blkstores.append(a)
            else:
                tag, det = base_tag(a, mi)
                if tag in ("BLKCONST", "STRIDE") or (
                        isinstance(det, int) and BLKBASE <= det < BLKEND):
                    blkstores.append(a)
    print("T4 turnfn stores=%d stringops=%d block-region stores=%d" % (
        len(ts), len(tso), len(blkstores)))
    for a, width, mi, src in ts:
        kind, ab, disp, base, index, scale, _ = mi
        print("  %s w=%s %s disp=%s base=%s src=%s" % (
            hex(a), width, kind, hex(disp) if disp is not None else (ab and hex(ab)),
            base, src))
    strs = {hex(a): pe_cstr(a) for a in (0x68c938, 0x68c948, 0x672e38)}
    print("T5 strings: %s" % strs)
    fd, fdshape = feed_direction()
    print("T6 feed direction=%s shape=%s" % (fd, fdshape))
    calE = callers_of(0x4e0260)
    calY = callers_of(0x4e0350)
    print("T7 callers 4e0260=%s 4e0350=%s owners=%s" % (
        [hex(a) for a in calE], [hex(a) for a in calY],
        sorted(set(owner(a) for a in calE + calY))))
    sv = save_values()
    print("T8 save: %s" % sv)
    cross_sites = sorted(set(s for s, _, _ in STACK_CALL_CROSSINGS if s is not None))
    prov_cross = sorted(set(x["a"] for x in writers
                            if x["prov"] in ("STRIDE", "BLKCONST")
                            and x["a"] in cross_sites))
    print("T9 stack-forward call-crossings (DECLARED linear limit): events=%d sites=%d proven-writer-sites-crossing=%s" % (
        len(STACK_CALL_CROSSINGS), len(cross_sites),
        ",".join(hex(a) for a in prov_cross)))
    # ---- gates ----
    G = []
    def gate(name, ok, detail):
        G.append(ok)
        print("%s %s %s" % (name, "PASS" if ok else "FAIL", detail))
    n_abs = sum(1 for x in rows if x["tag"].startswith("ABS") and x["mi"][0] == "abs")
    n_220 = sum(1 for x in rows if x["tag"] == "DISP220")
    n_sub = sum(1 for x in rows if x["tag"] == "SUB")
    n_dw = sum(1 for x in rows if x["width"] == 4)
    gate("G1", len(hits) == 234 and len(writers) == 54 and len(readers) == 180
         and n_abs == 0 and n_220 == 0 and n_sub == 0 and n_dw == len(rows),
         "hits=%d writers=%d readers=%d abs=%d disp220=%d sub=%d dw=%d/%d" % (
             len(hits), len(writers), len(readers), n_abs, n_220, n_sub, n_dw, len(rows)))
    wrsites = sorted(x["a"] for x in writers)
    exp_unprov = [0x4d29f3, 0x4e21fc, 0x4f5c8c, 0x506d2b, 0x5085c0, 0x5086e2,
                  0x50878c, 0x5087be, 0x51ae62, 0x536c45, 0x536c52, 0x53800f,
                  0x53801c, 0x53b794, 0x53b7a1, 0x53c65a, 0x53de13, 0x53de20,
                  0x53eab3, 0x540d20, 0x544410, 0x54441d, 0x547af3, 0x567080,
                  0x5a0144]
    exp_wrsites = [
        0x41a55d, 0x4295fe, 0x429628, 0x4d29f3, 0x4d2f71, 0x4e21fc, 0x4eec75,
        0x4f4952, 0x4f497f, 0x4f4999, 0x4f4a0b, 0x4f5c8c, 0x506d2b, 0x5085c0,
        0x5086e2, 0x50878c, 0x5087be, 0x51adf3, 0x51ae62, 0x520605, 0x520743,
        0x520770, 0x5207d9, 0x5207ff, 0x520a09, 0x520b1c, 0x520b30, 0x536c45,
        0x536c52, 0x53778b, 0x537798, 0x53800f, 0x53801c, 0x53b794, 0x53b7a1,
        0x53c64d, 0x53c65a, 0x53de13, 0x53de20, 0x53eaa9, 0x53eab3, 0x540d20,
        0x544410, 0x54441d, 0x546150, 0x547af3, 0x567080, 0x5936d3, 0x593f11,
        0x59d0d8, 0x59eef3, 0x59f0b9, 0x5a0144, 0x5a28fa]
    gate("G2", sorted(x["a"] for x in wr_unprov) == exp_unprov
         and wrsites == exp_wrsites
         and len(wowners) == 27 and len(writers) - len(wr_unprov) == 29,
         "wr_unproven=%d (pinned list) proven=%d owners=%d sites-pinned=%d" % (
             len(wr_unprov), len(writers) - len(wr_unprov), len(wowners),
             len(exp_wrsites)))
    exp_regwr = [
        (0x40dd01, "eax", 0x40dd0a, 4, "ecx", "STRIDE"),
        (0x40dd60, "eax", 0x40dd70, 4, "ecx", "BLKCONST"),
        (0x4d560a, "eax", 0x4d561a, 4, "edx", "STRIDE"),
        (0x4d58ff, "eax", 0x4d5908, 4, "esi", "STRIDE"),
        (0x4d59ea, "eax", 0x4d59f3, 4, "esi", "STRIDE"),
        (0x4e0311, "esi", 0x4e0336, 4, "eax", "STRIDE"),
        (0x51be55, "eax", 0x51be66, 4, "ecx", "UNPROVEN"),
        (0x520589, "ebx", 0x5205ed, 4, "edx", "BLKCONST"),
        (0x52e677, "eax", 0x52e687, 4, "ecx", "STRIDE"),
        (0x52e6a6, "eax", 0x52e6b6, 4, "edx", "STRIDE"),
        (0x53094f, "eax", 0x53095f, 4, "edx", "STRIDE"),
        (0x53097a, "eax", 0x53098a, 4, "ecx", "STRIDE"),
        (0x53753b, "eax", 0x537544, 4, "edx", "STRIDE"),
        (0x537c70, "eax", 0x537c80, 4, "edx", "STRIDE"),
        (0x540d07, "eax", 0x540d17, 4, "ecx", "STRIDE"),
        (0x546171, "eax", 0x546181, 4, "edx", "STRIDE"),
        (0x547b13, "eax", 0x547b1c, 4, "ecx", "UNPROVEN"),
        (0x56e86d, "eax", 0x56e87d, 4, "edx", "UNPROVEN"),
        (0x592d68, "eax", 0x592d78, 4, "edx", "UNPROVEN"),
        (0x593f26, "eax", 0x593f36, 4, "edx", "STRIDE")]
    allwr_owners = sorted(set(wowners) | set(owner(b) for _, _, b, _, _, _ in regwr))
    nprov_reg = sum(1 for t in regwr if t[5] in ("STRIDE", "BLKCONST"))
    nunprov_reg = len(regwr) - nprov_reg
    prov_tot = (len(writers) - len(wr_unprov)) + nprov_reg
    unprov_tot = len(wr_unprov) + nunprov_reg
    blkconst_seeds = sorted((sa, det) for sa, _, (tag, det) in seeds
                            if tag == "BLKCONST")
    gate("G3", sorted(regwr) == sorted(exp_regwr) and len(regrd) == 7
         and len(seeds) == 30
         and len(writers) + len(regwr) == 74 and len(allwr_owners) == 34
         and nprov_reg == 16 and nunprov_reg == 4
         and prov_tot == 45 and unprov_tot == 29
         and blkconst_seeds == [(0x40dd60, 0x94f70c), (0x4e02ae, 0x94f70c),
                                (0x520589, 0x94f70c), (0x523b57, 0x94f70c)],
         "regwr=%d (pinned) regrd=%d seeds=%d sites=%d owners=%d P=%d U=%d blkconst=%s" % (
             len(regwr), len(regrd), len(seeds), len(writers) + len(regwr),
             len(allwr_owners), prov_tot, unprov_tot,
             [(hex(a), hex(d)) for a, d in blkconst_seeds]))
    round_site = INS.get(0x51f53c)
    year_site = INS.get(0x51f54f)
    exp_ts_sites = [0x51f324, 0x51f433, 0x51f4bf, 0x51f526, 0x51f53c, 0x51f54f,
                    0x51f57e, 0x51f58e, 0x51f5a3, 0x51f5bf, 0x51f5c4, 0x51f68f,
                    0x51f696, 0x51f6b5, 0x51f6ca, 0x51f6ec]
    gate("G4", len(ts) == 16 and len(tso) == 0 and len(blkstores) == 0
         and sorted(a for a, _, _, _ in ts) == exp_ts_sites
         and round_site == ("mov", "ds:0x985afc,eax")
         and year_site == ("mov", "ds:0x985b00,eax"),
         "stores=%d stringops=%d blkstores=%d sites-pinned=%d round=%s year=%s" % (
             len(ts), len(tso), len(blkstores), len(exp_ts_sites), round_site, year_site))
    caps = {"cap9999999": INS.get(0x5087ae), "cap999999999": INS.get(0x5a28e9),
            "cap99999": INS.get(0x56706b), "minus1000": INS.get(0x5085c0),
            "reset0": INS.get(0x59eef3), "reset0src": INS.get(0x59ee73),
            "editorE_push": INS.get(0x4e0319), "editorY_push": INS.get(0x4e0366),
            "votefor_me_push": INS.get(0x4295c4)}
    ed = {"owner_push": owner(0x4e0319), "owner_store": owner(0x4e0336),
          "gate_call": INS.get(0x4e031e), "gate_jne": INS.get(0x4e032a),
          "src_load": INS.get(0x4e032c)}
    gate("G5", strs == {"0x68c938": b"EDITORENERGY", "0x68c948": b"EDITORYEAR",
                        "0x672e38": b"VOTEFORME"}
         and caps["cap9999999"] == ("cmp", "eax,0x98967f")
         and caps["cap999999999"] == ("cmp", "ecx,0x3b9ac9ff")
         and caps["cap99999"] == ("push", "0x1869f")
         and caps["minus1000"] == ("add", "DWORD PTR [eax+0x94d650],0xfffffc18")
         and caps["reset0"] == ("mov", "DWORD PTR [esi+0x94d650],ebx")
         and caps["reset0src"] == ("xor", "ebx,ebx")
         and caps["editorE_push"] == ("push", "0x68c938")
         and caps["editorY_push"] == ("push", "0x68c948")
         and caps["votefor_me_push"] == ("push", "0x672e38")
         and ed["owner_push"] == ed["owner_store"] == "FUN_004e0260"
         and ed["gate_call"] == ("call", "0x626ec4")
         and ed["gate_jne"] == ("jne", "0x4e0349")
         and ed["src_load"] == ("mov", "eax,ds:0x999fa4")
         and 0x4e0311 < 0x4e031e < 0x4e0336,
         "strings=%s caps=%s editor-handler=%s" % (strs, caps, ed))
    chain = {"parse_call": INS.get(0x626f67), "parse_je": INS.get(0x626f6e),
             "staging_push": INS.get(0x626fca), "thunk_call": INS.get(0x626fcf),
             "g999_store": INS.get(0x626fd7),
             "feed_read2": INS.get(0x44263c),
             "itoa_base": INS.get(0x626f26), "itoa_call": INS.get(0x626f30),
             "year_sub": INS.get(0x4e0382), "year_cmp": INS.get(0x4e0384),
             "year_store": INS.get(0x4e0387), "year_floor": INS.get(0x4e038e)}
    gate("G6", fd == "MIN"
         and chain["parse_call"] == ("call", "0x5f0583")
         and chain["parse_je"] == ("je", "0x626f75")
         and chain["staging_push"] == ("push", "0x99a01c")
         and chain["thunk_call"] == ("call", "0x64c460")
         and chain["g999_store"] == ("mov", "ds:0x999fa4,eax")
         and chain["feed_read2"] == ("mov", "edx,DWORD PTR [ecx+0x94d650]")
         and chain["itoa_base"] == ("push", "0xa")
         and chain["itoa_call"] == ("call", "0x64f980")
         and chain["year_sub"] == ("sub", "eax,edx")
         and chain["year_cmp"] == ("cmp", "eax,0x1")
         and chain["year_store"] == ("mov", "ds:0x985afc,eax")
         and chain["year_floor"] == ("mov", "DWORD PTR ds:0x985afc,0x1")
         and sorted(calE) == [0x514ebf, 0x517e2c]
         and sorted(calY) == [0x514ecf, 0x517e3a]
         and sorted(set(owner(a) for a in calE + calY)) == ["FUN_00512b40", "FUN_00516b80"],
         "feed=%s chain=%s callersE=%s callersY=%s" % (
             fd, chain, [hex(a) for a in calE], [hex(a) for a in calY]))
    gate("G7", sv is not None and sv["off"] == 0x32c
         and sv["vals"] == [10, 28, 112, 69, 229, 60, 102, 37]
         and sv["sha"] == "74d0f44ab9b9290b" and sv["size"] == 242539
         and sv["year"] == 2150 and sv["round"] == 50
         and all(v < 2100 for v in sv["vals"]),
         "save=%s" % sv)
    r1 = len(blkstores) > 0
    r2 = sv is not None and all(v == sv["year"] for v in sv["vals"])
    r3 = fd == "MAX"
    gate("G8", (not r1) and (not r2) and (not r3),
         "R1 turn-sets-field=%s R2 year-copy=%s R3 MAX-feed=%s (all must be False)" % (
             r1, r2, r3))
    # digest over measured detail
    d = hashlib.sha256()
    for x in rows:
        d.update(repr((x["a"], x["w"], x["r"], x["width"], x["tag"], x["prov"],
                       str(x["det"]), x["src"], x["owner"])).encode())
    for x in regwr: d.update(repr(x).encode())
    for x in regrd: d.update(repr(x).encode())
    for x in ts: d.update(repr((x[0], x[1], str(x[2]), x[3])).encode())
    d.update(repr((len(tso), sorted(blkstores))).encode())
    d.update(repr((strs, fd, str(fdshape), sorted(calE), sorted(calY))).encode())
    d.update(repr(sv).encode())
    d.update(repr(caps).encode())
    d.update(repr(ed).encode())
    d.update(repr(chain).encode())
    d.update(repr(blkconst_seeds).encode())
    d.update(repr((len(STACK_CALL_CROSSINGS), cross_sites, prov_cross)).encode())
    print("DIGEST %s" % d.hexdigest()[:16])
    print("== M325: %d/%d ==" % (sum(G), len(G)))
    return 0 if all(G) else 1

if __name__ == "__main__":
    sys.exit(main())