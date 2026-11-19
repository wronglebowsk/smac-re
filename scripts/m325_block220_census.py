#!/usr/bin/env python3
# M325: block+0x220 WRITER CENSUS (M324's carried OPEN). The per-faction field at
# block+0x220 (blocks 0x94d430+k*0x20bc, k=0..7) is RAW-carryied by the save loader
# (M324 G3) and feeds ROUND=max(1, g999fa4-2100) via the MAX-feed FUN_00442320
# (M324 G4). QUESTION: does FUN_0051f320's turn advance (M323's round+1/year writer,
# 0x40c B) set this field, and who else writes it? Name the semantics from the
# writer census + the carry law; if the bytes don't support a game noun, leave lead.
# STATIC, zero box. Footing: NAMED ## M324/M323/M320/M316.
# Law: table FIRST then ASSERT; >=1 RIVAL that FAILS on the printed numbers; digest
# hashes the MEASURED detail; declared sets MEASURED not authored.
# Mutants: M325_PATCH addr|mn ops (disassembly rewrite), M325_ALGO 1=provenance off
# 2=disp-match widened to any displacement, M325_SAVE=<file>, M325_EVIDENCE_ROOT.
# Resolver limit (DECLARED): base-register provenance is a LINEAR backward def-walk
# within the owning function (<=60 instrs, depth<=3), not a CFG dataflow proof;
# unresolved bases are reported UNPROVEN and counted, never silently dropped.
import bisect, csv, hashlib, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
EV = os.environ.get("M325_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M325_ALGO", "0")
SAVE = os.environ.get("M325_SAVE", os.path.join(ROOT, "programs/saves/m54b_clean.SAV"))

BLKBASE, STRIDE, NBLK, OFF = 0x94d430, 0x20bc, 8, 0x220
FADDRS = [BLKBASE + OFF + k * STRIDE for k in range(NBLK)]  # 0x94d650 + k*20bc
BLKBASES = [BLKBASE + k * STRIDE for k in range(NBLK)]
BLKEND = BLKBASE + NBLK * STRIDE            # 0x95da10 == base_array base (M321)
TURNFN = 0x51f320                            # FUN_0051f320, M323 round+1 @entry, year @51f54f
FEEDFN = 0x442320                            # FUN_00442320, M324 MAX-feed reader
G999, ROUND, YEARBASE = 0x999fa4, 0x985afc, 0x92bf68
CODEC = 0x596850
RD, WR = 0x64cc00, 0x64c9a0

STORE_MN = {"mov", "xchg", "add", "adc", "sub", "sbb", "inc", "dec", "or", "and",
            "xor", "not", "neg", "movnti", "pop"}
RMW1 = {"inc", "dec", "not", "neg"}
REGW = {"eax": 4, "ebx": 4, "ecx": 4, "edx": 4, "esi": 4, "edi": 4, "ebp": 4, "esp": 4,
        "ax": 2, "bx": 2, "cx": 2, "dx": 2, "si": 2, "di": 2, "bp": 2, "sp": 2,
        "al": 1, "bl": 1, "cl": 1, "dl": 1, "ah": 1, "bh": 1, "ch": 1, "dh": 1}
CALLER_SAVED = {"eax", "ecx", "edx"}

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

def fstart(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    return funcs[i][0] if i >= 0 else None

def split_ops(ops):
    # Intel syntax: no commas inside [...] in this objdump cache
    return [o.strip() for o in ops.split(",")] if ops.strip() else []

def memref(op):
    """Return (kind, absaddr, disp, base, index, scale, width) for a memory operand.
    kind: 'abs' (ds:imm), 'brk' ([...]); None if not memory."""
    m = re.search(r"(BYTE|WORD|DWORD|QWORD) PTR ", op)
    width = {"BYTE": 1, "WORD": 2, "DWORD": 4, "QWORD": 8}[m.group(1)] if m else None
    m = re.search(r"ds:0x([0-9a-f]+)", op)
    if m and "[" not in op:
        return ("abs", int(m.group(1), 16), None, None, None, None, width)
    m = re.search(r"\[([^\]]+)\]", op)
    if not m:
        return None
    body = m.group(1)
    disp, base, index, scale = 0, None, None, 1
    for term in re.findall(r"[+-]?[^+-]+", body):
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
            return ("brk", None, None, None, None, None, width)  # unparsed
    if neg and base is None and index is None:
        pass
    return ("brk", None, disp, base, index, scale, width)

def reg_of(op):
    t = op.strip()
    return t if t in REGW else None

def classify(a):
    """(is_write, is_read, width, meminfo, src_reg_or_imm) for instruction at a."""
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
    if mn not in STORE_MN and mn not in ("cmp", "test", "movzx", "movsx", "lea", "push",
                                          "imul", "bt", "bts", "btr", "btc", "cmpxchg",
                                          "xadd", "fld", "fst", "fstp", "fild", "fistp"):
        # any other mnemonic with a memory first operand that is not a known load:
        mi0 = memref(parts[0])
        if mi0 and mn not in ("jmp", "call", "jcc"):
            return (True, True, mi0[6] or 4, mi0, None)  # conservative RMW
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
    if mn in ("movzx", "movsx", "imul", "lea"):
        # dest is parts[0] (register); sources may hold memory
        if mn == "lea":
            mi = memref(parts[1]) if len(parts) > 1 else None
            return (False, False, None, mi, None)  # lea reads nothing; keep for fold walks
        for p in parts[1:]:
            mi = memref(p)
            if mi: return (False, True, mi[6] or REGW.get(parts[0], 4), mi, None)
        return (False, False, None, None, None)
    if mn in ("fst", "fstp", "fistp"):
        mi = memref(parts[0])
        if mi: return (True, False, mi[6] or 4, mi, "fpu")
        return (False, False, None, None, None)
    # mov / add / sub / or / and / xor / adc / sbb / cmpxchg / xadd / bts...
    mi = memref(parts[0])
    if mi:
        src = parts[1] if len(parts) > 1 else None
        w = mi[6] or (REGW.get(src, 4) if src else 4)
        rd = mn in ("add", "adc", "sub", "sbb", "or", "and", "xor", "cmpxchg", "xadd",
                    "bts", "btr", "btc")
        return (True, rd, w, mi, src)
    # load form: memory in a later operand
    for p in parts[1:]:
        mi = memref(p)
        if mi: return (False, True, mi[6] or REGW.get(parts[0], 4), mi, None)
    return (False, False, None, None, None)

def field_hit(mi):
    """Does this memory ref touch block+0x220? Returns tag or None."""
    if mi is None: return None
    kind, ab, disp, base, index, scale, width = mi
    if kind == "abs":
        if ab in FADDRS: return "ABS%d" % FADDRS.index(ab)
        return None
    if ALGO == "2":
        return "DISP_ANY" if disp is not None else None
    if disp == OFF: return "DISP220"
    if disp == FADDRS[0]: return "DISP94D650"
    if disp in FADDRS: return "ABSBRK%d" % FADDRS.index(disp)
    return None

# ---- base provenance: linear backward def-walk (DECLARED limit) ----
def resolves_to(a, reg, depth=0, budget=None):
    """Symbolic value of reg just BEFORE instruction at a. Returns (kind, val, chain).
    kind: IMM (val=const), BLK (val=block base const), STRIDE (val=('stride',src)),
    PTR (val=source mem expr), ZERO, ARG, CLOBBER, UNKNOWN, FOLD."""
    if budget is None: budget = [60]
    if depth > 3 or budget[0] <= 0: return ("UNKNOWN", None, [])
    o = owner(a)
    i = AIDX[a]
    chain = []
    while i > 0 and budget[0] > 0:
        i -= 1; budget[0] -= 1
        b = ADDRS[i]
        if owner(b) != o:
            return ("EDGE", None, chain)
        mn, ops = INS[b]
        parts = split_ops(ops)
        if not parts: continue
        dest = reg_of(parts[0])
        if mn == "call":
            if reg in CALLER_SAVED:
                return ("CLOBBER", None, chain + [hex(b)])
            continue
        if mn in ("ret", "leave") and depth == 0:
            return ("EDGE", None, chain)
        if dest != reg:
            continue
        chain.append("%s:%s %s" % (hex(b), mn, ops))
        if mn == "mov":
            src = parts[1] if len(parts) > 1 else ""
            r = reg_of(src)
            if r:
                k, v, c2 = resolves_to(b, r, depth + 1, budget)
                return (k, v, chain + c2)
            m = re.fullmatch(r"0x([0-9a-f]+)", src.strip())
            if m:
                v = int(m.group(1), 16)
                return ("BLK" if v in BLKBASES else "IMM", v, chain)
            mi = memref(src)
            if mi:
                if mi[0] == "abs":
                    return ("PTR", ("abs", mi[1]), chain)
                return ("PTR", ("brk", mi[2], mi[3], mi[4], mi[5]), chain)
            return ("UNKNOWN", None, chain)
        if mn == "lea":
            mi = memref(parts[1]) if len(parts) > 1 else None
            if mi and mi[0] == "brk":
                # fold: resolve base/index at b, add disp
                bv, iv = 0, 0
                ok = True
                if mi[3]:
                    k, v, c2 = resolves_to(b, mi[3], depth + 1, budget)
                    chain += c2
                    if k in ("IMM", "BLK") and isinstance(v, int): bv = v
                    else: ok = False
                if mi[4]:
                    k, v, c2 = resolves_to(b, mi[4], depth + 1, budget)
                    chain += c2
                    if k in ("IMM", "BLK") and isinstance(v, int): iv = v * mi[5]
                    else: ok = False
                if ok:
                    v = bv + iv + (mi[2] or 0)
                    return ("BLK" if v in BLKBASES else "IMM", v, chain)
                return ("FOLD", (mi[2], mi[3], mi[4], mi[5]), chain)
            return ("UNKNOWN", None, chain)
        if mn == "imul":
            if len(parts) == 3:
                m = re.fullmatch(r"0x([0-9a-f]+)", parts[2].strip())
                r = reg_of(parts[1])
                if m and r:
                    imm = int(m.group(1), 16)
                    k, v, c2 = resolves_to(b, r, depth + 1, budget)
                    chain += c2
                    if imm == STRIDE:
                        return ("STRIDE", (k, v), chain)
                    if k in ("IMM", "BLK") and isinstance(v, int):
                        vv = v * imm
                        return ("BLK" if vv in BLKBASES else "IMM", vv, chain)
                    return ("UNKNOWN", None, chain)
            if len(parts) == 2:
                m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
                if m:
                    imm = int(m.group(1), 16)
                    k, v, c2 = resolves_to(b, reg, depth + 1, budget)
                    chain += c2
                    if imm == STRIDE:
                        return ("STRIDE", (k, v), chain)
            return ("UNKNOWN", None, chain)
        if mn == "xor" and len(parts) == 2 and parts[0] == parts[1]:
            return ("ZERO", 0, chain)
        if mn == "pop":
            return ("UNKNOWN", None, chain)
        if mn in ("add", "sub") and len(parts) == 2:
            m = re.fullmatch(r"0x([0-9a-f]+)", parts[1].strip())
            if m:
                imm = int(m.group(1), 16)
                k, v, c2 = resolves_to(b, reg, depth + 1, budget)
                chain += c2
                if k in ("IMM", "BLK") and isinstance(v, int):
                    vv = v + imm if mn == "add" else v - imm
                    return ("BLK" if vv in BLKBASES else "IMM", vv, chain)
                if k == "STRIDE":
                    return ("STRIDE", (mn, imm, v), chain)
            return ("UNKNOWN", None, chain)
        return ("UNKNOWN", None, chain)
    return ("EDGE", None, chain)

def provenance(a, mi):
    """Classify the base of a disp-form field hit. Returns (tag, detail, chain)."""
    if ALGO == "1":
        return ("OFF", None, [])
    kind, ab, disp, base, index, scale, width = mi
    if disp == OFF:
        # need base (+index*stride) == some block base
        if base is None and index is None:
            return ("NOBASE", None, [])
        k, v, chain = resolves_to(a, base, 0, [60]) if base else ("IMM", 0, [])
        if index:
            ki, vi, ci = resolves_to(a, index, 0, [60])
            chain += ci
            if ki == "IMM" and isinstance(vi, int) and scale == STRIDE:
                if k in ("IMM", "BLK") and isinstance(v, int):
                    tot = v + vi * scale
                    return ("BLKIDX", tot, chain) if tot in BLKBASES else ("OUT", tot, chain)
            return ("UNPROVEN", (k, v, ki, vi), chain)
        if k == "BLK": return ("BLK", v, chain)
        if k == "IMM" and isinstance(v, int):
            return ("BLK", v, chain) if v in BLKBASES else ("OUT", v, chain)
        if k == "STRIDE":
            return ("STRIDE220", v, chain)  # base=idx*stride, disp 220: needs +94d430 elsewhere
        if k == "PTR":
            return ("PTR", v, chain)
        return ("UNPROVEN", (k, v), chain)
    if disp == FADDRS[0]:
        # base (+index) must be blk*stride (k in 0..7)
        if base is None and index is None:
            return ("BLK", BLKBASE, [])  # [0x94d650] alone = block 0
        regs = [r for r in (base, index) if r]
        tot, ok, chain = 0, True, []
        for r in regs:
            sc = scale if r == index and base is not None else 1
            k, v, c2 = resolves_to(a, r, 0, [60])
            chain += c2
            if k in ("IMM", "BLK", "ZERO") and isinstance(v, int):
                tot += v * sc
            elif k == "STRIDE":
                kk, vv = v
                if kk in ("IMM", "BLK", "ZERO") and isinstance(vv, int):
                    tot += vv * STRIDE * sc
                else:
                    ok = False; chain.append("stride-src-unresolved:%s" % kk)
            else:
                ok = False; chain.append("unresolved:%s=%s" % (r, k))
        if ok:
            if tot % STRIDE == 0 and 0 <= tot // STRIDE < NBLK:
                return ("BLKIDX", BLKBASE + tot, chain)
            return ("OUT", tot, chain)
        return ("UNPROVEN", tot, chain)
    return ("OTHER", disp, [])

# ---- census ----
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

def turnfn_stores():
    """Every store inside FUN_0051f320 (the whole 0x40c-B turn advance)."""
    out = []
    lo, hi = TURNFN, TURNFN + FSIZE[TURNFN]
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        w, r, width, mi, src = classify(a)
        if w and mi:
            out.append((a, width, mi, src))
    return out

def save_block_values():
    """Read the 8 block+0x220 dwords from the .SAV via the codec READ-leg sequence.
    File layout: 12-B prefix, then sequential legs (M324 T3: blob@12, round@0x50).
    Walk READ legs in address order from the codec entry, accumulate count*size."""
    data = open(SAVE, "rb").read()
    legs = []
    lo, hi = CODEC, CODEC + FSIZE[CODEC]
    for a in ADDRS:
        if a < lo: continue
        if a >= hi: break
        mn, ops = INS[a]
        if mn == "call":
            m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
            if m and int(m.group(1), 16) == RD:
                legs.append(a)
    # push-arg walk (linear, m324 law): dest,size,count before each RD call
    off = 12
    vals, blkoff, trace = None, None, []
    for a in legs:
        args = []
        i = AIDX[a]
        seen = 0
        while i > 0 and seen < 32 and len(args) < 3:
            i -= 1
            b = ADDRS[i]
            if owner(b) != owner(a): break
            mn, ops = INS[b]
            if mn == "push":
                m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
                args.append(int(m.group(1), 16) if m else None)
                seen += 1
            elif mn == "call":
                m = re.fullmatch(r"0x([0-9a-f]+)", ops.strip())
                t = int(m.group(1), 16) if m else -1
                if t not in (RD, WR, 0x596470, 0x596540): break
                seen += 1
            elif mn == "add" and ops.startswith("esp,"): break
            elif mn in ("lea", "ret", "leave"): break
        while len(args) < 3: args.append(None)
        dest, size, cnt = args
        if dest == BLKBASE and size == NBLK * STRIDE:
            blkoff = off
            vals = [struct.unpack_from("<I", data, off + k * STRIDE + OFF)[0]
                    for k in range(NBLK)]
        if dest is not None and size is not None and cnt is not None:
            off += size * cnt
        trace.append((hex(a), dest and hex(dest), size, cnt, hex(off)))
    return vals, blkoff, trace, len(data)

def main():
    print("== M325: block+0x220 writer census (STATIC) ==")
    print("T0 field addrs: %s stride=%s nblk=%d turnfn=%s size=%s" % (
        ",".join(hex(x) for x in FADDRS), hex(STRIDE), NBLK, hex(TURNFN), hex(FSIZE[TURNFN])))
    hits = census()
    print("T1 census hits: %d" % len(hits))
    rows = []
    for a, w, r, width, tag, mi, src in hits:
        kind, ab, disp, base, index, scale, _ = mi
        if tag.startswith("ABS") and kind == "abs":
            prov, det, chain = ("ABS", ab, [])
        else:
            prov, det, chain = provenance(a, mi)
        rows.append((a, w, r, width, tag, prov, det, src, chain))
        print("  %s %s%s w=%d %s base=%s idx=%s*%s src=%s prov=%s det=%s owner=%s" % (
            hex(a), "W" if w else "-", "R" if r else "-", width or 0, tag,
            base, index, scale, src, prov,
            hex(det) if isinstance(det, int) else det, owner(a)))
    writers = [x for x in rows if x[1]]
    readers = [x for x in rows if x[2] and not x[1]]
    print("T2 writers=%d readers=%d" % (len(writers), len(readers)))
    ts = turnfn_stores()
    print("T3 FUN_0051f320 store inventory: %d stores" % len(ts))
    for a, width, mi, src in ts:
        kind, ab, disp, base, index, scale, _ = mi
        print("  %s w=%d %s disp=%s base=%s idx=%s*%s src=%s" % (
            hex(a), width or 0, kind, hex(disp) if disp is not None else ab and hex(ab),
            base, index, scale, src))
    vals, blkoff, trace, fsz = save_block_values()
    print("T4 save: size=%d blkoff=%s vals=%s" % (
        fsz, blkoff and hex(blkoff), vals))
    print("T4b leg trace (first 12): %s" % trace[:12])
    # digest of the measured detail
    d = hashlib.sha256()
    for x in rows:
        d.update(repr((x[0], x[1], x[2], x[3], x[4], x[5],
                       x[6] if isinstance(x[6], int) else str(x[6]), x[7])).encode())
    for x in ts:
        d.update(repr((x[0], x[1], str(x[2]), x[3])).encode())
    d.update(repr((vals, blkoff, fsz)).encode())
    print("DIGEST %s" % d.hexdigest()[:16])
    print("SKELETON: gates pending (probe phase)")

if __name__ == "__main__":
    main()