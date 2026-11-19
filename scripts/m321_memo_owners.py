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
IDX = os.environ.get("M321_INDEX", os.path.join(REPO, "ghidra_out", "index.csv"))

MEMO = 0x68CBB4
IDXG = 0x68CBB0
REC = 0x8F0D60
BASE = 0x95DA10
FIELD38 = 0x95DA48          # BASE + 0x38, the folded idiom of the same field
SEL = 0x99AA38              # the scratch dword FUN_0041a8f0 round-trips the bits through
EMITTER = 0x48F100
PAIR = (0x4E8D60, 0x4E78E0)
PAIR_MAX = 25               # the claimed bound: the WHOLE pair completes within this many B
FIELDS = (0x78, 0x7C, 0x80)  # record fields the caller clears before the leg the je gates
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
    imagebase = int.from_bytes(blob[opt + 28:opt + 32], "little") if magic == 0x10B \
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
    raise ValueError("VA %#x outside every section" % va)


def cstr(va, cap=64):
    b = read_va(va, cap).split(b"\0")[0]
    return b.decode("latin-1", "replace")


def ds_of(op):
    m = DS_RE.search(op)
    return int(m.group(1), 16) if m else None


def disp_of(op):
    m = DISP_RE.search(op)
    return (m.group(1), int(m.group(2), 0)) if m else (None, None)


def stores_to(op, target):
    """True if this operand list WRITES the dword global `target`. objdump emits the same
    instruction in two encodings - `mov DWORD PTR ds:X,reg` and `mov ds:X,reg` (the a3/89
    forms) - and a detector that only reads the DWORD-shaped face silently misses every
    short-form site (M311's six index stores are 5 + 1 here)."""
    first = op.split(",")[0].strip()
    if first.startswith("ds:"):
        return ds_of(first) == target
    return first.startswith(("DWORD PTR ", "DWORD ")) and ds_of(first) == target


def is_store(mn, op):
    """objdump `dst,src`: a write to the first operand."""
    first = op.split(",")[0].strip()
    return mn in ("mov", "or", "and", "xor", "add", "sub", "inc", "dec", "movzx", "movsx",
                  "movbe", "not", "neg") and (ds_of(op) is not None or first.startswith(
                      ("BYTE", "WORD", "DWORD", "QWORD")) or first.startswith("["))


CLOBBER = ("eax", "ecx", "edx")
NONWRITE = ("cmp", "test", "push", "pusha", "popf")
ALIAS = {"al": "eax", "ah": "eax", "ax": "eax", "cl": "ecx", "ch": "ecx", "cx": "ecx",
         "dl": "edx", "dh": "edx", "dx": "edx", "bl": "ebx", "bx": "ebx", "si": "esi",
         "di": "edi", "bp": "ebp"}


def back_def(a, reg):
    """Nearest preceding instruction that WRITES `reg`, scanning straight back to the
    function entry (there is deliberately NO byte limit: a bounded scan would silently
    return None on a long live range and make "nearest def" claims unverifiable - the
    locality of every def this census quotes is instead MEASURED and printed as a byte
    distance, and the gates pin that distance). Two hazards are honoured (both bite this
    census when ignored): a CALL kills a CALLER-SAVED register, so a `mov eax,ds:0x8f0d60`
    several blocks up is NOT a def; and cmp/test/push name a register without writing it.
    Straight-line only - a control-flow join is still an over-approximation, declared OPEN
    in the NAMED block."""
    reg = ALIAS.get(reg, reg)
    e, end, _ = span(a)
    for x in reversed(neighbours(e, 0, a - e)):
        if x >= a:
            continue
        m = at(x)
        if m is None:
            continue
        mn, op = m
        if mn == "call":
            if reg in CLOBBER:
                return None
            continue
        if mn in NONWRITE:
            continue
        if op.split(",")[0].strip() == reg:
            return x, mn, op
    return None


def is_zero(a, v):
    """Does operand `v` provably hold 0 at address `a`? objdump's own zero-forms only: an
    immediate 0, or the nearest straight-line def being xor/sub of the register with
    itself, or a mov of immediate 0. Returns (proven, how) - `how` is always the def text,
    so a claim of "zeroed" that rests on an unrelated value prints the line that refutes it.
    """
    if v in ("0x0", "0"):
        return True, "immediate 0"
    if not re.fullmatch(r"[a-z][a-z0-9]*", v):
        return False, "operand %s" % v
    reg = ALIAS.get(v, v)
    bd = back_def(a, v)
    if not bd:
        return False, "%s: no straight-line def" % v
    mn, op = bd[1], bd[2]
    parts = [p.strip() for p in op.split(",")]
    how = "%s %s @0x%x" % (mn, op, bd[0])
    if mn in ("xor", "sub") and len(parts) == 2 and parts[0] == parts[1] == reg:
        return True, how
    if mn == "mov" and len(parts) == 2 and parts[1] in ("0x0", "0"):
        return True, how
    return False, how


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
    chains = []   # (lea1, lea2, shl, i, r1, r2, s1, s2, sh)
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "lea":
            continue
        mm = re.fullmatch(r"\[([a-z0-9]+)\+\1\*(\d+)\]", m[1].split(",", 1)[-1].strip())
        if not mm:
            continue
        bi, s1 = mm.group(1), int(mm.group(2))
        r1 = m[1].split(",")[0].strip()
        for x in neighbours(a, 0, 24):
            if x <= a:
                continue
            mx = at(x)
            if not mx or mx[0] != "lea":
                continue
            mmx = re.fullmatch(r"\[([a-z0-9]+)\+([a-z0-9]+)\*(\d+)\]",
                               mx[1].split(",", 1)[-1].strip())
            if not mmx or mmx.group(1) != bi or mmx.group(2) != r1:
                continue
            s2, r2 = int(mmx.group(3)), mx[1].split(",")[0].strip()
            for y in neighbours(x, 0, 16):
                if y <= x:
                    continue
                my = at(y)
                if not my or my[0] != "shl" or my[1].split(",")[0].strip() != r2:
                    continue
                cnt = my[1].split(",")[-1].strip()
                if not re.fullmatch(r"0x[0-9a-f]+|\d+", cnt):
                    continue        # a CL-counted shift is not a constant fold
                sh = int(cnt, 0)
                chains.append((a, x, y, bi, r1, r2, s1, s2, sh))
                break
            break

    def mult(c):
        """(i + i*s1) -> r1 ; (i + r1*s2) -> r2 ; r2 << sh  == the multiplier, PARSED."""
        return (1 + (1 + c[6]) * c[7]) << c[8]

    hist = {}
    for c in chains:
        hist[mult(c)] = hist.get(mult(c), 0) + 1
    P("   chains=%d  multiplier histogram (parsed from the scale+shift fields): %s"
      % (len(chains), sorted(hist.items(), key=lambda kv: (-kv[1], kv[0]))[:6]))
    c304 = [c for c in chains if mult(c) == 304]
    uses = {}
    for c in c304:
        y = c[2]
        for z in neighbours(y, 0, 32):
            if z <= y:
                continue
            mz = at(z)
            if not mz:
                continue
            for mmk in re.finditer(r"\+(-?0x[0-9a-f]{6,8})\]", mz[1]):
                k = int(mmk.group(1), 0)
                if 0x900000 <= k < 0x9A0000:
                    uses[k] = uses.get(k, 0) + 1
    P("   304-chains=%d; global displacements they feed: %s"
      % (len(c304), [("%#x" % k, v) for k, v in
                     sorted(uses.items(), key=lambda kv: (-kv[1], kv[0]))[:8]]))
    # the one chain that actually feeds ds:0x8f0d60: its shl result must be the register
    # the add-of-0x95da10 modifies, and that add must sit right before the store.
    feed = [c for c in c304 if c[2] < 0x4E3484 and 0x4E3484 - c[2] <= 16
            and at(0x4E3484)[1].split(",")[0].strip() == c[5]
            and at(0x4E3484)[0] == "add" and at(0x4E3484)[1].endswith("0x95da10")]
    P("   chain that feeds ds:0x8f0d60 (shl at %s, then `add %s,0x95da10` @0x4e3484): %d"
      % ([hex(c[2]) for c in feed], "edx", len(feed)))
    P("   the store itself 0x4e348a: %s %s" % at(0x4E348A))
    P("   idiom identity: 0x%x - 0x%x = %d = 0x%x (the field the arrival test reads)"
      % (FIELD38, BASE, FIELD38 - BASE, FIELD38 - BASE))
    unit_stride = 0x34
    P("   RIVAL (the record pointer is a unit row): unit stride 0x%x=%d vs the measured "
      "fold %d -> %s" % (unit_stride, unit_stride, 304,
                         "REJECTED" if 304 != unit_stride else "NOT REJECTED"))

    # ------------------------------------------------------------- T2 store lockstep
    P("-- T2 stores to the index ds:0x68cbb0 and the pointer ds:0x8f0d60 (image-wide) --")
    idxst, recst = [], []
    for a in ADDRS:
        m = at(a)
        if not m or m[0] != "mov":
            continue
        d = None
        if m[0] == "mov" and stores_to(m[1], IDXG):
            idxst.append(a)
        if m[0] == "mov" and stores_to(m[1], REC):
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
        if not stores_to(m[1], MEMO):
            continue
        reg = m[1].split(",")[-1].strip()
        bd = back_def(a, reg)
        fed = bd and ds_of(bd[2]) == IDXG
        e, end, name = span(a)
        if not fed:
            continue
        # The order is PINNED by the PAIR tuple, never by set iteration (review #324 P1-2):
        # hits[0] must be PAIR[0] and hits[1] must be PAIR[1], at increasing addresses.
        hits, seq = calls_after(a, PAIR, window=48)
        order_ok = (hits[0][1] is not None and hits[1][1] is not None
                    and hits[0][0] == PAIR[0] and hits[1][0] == PAIR[1]
                    and hits[0][1] < hits[1][1])
        # and the law is a DISTANCE, not an existence (review #324 P1-1): measure how far
        # the SECOND refresh call sits from its memo store.
        d1 = None if hits[0][1] is None else hits[0][1] - a
        d2 = None if hits[1][1] is None else hits[1][1] - a
        form = "a3" if m[1].strip().startswith("ds:") else "DWORD"
        ownersites.setdefault(name, []).append((a, reg, order_ok, d1, d2, form))
    a3memo = 0
    for name in OWNER:
        sites = ownersites.get(name, [])
        P("   %s memo stores fed by `mov R,ds:0x68cbb0` = %d %s (pair in PINNED order: %s; "
          "B to 1st/2nd refresh call: %s; encoding: %s)"
          % (name, len(sites), [hex(s[0]) for s in sites], [bool(s[2]) for s in sites],
             [(s[3], s[4]) for s in sites], [s[5] for s in sites]))
    ownrows = [s for k in OWNER for s in ownersites.get(k, [])]
    a3memo = sum(1 for s in ownrows if s[5] == "a3")
    allpair = [s[4] for s in ownrows if s[4] is not None]
    maxpair = max(allpair) if allpair else None
    P("   the WHOLE pair completes within %s B of its memo store (measured set %s) - the "
      "claim is <=%d" % (maxpair, sorted(set(allpair)), PAIR_MAX))
    P("   the two owners' memo-store encodings: a3 short form=%d, DWORD form=%d (the a3 "
      "site(s): %s)" % (a3memo, len(ownrows) - a3memo,
                        [hex(s[0]) for s in ownrows if s[5] == "a3"]))
    P("   image-wide with the same filter (informational, not claimed): memo stores fed by the "
      "index = %d in %d functions, of which these two owners hold %d"
      % (sum(len(v) for v in ownersites.values()), len(ownersites), len(ownrows)))

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
        bd = back_def(a, r)
        defstr = "NONE" if not bd else "%s %s" % (bd[1], bd[2])
        defdist = None if not bd else a - bd[0]
        e, end, name = span(a)
        # the jcc right after the test, and the call its JE skips over. The MNEMONIC is part
        # of the claim (review #324 P1-3): a `jne` there would gate the opposite branch.
        nxt = [x for x in neighbours(a, 0, 8) if x > a]
        j = at(nxt[0]) if nxt else None
        jmn = j[0] if j else "no-jcc"
        isje = jmn == "je"
        tgt = int(j[1].split()[-1], 16) if isje and j[1].split() else None
        gated, seq = calls_after(a, (OWNER["FUN_004f41f0"],), window=48)
        gc = gated[0][1]
        # What the caller writes to the record's +0x78/+0x7c/+0x80 between the test and its
        # je. A field counts as ZEROED only if (i) the base register is the test's own
        # register or resolves to ds:0x8f0d60 by its nearest def, and (ii) the value's
        # nearest def is a provable zero-form (review #324 P1-4). Everything else is
        # collected in notzero and printed - a write the claim does not cover.
        clears, notzero = [], []
        for x in neighbours(a, 0, 128):
            if tgt is None or not (a < x < tgt):
                continue
            mx = at(x)
            if not mx or mx[0] != "mov" or not mx[1].startswith("DWORD"):
                continue
            rb, db = disp_of(mx[1])
            if rb is None or db not in FIELDS:
                continue
            v = mx[1].rsplit(",", 1)[-1].strip()
            # the base must be THIS record at the moment of the write - proved from the
            # write's own address, not from the test's (edx is loaded after the test)
            bdef = back_def(x, rb)
            bok = bool(bdef and ds_of(bdef[2]) == REC)
            ok0, how = is_zero(x, v)
            (clears if (bok and ok0) else notzero).append((db, x, rb, v, bok, how))
        zeroed = sorted({d for d, _x, _rb, _v, _b, _h in clears})
        arrrows.append((a, name, defstr, bool(isje and gc is not None and tgt is not None
                                             and gc < tgt), zeroed, tgt, gc, jmn, defdist,
                        [(x, d, rb, v, bok, how) for d, x, rb, v, bok, how in notzero]))
        P("   0x%x in %-13s r=%-3s nearest def of r: %-28s (%s B back) | %s -> je 0x%x | the "
          "call of FUN_004f41f0 at %s lies ON THE FALL-THROUGH (je skips it: %s) | before "
          "the je it ZEROES record fields %s"
          % (a, name, r, defstr, defdist, (j[0] + " " + j[1]) if j else "no jcc", tgt or 0,
             hex(gc) if gc else "none", arrrows[-1][3], [hex(d) for d in zeroed]))
        for d, x, rb, v, _b, how in sorted(clears):
            P("      0x%x mov DWORD PTR [%s+0x%x],%s - base proven = this record at the write, "
              "value proven 0 by %s" % (x, rb, d, v, how))
        for x, d, rb, v, bok, how in arrrows[-1][9]:
            P("      NOT a proven zero on this record: 0x%x mov DWORD PTR [%s+0x%x],%s "
              "(base resolves to the record: %s) - value's nearest def: %s"
              % (x, rb, d, v, bok, how))

    trip = {(re.search(r"ds:(0x[0-9a-f]+)", x[2]).group(1) if re.search(r"ds:(0x[0-9a-f]+)", x[2]) else None,
             0x38, 0x40) for x in arrrows}
    P("   RIVAL (three look-alike tests on three different fields): distinct "
      "(def-global, disp, mask) triples = %d -> %s"
      % (len(trip), "REJECTED: one field, one pointer, three callers" if len(trip) == 1
         else "NOT REJECTED"))
    P("-- T5 writes to base_array field +0x38 (dword): both address idioms --")

    def eff(mn, mask):
        if mask is None:
            return "FULLWORD-untraced"
        if mn == "or":
            return "SETS bit6" if mask & 0x40 else "preserves bit6"
        if mn == "and":
            return "CLEARS bit6" if not (mask & 0x40) else "preserves bit6"
        if mn == "mov":
            return "OVERWRITES bit6=%d" % bool(mask & 0x40)
        return "other"

    WRMN = ("mov", "or", "and", "xor", "not", "neg", "add", "sub", "inc", "dec")
    recw, foldw = [], []
    for a in ADDRS:
        m = at(a)
        if not m or m[0] not in WRMN:
            continue
        mn, op = m
        if not op.split(",")[0].strip().startswith("DWORD"):
            continue
        r, d = disp_of(op)
        imm = op.rsplit(",", 1)[-1].strip()
        mask = int(imm, 0) if re.fullmatch(r"0x[0-9a-f]+", imm) else None
        if d == 0x38:
            bd = back_def(a, r)
            recw.append((a, r, mn, mask, eff(mn, mask),
                         bool(bd) and ds_of(bd[2]) == REC, bd[0] if bd else None))
        else:
            k = re.search(r"\+(-?0x[0-9a-f]{6,8})\]", op)
            if k and int(k.group(1), 0) == FIELD38:
                foldw.append((a, r, mn, mask, eff(mn, mask)))
    recok = [x for x in recw if x[5]]
    tally = {}
    for x in [(x[4]) for x in recok] + [x[4] for x in foldw]:
        tally[x] = tally.get(x, 0) + 1
    P("   [reg+0x38] dword writes image-wide=%d; accepted as THIS field (nearest def of the "
      "base register is ds:0x8f0d60)=%d; rejected (some other object's +0x38)=%d"
      % (len(recw), len(recok), len(recw) - len(recok)))
    P("   folded-view writes [reg+0x95da48]=%d" % len(foldw))
    P("   effect on bit 6 (accepted views): %s" % sorted(tally.items()))
    for x in recok:
        if x[3] is not None:
            P("   0x%x rec-view %-4s %-10s -> %s" % (x[0], x[2], hex(x[3]), x[4]))
    for x in foldw:
        P("   0x%x folded  %-4s %-10s -> %s" % (x[0], x[2],
          hex(x[3]) if x[3] is not None else "-", x[4]))
    fw = [hex(x[0]) for x in recok if x[3] is None]
    P("   untraced FULLWORD stores through the record view (a whole-dword mov can set or "
      "clear bit 6; their SOURCES are not traced this round - OPEN): %d %s"
      % (len(fw), fw[:14] + (["..."] if len(fw) > 14 else [])))
    setter40 = [x[0] for x in recok if x[2] == "or" and x[3] and x[3] & 0x40] + \
               [x[0] for x in foldw if x[2] == "or" and x[3] and x[3] & 0x40]
    P("   the only sites that OR 0x40 into the field: %s" % [hex(x) for x in setter40])

    P("-- T5b FUN_0041a8f0's round trip: field bits -> scratch ds:0x99aa38 -> field bits --")
    e, end, name = span(0x41A8F0)
    extract, writeback = [], []

    def field_src(a, operand):
        """Where does the tested operand come from? Either it IS [reg+0x38], or the register
        was loaded from there by the nearest def. Returns (load_site, ptr_reg, how)."""
        first = operand.split(",")[0].strip()
        r, d = disp_of(operand)
        if d == 0x38:
            return a, r, "inline"
        bd = back_def(a, ALIAS.get(first, first))
        if bd:
            r2, d2 = disp_of(bd[2])
            if d2 == 0x38:
                return bd[0], r2, "via-def %#x" % bd[0]
        return None

    for a in neighbours(e, 0, end - e):
        m = at(a)
        if not m or m[0] != "test":
            continue
        v = m[1].rsplit(",", 1)[-1].strip()
        if not re.fullmatch(r"0x[0-9a-f]+", v):
            continue
        mask = int(v, 0)
        fs = field_src(a, m[1])
        if fs:
            bit = None
            for x in neighbours(a, 0, 12):
                if x <= a:
                    continue
                mx = at(x)
                if not mx:
                    continue
                if mx[0] in ("or", "and") and mx[1].split(",")[0].strip() == "al":
                    bit = (mx[0], int(mx[1].rsplit(",", 1)[-1].strip(), 0))
                    break
                if mx[0] == "test":
                    break
            pdef = back_def(fs[0], fs[1]) if fs[1] else None
            extract.append((a, mask, bit, fs[2],
                            ds_of(pdef[2]) if pdef else None))
            continue
        if ds_of(m[1]) == SEL:
            wb = None
            for x in neighbours(a, 0, 24):
                if x <= a:
                    continue
                mx = at(x)
                if not mx:
                    continue
                if mx[0] in ("or", "and") and disp_of(mx[1])[1] == 0x38:
                    wb = (mx[0], int(mx[1].rsplit(",", 1)[-1].strip(), 0), x)
                    break
                if mx[0] in ("test", "call"):
                    break
            writeback.append((a, mask, wb))
    P("   extraction: test <field+0x38>,mask -> al op (mask, scratch bit, how the tested "
      "operand was loaded, ptr-global of that load): %s"
      % [(hex(x), hex(mk), b, how, ("%#x" % g) if g else None)
         for x, mk, b, how, g in extract])
    P("   write-back: test ds:0x99aa38,bit -> op on [rec+0x38]: %s"
      % [(hex(x), hex(mk), (wb[0], hex(wb[1]), hex(wb[2])) if wb else None)
         for x, mk, wb in writeback])
    pairs = {(mk, b[1]) for _, mk, b, _h, _g in extract if b and b[0] == "or"}
    back = {(mk, wb[1]) for _, mk, wb in writeback if wb and wb[0] == "or"}
    P("   record bit -> scratch bit: %s" % sorted((hex(a), hex(b)) for a, b in pairs))
    P("   scratch bit -> record bit: %s" % sorted((hex(a), hex(b)) for a, b in back))
    P("   inverse on bit 0x40: extraction %s / write-back %s"
      % ((0x40, 0x8) in pairs, (0x8, 0x40) in back))

    # ----------------------------------------------------------------- T6 callee gate
    P("-- T6 the callee re-tests the same bit on the same pointer --")
    e, end, name = span(OWNER["FUN_004f41f0"])
    selfgate, other40 = [], []
    for a in neighbours(e, 0, end - e):
        m = at(a)
        if not m or m[0] != "test" or m[1].rsplit(",", 1)[-1].strip() != "0x40":
            continue
        r, d = disp_of(m[1])
        reg = r if r else m[1].split(",")[0].strip()
        chain = []
        bd = back_def(a, reg)
        if bd:
            chain.append("%s %s" % (bd[1], bd[2]))
            r2, d2 = disp_of(bd[2])
            if d2 == 0x38 and r2:
                b2 = back_def(bd[0], r2)
                if b2:
                    chain.append("%s %s" % (b2[1], b2[2]))
                    if ds_of(b2[2]) == REC:
                        selfgate.append((a, m[1], " <- ".join(chain)))
        if not chain or "ds:0x8f0d60" not in chain[-1]:
            other40.append((a, m[1]))
    for a, txt, ch in selfgate:
        P("   0x%x test %-18s <- %s" % (a, txt, ch))
    P("   other `test ...,0x40` inside FUN_004f41f0 NOT traced to this field: %s"
      % [(hex(a), t) for a, t in other40])
    digest_src = "\n".join(OUT).encode()

    # --------------------------------------------------------------------- gates
    G = {}
    G["G1"] = (len(c304) > 100 and len(feed) == 1 and mult(feed[0]) == 304
               and stores_to(at(0x4E348A)[1], REC) and uses.get(BASE, 0) == 122
               and FIELD38 - BASE == 56 and unit_stride != 304
               # the rival is not hand-written: the MOST COMMON non-304 multiplier in the
               # printed histogram has to BE the unit stride, at its printed chain count
               and hist.get(304) == 646 and hist.get(unit_stride) == 565
               and max(((v, k) for k, v in hist.items() if k != 304))[1] == unit_stride)
    # the gate is scoped to the TWO OWNERS (ownrows), never to ownersites.values(), which
    # after the image-wide census holds every index-fed memo store in the image (review #324:
    # a gate over the census would pass on a wrong owner set).
    G["G2"] = (len(ownersites.get("FUN_004ee410", [])) == 2
               and len(ownersites.get("FUN_004f41f0", [])) == 2
               and [hex(s[0]) for s in ownrows]
               == ["0x4ee6c9", "0x4ee883", "0x4f44a8", "0x4f455d"]
               and all(s[2] for s in ownrows)
               and maxpair == 11 and maxpair <= PAIR_MAX and a3memo == 1)
    n1 = sorted({s for _, rows in fam["FUN_004ee410"] for _, s in rows})
    n2 = sorted({s for _, rows in fam["FUN_004f41f0"] for _, s in rows})
    NUTR = {"STARVE", "starv_sm.pcx", "POPULATIONLIMIT", "pop_sm.pcx", "LOWNUTRIENT",
            "LOWNUTRIENTFARMS", "LOWNUTRIENTFORMERS", "LOWNUTRIENTSPEC1", "LOWNUTRIENTSPEC2"}
    TALENT = {"PSYCHREQUEST", "talent_sm.pcx"}
    NUTRSITES = ["0x4ee501", "0x4ee859", "0x4eeb77", "0x4eeb96", "0x4eebd2", "0x4eebfc",
                 "0x4eec1b"]
    G["G3"] = (len(fam["FUN_004ee410"]) == 7 and len(fam["FUN_004f41f0"]) == 1
               and set(n1) == NUTR and set(n2) == TALENT and not (set(n1) & set(n2))
               and [hex(x) for x, _ in fam["FUN_004ee410"]] == NUTRSITES
               and [hex(x) for x, _ in fam["FUN_004f41f0"]] == ["0x4f46a9"]
               and EMITTER == 0x48F100)
    G["G4"] = (len(sites) == 3
               and [x[0] for x in arrrows] == [0x416F32, 0x417057, 0x41ADE4]
               and all(x[7] == "je" for x in arrrows)
               and [x[5] for x in arrrows] == [0x416F5E, 0x417083, 0x41AE17]
               and [x[6] for x in arrrows] == [0x416F59, 0x41707E, 0x41AE0D]
               and [x[8] for x in arrrows] == [8, 8, 8]
               and all(x[2] and "ds:0x8f0d60" in str(x[2]) for x in arrrows)
               and all(x[3] for x in arrrows)
               and all(x[4] == [0x78, 0x7C, 0x80] for x in arrrows)
               and all(x[9] == [] for x in arrrows))
    G["G5"] = (setter40 == [0x41AC34] and (0x40, 0x8) in pairs and (0x8, 0x40) in back
               and all(g in (REC, None) for _x, _mk, _b, _h, g in extract)
               and (len(recw), len(recok), len(foldw)) == (108, 59, 9))
    G["G6"] = (len(selfgate) == 1 and selfgate[0][0] == 0x4F43A0
               and selfgate[0][1] == "cl,0x40"
               and "mov ecx,DWORD PTR [eax+0x38]" in selfgate[0][2]
               and "ds:0x8f0d60" in selfgate[0][2] and other40 == [])
    G["G7"] = (len(idxst) == 6 and len(recst) == 6
               and all(len(d[1]) == 1 for d in dist) and len(sites) == 3)
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
