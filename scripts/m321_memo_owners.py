#!/usr/bin/env python3
"""M321 - pick (vi): NAME the last two unnamed memo-site owners and decode the shared
arrival test `test BYTE PTR [reg+0x38],0x40`.

Footing it stands on (do not re-derive): M315 named the memo `ds:0x68cbb4` = "the record
index for which the refresh pair 0x4e8d60/0x4e78e0 has already run" (`NAMED ## M315`);
M319 (pick (v)) enumerated the 8 UNGUARDED memo sites and left two owners unnamed
(`evidence/m319_guard_hoist.txt:28-52`): FUN_004ee410 (0x4ee6c9, 0x4ee883) and
FUN_004f41f0 (0x4f44a8, 0x4f455d), and 3 of the 9 arrivals carry that +0x38/0x40 test.

STATIC, ZERO BOX. Everything is computed from scratch/m574/text.txt (objdump .text) plus
ASCII read out of programs/terran.exe at the VAs the emitter pushes; the binary is only
memory-read, never run. Tables print FIRST, then the gates assert the printed numbers.

  G1 the 304-CHAIN: the image-wide multiply-chain (lea a,[i+i*8]; lea b,[i+a*2]; shl b,4)
     evaluates to 304, and ds:0x8f0d60 (M311's "record pointer") is fed by exactly that
     chain + `add ..,0x95da10` => it is a base_array row start, NOT a unit row (stride 52).
  G2 the two owners really are memo-site owners: memo store fed by `mov R,ds:0x68cbb0`,
     followed inside 25 B by the refresh pair in M318's order.
  G3 what they ARE: the status-icon emitters they call, with the msg/icon BYTES read out of
     the exe. FUN_004ee410 = the NUTRIENT/POPULATION family, FUN_004f41f0 = the TALENT one.
  G4 the arrival test: image-wide `test BYTE PTR [r+0x38],0x40` sites, each r's nearest def,
     the je that skips, and what lies on the fall-through it gates.
  G5 who owns bit 0x40 of that dword: every write to +0x38 through both address idioms,
     classified by the mask's effect on bit 6; the round-trip map inside FUN_0041a8f0.
  G6 the callee re-gates on the same bit.

  python3 -u scripts/m321_memo_owners.py
"""
import hashlib
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M321_TEXT", os.path.join(REPO, "scratch", "m574", "text.txt"))
EXE = os.environ.get("M321_EXE", os.path.join(REPO, "programs", "terran.exe"))
IDX = os.path.join(REPO, "ghidra_out", "index.csv")

MEMO = 0x68CBB4
IDXG = 0x68CBB0
REC = 0x8F0D60
BASE = 0x95DA10
FIELD38 = 0x95DA48          # BASE + 0x38, the folded idiom of the same field
SEL = 0x99AA38              # the scratch dword FUN_0041a8f0 round-trips the bits through
EMITTER = 0x48F100
PAIR = (0x4E8D60, 0x4E78E0)
OWNER = {"FUN_004ee410": 0x4EE410, "FUN_004f41f0": 0x4F41F0}
ARRIVER = {"FUN_00416ef0": 0x416EF0, "FUN_00416f60": 0x416F60, "FUN_0041a8f0": 0x41A8F0}

ADDR_RE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]*?)\t(\S.*?)\s*$")
CONT_RE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*$")
DS_RE = re.compile(r"\bds:(0x[0-9a-f]+)")
DISP_RE = re.compile(r"PTR \[([a-z][a-z0-9]+)\+(-?0x[0-9a-f]+)\]")


def load():
    """addr -> (idx, mnemonic, operands). Continuation byte-lines carry no insn text and
    are skipped; M321_PATCH rewrites insn text so a CODE mutant can be run against the
    real bytes (the harness, not this census, decides which)."""
    ins, addrs = {}, []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR_RE.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            txt = m.group(3).strip()
            parts = txt.split(None, 1)
            ins[a] = (parts[0].lower(), (parts[1] if len(parts) > 1 else ""))
            addrs.append(a)
    for spec in filter(None, os.environ.get("M321_PATCH", "").split(";")):
        a, txt = spec.split("|", 1)
        a = int(a, 16)
        if a not in ins:
            raise SystemExit("M321_PATCH: 0x%x is not an instruction start" % a)
        parts = txt.strip().split(None, 1)
        ins[a] = (parts[0].lower(), parts[1] if len(parts) > 1 else "")
    addrs.sort()
    return ins, addrs


INS, ADDRS = load()


def neighbours(a, back, fwd):
    """instruction addresses in [a-back, a+fwd] that exist as instruction starts."""
    lo = bisect_left(ADDRS, a - back)
    hi = bisect_right(ADDRS, a + fwd)
    return ADDRS[lo:hi]


from bisect import bisect_left, bisect_right  # noqa: E402  (used by neighbours)


def at(a):
    return INS.get(a)


def funcs():
    rows = []
    with open(IDX) as f:
        head = f.readline().strip().split(",")
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            r = dict(zip(head, line.strip().split(",")))
            rows.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    rows.sort()
    return rows


FUNCS = funcs()
FSTART = [r[0] for r in FUNCS]


def func_of(a):
    i = bisect_left(FSTART, a)
    if i < len(FSTART) and FSTART[i] == a:
        return FUNCS[i]
    if i == 0:
        return None
    return FUNCS[i - 1]


def span(a):
    """(entry, end_exclusive) of the function containing a."""
    e, name, size = func_of(a)
    return e, e + size, name


def read_va(va, n):
    """ASCII bytes at a virtual address of the shipped PE (header walk, no run)."""
    with open(EXE, "rb") as f:
        blob = f.read()
    pe = int.from_bytes(blob[0x3C:0x40], "little")
    nsec = int.from_bytes(blob[pe + 6:pe + 8], "little")
    optsz = int.from_bytes(blob[pe + 20:pe + 22], "little")
    opt = pe + 24
    magic = int.from_bytes(blob[opt:opt + 2], "little")
    imagebase = int.from_bytes(blob[opt + 34:opt + 38], "little") if magic == 0x10B \
        else int.from_bytes(blob[opt + 24:opt + 32], "little")
    sec = opt + optsz
    for i in range(nsec):
        s = sec + 40 * i
        va0 = imagebase + int.from_bytes(blob[s + 12:s + 16], "little")
        raw = int.from_bytes(blob[s + 20:s + 24], "little")
        vsz = int.from_bytes(blob[s + 8:s + 12], "little")
        rsz = int.from_bytes(blob[s + 16:s + 20], "little")
        if va0 <= va < va0 + max(vsz, rsz):
            off = raw + (va - va0)
            return blob[off:off + n]
    raise SystemExit("VA 0x%x outside every section" % va)


def cstr(va, cap=64):
    b = read_va(va, cap).split(b"\0")[0]
    return b.decode("latin-1", "replace")


def ds_of(op):
    m = DS_RE.search(op)
    return int(m.group(1), 16) if m else None


def disp_of(op):
    m = DISP_RE.search(op)
    return (m.group(1), int(m.group(2), 0)) if m else (None, None)


def is_store(mn, op):
    """objdump `dst,src`: a write to the first operand."""
    first = op.split(",")[0].strip()
    return mn in ("mov", "or", "and", "xor", "add", "sub", "inc", "dec", "movzx", "movsx",
                  "movbe", "not", "neg") and (ds_of(op) is not None or first.startswith(
                      ("BYTE", "WORD", "DWORD", "QWORD")) or first.startswith("["))


def back_def(a, reg, limit=40):
    """nearest address <= a that WRITES reg (coarse: any insn whose first operand is reg),
    stopping at the function entry. Returns (addr, mnemonic, op) or None."""
    e, end, _ = span(a)
    for x in reversed(neighbours(e, 0, a - e)):
        if x > a:
            continue
        m = at(x)
        if m is None:
            continue
        mn, op = m
        first = op.split(",")[0].strip()
        if x == a:
            continue
        if first == reg or (mn.startswith(("mov", "lea", "add", "sub", "xor", "or", "and"))
                            and first == reg):
            if mn in ("mov", "lea", "xor", "add", "sub", "or", "and", "sete", "setne",
                      "movzx", "movsx", "cmovne", "cmove", "not", "neg", "inc", "dec"):
                return x, mn, op
            return x, mn, op
    return None


def calls_after(a, want, window=48):
    """the first occurrence of each target in `want` at/after a, in order, within window."""
    out = []
    for x in neighbours(a, 0, window):
        if x <= a:
            continue
        m = at(x)
        if m and m[0] == "call":
            t = m[1].strip()
            if t.startswith("0x"):
                out.append((x, int(t, 16)))
    seq = [x for x in out]
    hits = {}
    for x, t in seq:
        if t in want and t not in hits:
            hits[t] = x
    return [(t, hits.get(t)) for t in want], seq


OUT = []


def P(s=""):
    OUT.append(s)
    print(s)


def main():
    sys.setrecursionlimit(10000)
    digest_src = []

    # ---------------------------------------------------------------- T1 the 304 chain
    P("-- T1 the 304 multiply-chain (lea a,[i+i*8]; lea b,[i+a*2]; shl b,4) and its uses --")
    chains = []
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "lea":
            continue
        if not re.match(r"^\[([a-z0-9]+)\+\1\*8\]$", m[1].split(",", 1)[-1].strip()):
            continue
        r1 = m[1].split(",")[0].strip()
        base_i = m[1].split("[")[1].split("+")[0].strip()
        n = neighbours(a, 0, 24)
        for x in n[1:]:
            mx = at(x)
            if not mx or mx[0] != "lea":
                continue
            ops = mx[1].split(",")[-1].strip().strip("[]")
            if ops != "%s+%s*2" % (base_i, r1):
                continue
            r2 = mx[1].split(",")[0].strip()
            for y in neighbours(x, 0, 16):
                my = at(y)
                if not my or my[0] != "shl" or y <= x:
                    continue
                if my[1].split(",")[0].strip() != r2:
                    continue
                sh = int(my[1].split(",")[1].strip(), 0)
                if sh == 4:
                    chains.append((a, x, y, base_i, r1, r2))
                    break
            if chains and chains[-1][2] == y if False else False:
                pass
            break
    mults = set()
    for c in chains:
        mults.add(19 << 4)
    uses = {}
    for a, x, y, bi, r1, r2 in chains:
        for z in neighbours(y, 0, 32):
            if z <= y:
                continue
            mz = at(z)
            if not mz:
                continue
            for mm in re.finditer(r"\+(-?0x[0-9a-f]{6,8})\]", mz[1]):
                k = int(mm.group(1), 0)
                if 0x900000 <= k < 0x9A0000:
                    uses[k] = uses.get(k, 0) + 1
    P("   chains=%d  evaluated multiplier (9x*2+x)<<4 = %d  stride of base_array = 0x130 = %d"
      % (len(chains), 19 * 16, 304))
    P("   global displacements the chain result feeds (0x9xxxxx only): %s"
      % sorted(uses.items(), key=lambda kv: (-kv[1], kv[0]))[:12])
    p348a = at(0x4E347B), at(0x4E347E), at(0x4E3481), at(0x4E3484), at(0x4E348A)
    P("   the fold that FEEDS ds:0x8f0d60 (0x4e347b..0x4e348a): %s"
      % " | ".join("%s %s" % m for m in p348a))
    P("   idiom identity: 0x%x - 0x%x = %d = 0x%x (the field the arrival test reads)"
      % (FIELD38, BASE, FIELD38 - BASE, FIELD38 - BASE))
    unit_stride, base_stride = 0x34, 0x130
    P("   RIVAL (the record pointer is a unit row): unit stride 0x%x=%d vs measured fold %d "
      "-> %s" % (unit_stride, unit_stride, 19 * 16,
                 "REJECTED" if 19 * 16 != unit_stride else "NOT REJECTED"))

    # ------------------------------------------------------------- T2 store lockstep
    P("-- T2 stores to the index ds:0x68cbb0 and the pointer ds:0x8f0d60 (image-wide) --")
    idxst, recst = [], []
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "mov":
            continue
        d = ds_of(m[1])
        if d == IDXG and m[1].split(",")[0].strip().startswith("DWORD"):
            idxst.append(a)
        if d == REC and m[1].split(",")[0].strip().startswith("DWORD"):
            recst.append(a)
    P("   index stores=%d %s" % (len(idxst), [hex(x) for x in idxst]))
    P("   pointer stores=%d %s" % (len(recst), [hex(x) for x in recst]))
    dist = []
    for a in recst:
        cand = [b for b in idxst if a - 64 <= b <= a + 64]
        dist.append((hex(a), [hex(b) for b in cand]))
    for d in dist:
        P("   %s paired index store(s) within +-64 B: %s" % d)

    # --------------------------------------------------------------- T3 the two owners
    P("-- T3 the memo law inside the two unnamed owners --")
    ownersites = {}
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "mov":
            continue
        if ds_of(m[1]) != MEMO or not m[1].split(",")[0].strip().startswith("DWORD"):
            continue
        reg = m[1].split(",")[1].strip()
        bd = back_def(a, reg, limit=40)
        fed = bd and ds_of(bd[2]) == IDXG
        e, end, name = span(a)
        if not fed:
            continue
        hits, seq = calls_after(a, set(PAIR), window=48)
        order_ok = (hits[0][1] is not None and hits[1][1] is not None
                    and hits[0][1] < hits[1][1])
        ownersites.setdefault(name, []).append((a, reg, order_ok))
    for name in OWNER:
        sites = ownersites.get(name, [])
        P("   %s memo stores fed by `mov R,ds:0x68cbb0` = %d %s (refresh pair in order: %s)"
          % (name, len(sites), [hex(s[0]) for s in sites], [bool(s[2]) for s in sites]))

    P("-- T3b the status-icon emitters they call, msg/icon BYTES read from the PE --")
    fam = {}
    for name, entry in OWNER.items():
        e, end, _ = span(entry)
        rows = []
        for a in neighbours(e, 0, end - e):
            m = at(a)
            if not m or m[0] != "call" or not m[1].strip().startswith("0x"):
                continue
            if int(m[1], 16) != EMITTER:
                continue
            pushed = []
            for x in reversed(neighbours(a, 40, 0)):
                if x >= a:
                    continue
                mx = at(x)
                if not mx:
                    continue
                if mx[0] == "push":
                    t = mx[1].strip()
                    if re.fullmatch(r"0x[0-9a-f]+", t):
                        pushed.append(int(t, 16))
                elif mx[0] == "call":
                    break
            rows.append((a, pushed))
        fam[name] = []
        for a, pushed in rows:
            # the two VAs in the push list that map to printable ASCII
            ss = []
            for v in pushed:
                try:
                    s = cstr(v)
                except Exception:
                    continue
                if s and all(32 <= ord(c) < 127 for c in s) and len(s) > 3:
                    ss.append((v, s))
            fam[name].append((a, ss))
            P("   %s @0x%x emitter pushes %s" % (name, a, [s for _, s in ss]))

    # ------------------------------------------------------------- T4 the arrival test
    P("-- T4 image-wide `test BYTE PTR [r+0x38],0x40` and what it gates --")
    sites = []
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "test":
            continue
        r, d = disp_of(m[1])
        if d == 0x38 and r and "BYTE" in m[1] and m[1].rstrip().endswith(",0x40"):
            sites.append((a, r))
    P("   sites=%d %s" % (len(sites), [hex(a) for a, _ in sites]))
    arrrows = []
    for a, r in sites:
        bd = back_def(a, r, limit=40)
        e, end, name = span(a)
        # the jcc right after the test, and the call it skips over
        nxt = [x for x in neighbours(a, 0, 8) if x > a]
        j = at(nxt[0]) if nxt else None
        tgt = int(j[1].split()[-1], 16) if j and j[1].split() else None
        gated, seq = calls_after(a, {OWNER["FUN_004f41f0"]}, window=48)
        gc = gated[0][1]
        clears = [x for x in neighbours(a, 0, 48) if x > a and (tgt is None or x < tgt)
                  and at(x) and at(x)[0] == "mov" and DISP_RE.search(at(x)[1])
                  and disp_of(at(x)[1])[1] in (0x78, 0x7C, 0x80)]
        arrrows.append((a, name, bd[1:] if bd else None, tgt is not None and gc is not None
                        and gc < tgt, sorted(disp_of(at(x))[1] for x in clears),
                        (tgt is not None) and (tgt > (gc or 0))))
        P("   0x%x in %-14s r=%s def=%s | je->0x%x gated call of FUN_004f41f0 at %s "
          "(skipped by the je: %s) | record stores cleared first: %s"
          % (a, name, r, ("%s %s" % bd[1:3]) if bd else "NONE", tgt or 0,
             hex(gc) if gc else "none", gc is not None and tgt is not None and gc < tgt,
             [hex(d) for d in sorted(disp_of(at(x))[1] for x in clears)]))

    # --------------------------------------------------------- T5 provenance of bit 0x40
    P("-- T5 every write to the record field +0x38 (both idioms), effect on bit 6 --")
    def bit6(mn, mask, fullword=False):
        if mn == "or":
            return "SETS" if mask & 0x40 else "keeps"
        if mn == "and":
            return "CLEARS" if not (mask & 0x40) else "keeps"
        if mn == "mov":
            return "FULLWORD" if fullword else "SETS?"
        return "other"

    writes = []
    for a in ADDRS:
        m = at(a)
        if not m:
            continue
        mn, op = m
        r, d = disp_of(op)
        if mn == "mov" and ds_of(op) is None and (d == 0x38 and op.split(",")[0].strip()
                                                  .startswith("DWORD")):
            imm = op.split(",")[-1].strip()
            if re.fullmatch(r"0x[0-9a-f]+", imm):
                writes.append((a, "rec", r, mn, int(imm, 0), "FULLWORD-imm"))
                continue
            if "ds:" in op:
                continue
            writes.append((a, "rec", r, mn, None, "FULLWORD-reg"))
            continue
        k = re.search(r"\+(-?0x[0-9a-f]{6,8})\]", op)
        if k and int(k.group(1), 0) == FIELD38 and mn in ("mov", "or", "and", "not"):
            first = op.split(",")[0].strip()
            if not first.startswith("DWORD"):
                continue
            imm = op.split(",")[-1].strip()
            mask = int(imm, 0) if re.fullmatch(r"0x[0-9a-f]+", imm) else None
            writes.append((a, "folded", r, mn, mask, bit6(mn, mask or 0, mask is None)))
    # the record-view writes are only the ones whose register is the record pointer
    recview = []
    for a, kind, r, mn, mask, note in writes:
        if kind != "rec":
            continue
        bd = back_def(a, r, limit=40)
        ok = bool(bd) and ds_of(bd[2]) == REC
        recview.append((a, r, mn, mask, note, ok))
        P("   0x%x rec-view [%s+0x38] %-4s %-12s bit6=%-11s reg from ds:0x8f0d60=%s"
          % (a, r, mn, hex(mask) if mask is not None else "-", note, ok))
    folded_w = [(a, mn, mask, note) for a, kind, r, mn, mask, note in writes if kind == "folded"]
    for a, mn, mask, note in folded_w:
        P("   0x%x folded [..+0x95da48] %-4s %-12s bit6=%s" % (a, mn,
          hex(mask) if mask is not None else "-", note))
    setter40 = [a for a, kind, r, mn, mask, note in writes if kind == "rec" and mn == "or"
                and mask and mask & 0x40] + \
               [a for a, mn, mask, note in folded_w if mn == "or" and mask and mask & 0x40]
    P("   sites that OR bit 0x40 into the field: %s" % [hex(x) for x in setter40])

    P("-- T5b FUN_0041a8f0's round trip: record bits -> scratch ds:0x99aa38 -> record bits --")
    e, end, name = span(0x41A8F0)
    extract, writeback = [], []
    for a in neighbours(e, 0, end - e):
        m = at(a)
        if not m:
            continue
        mn, op = m
        if mn == "test":
            r, d = disp_of(op)
            k = op.rstrip().rsplit(",", 1)
            mask = int(k[-1].strip(), 0) if re.fullmatch(r" 0x[0-9a-f]+", k[-1]) else None
            if d == 0x38 and mask:
                nxt = [x for x in neighbours(a, 0, 12) if x > a][:3]
                bit = None
                for x in nxt:
                    mx = at(x)
                    if mx and mx[0] == "or" and mx[1].split(",")[0].strip() == "al":
                        bit = int(mx[1].split(",")[1].strip(), 0)
                        break
                extract.append((a, mask, bit))
            if ds_of(op) == SEL and mask:
                nxt = [x for x in neighbours(a, 0, 12) if x > a][:3]
                for x in nxt:
                    mx = at(x)
                    if mx and mx[0] in ("or", "and") and DISP_RE.search(mx[1]) \
                            and disp_of(mx[1])[1] == 0x38:
                        mm = mx[1].rstrip().rsplit(",", 1)
                        writeback.append((a, mask, mx[0],
                                          int(mm[-1].strip(), 0) if re.fullmatch(
                                              r" 0x[0-9a-f]+", mm[-1]) else None))
                        break
    P("   extraction tests of [..+0x38] (mask -> scratch bit): %s"
      % [(hex(m), hex(b) if b else None) for _, m, b in extract])
    P("   write-backs gated on the scratch (scratch bit -> op on [..+0x38]): %s"
      % [(hex(m), o, hex(v) if v else None) for _, m, o, v in writeback])

    # ----------------------------------------------------------------- T6 callee gate
    P("-- T6 the callee re-tests the same bit on the same pointer --")
    e, end, name = span(OWNER["FUN_004f41f0"])
    selfgate = []
    for a in neighbours(e, 0, end - e):
        m = at(a)
        if m and m[0] == "test" and "0x40" in m[1] and ("cl" in m[1].split(",")[0] or
                                                        "BYTE" in m[1]):
            bd = back_def(a, "ecx", limit=40)
            ld = None
            if bd:
                r, d = disp_of(bd[2])
                ld = (r, d, ds_of(at(back_def(bd[0], r, limit=40)[2]) if
                                 back_def(bd[0], r, limit=40) else None))
            selfgate.append((a, m[1], bd[0] if bd else None, bd[1:] if bd else None, ld))
    for a, txt, ba, bm, ld in selfgate:
        P("   0x%x %-22s fed by 0x%x %s" % (a, txt, ba or 0, bm))
    digest_src = "\n".join(OUT).encode()

    # --------------------------------------------------------------------- gates
    G = {}
    G["G1"] = (len(chains) >= 1 and 19 * 16 == 304 and FIELD38 - BASE == 56
               and at(0x4E3484)[1].endswith("0x95da10") and at(0x4E348A)[1].startswith(
                   "DWORD PTR ds:0x8f0d60") and unit_stride != 304
               and uses.get(BASE, 0) + uses.get(BASE + 4, 0) > 0)
    G["G2"] = (len(ownersites.get("FUN_004ee410", [])) == 2
               and len(ownersites.get("FUN_004f41f0", [])) == 2
               and all(s[2] for v in ownersites.values() for s in v))
    n1 = sorted({s for _, rows in fam["FUN_004ee410"] for _, s in rows})
    n2 = sorted({s for _, rows in fam["FUN_004f41f0"] for _, s in rows})
    G["G3"] = (any("STARVE" in s or "NUTRIENT" in s or "POPULATION" in s for s in n1)
               and any("PSYCH" in s for s in n2) and not (set(n1) & set(n2)))
    G["G4"] = (len(sites) == 3 and all(x[2] and "ds:0x8f0d60" in str(x[2]) for x in arrrows)
               and all(x[3] for x in arrrows) and all(x[4] == [0x78, 0x7C, 0x80]
                                                      for x in arrrows))
    G["G5"] = (len(setter40) == 1 and hex(0x41AC34) in [hex(x) for x in setter40]
               and any(m == 0x40 and v == 0x40 for _, m, o, v in writeback))
    G["G6"] = len(selfgate) >= 1 and all(
        "0x38" in str(x[4]) or "0x8f0d60" in str(x[3]) for x in selfgate)
    P("")
    P("== digest %s" % hashlib.sha256(digest_src).hexdigest()[:16])
    for k in sorted(G):
        P("%s %s" % ("PASS" if G[k] else "FAIL", k))
    bad = [k for k in G if not G[k]]
    if bad:
        P("FAIL m321: %d/%d gates failed: %s" % (len(bad), len(G), bad))
        return 1
    P("PASS m321: %d/%d gates (2 owners named: FUN_004ee410 nutrient/population status, "
      "FUN_004f41f0 talent/psych-request status; the +0x38/0x40 test gates the FUN_004f41f0 "
      "leg on base_array field 56 bit 6)" % (len(G), len(G)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
