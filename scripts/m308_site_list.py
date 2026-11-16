#!/usr/bin/env python3
"""M308 (STATIC, zero box): what ARE FUN_0056d480 / FUN_0056d630 and ds:0x985b10 / ds:0x985aec?

The OPEN lead (NAMED.md ## M303 row S9, NEXT_PROMPT shortlist) asked for their identities.
This instrument decides them from the objdump dump (scratch/m574/text.txt), ghidra_out/index.csv
and the terran.exe bytes. It parses the ENCODING with one affine register engine (never the
Ghidra C text, which is written in ELEMENT units and misleads about the byte stride), prints the
tables first, then asserts every number it printed.

  S1  the block-offset multiply chain, evaluated symbolically -> byte stride, per function
  S2  every memory access of the two functions, classified stack / site-window / other, and the
      site-window field+width map
  S3  the loop bounds + steps in the family (the 25 x 0x10 site list vs the 75-entry sibling)
  S4  store census (630 writes nothing at all) and 630's 0/1 return
  S5  FUN_0056d480's found path = max() on the +2 short
  S6  its eviction law (empty slot scores 1000, else 20 - priority; ties keep the first index;
      no candidate -> return without inserting)
  S7  the (x^y) parity guard + ds:0x985ae8 bit 0x1000 + the "Bad SITE" string in the binary
  S8  caller census of both functions with the immediates each site pushes
  S9  ds:0x985b10: 544 refs, all direct (no array form), 12 byte writers, 96 register-bit tests,
        and one writer that REBUILDS the mask as OR(1 << BYTE[rec]) over 412-B records at 0x91e494
  S10 ds:0x985aec: 4 writers, 2 attributed to ds:0x92bde8 by a BACKWARD DEF-WALK (one load, one
        co-store), 1 closed on the setup byte ds:0x8f0c11 by the same walk, 1 declared unattributed,
        and comparisons only against 1/2/3/4

  The classifier sees BOTH bracketed and direct `ds:` operands (Greptile #281 P2a: the first version
  missed `mov eax,ds:0x985ae8`, so A4 claimed a clean window while the debug-flag read was invisible),
  the loop inventory comes from BACK-EDGES with an unfiltered immediate scan (P2b), and A9-A11 assert
  operand identity plus BRANCH TARGETS, not mnemonic presence (P2c).

  RIVALS that FAIL on the printed numbers: R1 0x985b10 is a per-faction ARRAY; R2 it is an
  accumulator; R3 its bits are set by read-modify-write on the global; R4 0x985aec is a counter;
  R5 the site-record stride is 0x82f = 2095 BYTES (what the decompiled C literally says);
  R6 the two functions are insert/probe twins (both write); R7 the parity guard can suppress the
  insert; R8 the site list grows past 25; R9 the 75-entry sibling is the same list; R10 the +0
  "kind" is the constant 3 that the M303 dispatch passes; R11 the def-walk is the old proximity
  test renamed.

    python3 scripts/m308_site_list.py        # stdout -> evidence/m308_site_list.txt
"""
import bisect
import csv
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")

INSN = re.compile(r"^\s+([0-9a-f]{6,8}):\t[0-9a-f ]{1,30}\t([a-z][a-z0-9]*)\s*(.*)$")
MEM = re.compile(r"^(DWORD|WORD|BYTE) PTR \[([^]]+)\]$")
DISP = re.compile(r"([+-])\s*0x([0-9a-f]+)\s*$")
TERM = re.compile(r"^(\w+)(?:\*(\d+))?$")
WRITES_DST = {"mov", "lea", "xor", "add", "sub", "shl", "shr", "and", "or", "movzx", "movsx",
              "inc", "dec", "neg", "not", "sete", "setne", "setg", "setge", "setl", "setle",
              "sbb", "cdq", "movbe", "xchg", "cmc", "sahf"}

SITE_BASE = 0x94F2D8
SITE_STRIDE = 0x10
SITE_COUNT = 0x19            # 25
RECORD_STRIDE = 0x20BC       # 8380 - asserted from the encoding, never assumed
SIB_BASE = 0x94EE28          # the 75-entry sibling list base, as indexed by FUN_0056d690
JCC = {"jo", "jno", "jb", "jae", "je", "jne", "jbe", "ja", "js", "jns", "jl", "jge", "jle",
       "jg", "jc", "jnc", "jz", "jnz", "ecxz"}
FUN_480 = (0x56D480, 0x56D5C4)
FUN_630 = (0x56D630, 0x56D686)
FUN_690 = (0x56D690, 0x56D710)


class Out:
    def __init__(self):
        self.lines = []

    def p(self, s=""):
        self.lines.append(s)
        print(s)
        sys.stdout.flush()


def parse_text():
    ins, order = {}, []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = INSN.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            ins[a] = (m.group(2), m.group(3).strip())
            order.append(a)
    return ins, order


def load_index():
    rows = []
    with open(INDEX) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["addr"], 16), r["name"]))
    rows.sort()
    return rows


def contain(fnrows, addr):
    i = bisect.bisect_right(fnrows, (addr, "\xff" * 8)) - 1
    return fnrows[i][1] if i >= 0 else "?"


def pe_sections(blob):
    e = struct.unpack_from("<I", blob, 0x3C)[0]
    opt = struct.unpack_from("<H", blob, e + 20)[0]
    ib = struct.unpack_from("<I", blob, e + 52)[0]
    secs = []
    for i in range(struct.unpack_from("<H", blob, e + 6)[0]):
        o = e + 24 + opt + i * 40
        nm = blob[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vsz, va, rsz, rp = struct.unpack_from("<IIII", blob, o + 8)
        secs.append((nm, ib + va, vsz, rsz, rp))
    return ib, secs


def va2off(secs, v):
    for nm, sv, vsz, rsz, rp in secs:
        if sv <= v < sv + max(vsz, rsz):
            if v - sv >= rsz:
                return None, nm + "(BSS)"
            return rp + (v - sv), nm
    return None, "?"


_ORDER = []
_INS = {}


def window(lo, hi):
    a = bisect.bisect_left(_ORDER, lo)
    b = bisect.bisect_right(_ORDER, hi - 1)
    return [(x, _INS[x][0], _INS[x][1]) for x in _ORDER[a:b]]


def split_ops(ops):
    return [x.strip() for x in ops.split(",")]


def dst_reg(mn, ops):
    """Which general register this instruction writes (None if not a tracked scalar write)."""
    if mn not in WRITES_DST:
        return None
    d = split_ops(ops)
    if not d:
        return None
    t = d[0]
    if t.startswith("BYTE PTR") or t.startswith("WORD PTR") or t.startswith("DWORD PTR"):
        return None
    if re.fullmatch(r"0x[0-9a-f]+", t):
        return None
    return t


def eval_expr(expr, val):
    """Affine form (B_coef, const) of a bracket/immediate expression; None if unknown."""
    k, c = 0, 0
    expr = expr.replace(" ", "")
    for term in re.split(r"(?=[+-])", expr):
        if not term:
            continue
        sgn = -1 if term[0] == "-" else 1
        t = term.lstrip("+-")
        sm = TERM.match(t)
        if not sm:
            return None, None
        name, scale = sm.group(1), int(sm.group(2) or 1)
        if re.fullmatch(r"0x[0-9a-f]+", name):
            c += sgn * scale * int(name, 16)
        elif name in val and val[name]:
            c += sgn * scale * val[name][1]
            k += sgn * scale * val[name][0]
        else:
            return None, None
    return k, c


def analyze(lo, hi):
    """One affine pass over [lo,hi):
       returns stride (first window-access base coefficient), accesses, traces, unresolved."""
    val, acc, traces, stride, bases = {}, [], [], None, []
    for a, mn, ops in window(lo, hi):
        d = split_ops(ops)
        v = None
        if mn == "xor" and len(d) == 2 and d[0] == d[1]:
            v = (0, 0)
        elif mn == "mov" and len(d) == 2:
            if re.fullmatch(r"0x[0-9a-f]+", d[1]):
                v = (0, int(d[1], 16))
            elif d[1] in val:
                v = val[d[1]]
            else:
                mm = MEM.match(d[1])
                # the callee's first argument (block index) is the affine symbol B
                if mm and mm.group(2) == "ebp+0x8":
                    v = (1, 0)
        elif mn == "shl" and len(d) == 2 and re.fullmatch(r"0x[0-9a-f]+", d[1]):
            p = val.get(d[0])
            v = (p[0] << int(d[1], 16), p[1] << int(d[1], 16)) if p else (None, None)
        elif mn in ("add", "sub") and len(d) == 2:
            p = val.get(d[0])
            if p:
                q = None
                if re.fullmatch(r"0x[0-9a-f]+", d[1]):
                    q = (0, int(d[1], 16))
                elif d[1] in val and val[d[1]]:
                    q = val[d[1]]
                if q:
                    s = 1 if mn == "add" else -1
                    v = (p[0] + s * q[0], p[1] + s * q[1])
        elif mn == "lea" and len(d) == 2:
            mm = MEM.match("DWORD PTR " + d[1]) or MEM.match(d[1])
            inner = d[1]
            m2 = re.match(r"^(?:\w+ PTR )?\[(.*)\]$", d[1])
            if m2:
                inner = m2.group(1)
            k, c = eval_expr(inner, val)
            v = (k, c)
        # --- classify memory accesses of THIS instruction (before the write is applied)
        for tok in d:
            m3 = MEM.match(tok)
            if not m3:
                # a DIRECT global operand (mov eax,ds:0x985ae8 / mov ds:0x985aec,eax) is still a
                # memory access - Greptile #281 P2a: classifying only bracketed forms hid the
                # debug-flag read inside FUN_0056d480
                m4 = re.match(r"^(DWORD|WORD|BYTE) PTR ds:(0x[0-9a-f]+)$", tok) or \
                    re.match(r"^ds:(0x[0-9a-f]+)$", tok)
                if m4:
                    g = int(m4.group(m4.lastindex), 16)
                    w = {"DWORD": "d", "WORD": "w", "BYTE": "b"}.get(
                        m4.group(1), "?" if mn in ("push", "lea", "add", "sub") else "d")
                    is_st = mn == "mov" and tok is d[0]
                    acc.append((a, mn, w, g, None, "ds:" + hex(g)[2:], "global", is_st))
                continue
            width = {"DWORD": "d", "WORD": "w", "BYTE": "b"}[m3.group(1)]
            raw = m3.group(2)
            k, c = eval_expr(raw, val)
            is_st = mn in ("mov", "movzx", "movbe", "xchg") and tok is d[0]
            kind = "stack" if ("ebp" in raw or "esp" in raw) else (
                "unresolved" if c is None else
                ("site" if SITE_BASE <= c <= SITE_BASE + 0xC else "other"))
            acc.append((a, mn, width, c, k, raw, kind, is_st))
            if kind == "site" and stride is None and not is_st and k:
                stride = k
                traces.append((hex(a), ops, k, c))
        r = dst_reg(mn, ops)
        if r is not None:
            val[r] = v
        if mn == "push":
            mm = re.match(r"^(?:\w+ PTR )?\[(\w+)", d[0]) if d else None
    return stride, acc, traces


REG_ALIAS = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx", "bx": "ebx",
             "cl": "ecx", "ch": "ecx", "cx": "ecx", "dl": "edx", "dh": "edx", "dx": "edx",
             "si": "esi", "di": "edi", "sp": "esp", "bp": "ebp"}


def reg_norm(name):
    """Sub-register -> 32-bit owner, so a def of AL cannot walk past as if it did not touch EAX
    (Greptile #281 P2d: a def-walk that compares register NAMES literally is unsound)."""
    n = name.strip().lower()
    return REG_ALIAS.get(n, n)


def writes_what(mn, ops):
    """What an instruction defines: ('reg', name) / ('mem', addr) / None. dst_reg() keeps the
    register case; this adds the memory destination so a def-walk cannot be fooled by a store."""
    if mn not in WRITES_DST:
        return None
    d = split_ops(ops)
    if not d:
        return None
    t = d[0]
    if re.fullmatch(r"0x[0-9a-f]+", t):
        return None
    if t.startswith(("[", "fs:", "ds:")) or t.startswith(("BYTE PTR", "WORD PTR", "DWORD PTR")) \
            or "PTR" in t:
        a = re.search(r"0x[0-9a-f]+", t)
        return ("mem", int(a.group(0), 16)) if a else ("mem", None)
    if re.fullmatch(r"[a-z][a-z0-9]*", t):
        return ("reg", reg_norm(t))
    return None


def def_producer(addr, reg, lo, hi):
    """Walk back from `addr` (exclusive) inside [lo,hi) to the instruction that last DEFINED `reg`
    (sub-registers normalized), collecting every instruction crossed. Stops at a call (volatile
    kill) or the window edge. Returns ((kind, (a, mn, ops)) | None, [crossed...])."""
    reg = reg_norm(reg)
    i = bisect.bisect_left(_ORDER, addr)
    crossed = []
    while i > 0:
        i -= 1
        a = _ORDER[i]
        mn, ops = _INS[a]
        if a < lo:
            break
        if writes_what(mn, ops) == ("reg", reg):
            return ("found", (a, mn, ops)), crossed
        crossed.append((a, mn, ops))
        if mn == "call":                       # a call redefines the volatile registers
            return ("kill", (a, mn, ops)), crossed
    return None, crossed


def def_globals(addr, reg, lo, hi, seen=None, depth=0):
    """Transitive def-walk over the value held in `reg` at `addr`: follow producer instructions
    until the value's source is a global (returned as that address), a register copy (recurse), a
    call/edge (the chain cannot be closed -> 'kill'/'edge'), or an arithmetic/other definition
    ('other'). Returns (sources, chain) where chain is every instruction crossed, newest first."""
    seen = seen if seen is not None else set()
    key = (addr, reg_norm(reg))
    if key in seen or depth > 12:
        return {"cycle"}, []
    seen.add(key)
    prod, crossed = def_producer(addr, reg, lo, hi)
    if prod is None:
        return {"edge"}, crossed
    kind, pin = prod
    if kind == "kill":
        return {"kill"}, crossed + [pin]
    a, mn, ops = pin
    crossed = crossed + [pin]
    d = split_ops(ops)
    if not d or reg_norm(d[0]) != reg_norm(reg):
        return {"other"}, crossed
    srcs = d[1:]
    if mn == "xor" and len(srcs) == 1 and reg_norm(srcs[0]) == reg_norm(reg):
        return {"zero"}, crossed
    for tok in srcs:                                  # a global operand settles the question
        if tok.startswith(("ds:", "fs:")) or ("PTR" in tok and "ds:" in tok):
            m = re.search(r"(?:fs:|ds:)(0x[0-9a-f]+)", tok)
            if m:
                return {int(m.group(1), 16)}, crossed
    if len(srcs) == 1 and re.fullmatch(r"[a-z][a-z0-9]*", srcs[0]):
        out, deeper = def_globals(a, srcs[0], lo, hi, seen, depth + 1)
        return out, crossed + deeper
    return {"other"}, crossed


def load_spans():
    rows = []
    with open(INDEX) as f:
        for r in csv.DictReader(f):
            a = int(r["addr"], 16)
            rows.append((a, a + int(r["size_bytes"]), r["name"]))
    rows.sort()
    return rows


_SPANS = []


def span_of(addr):
    """(lo, hi, name) of the function containing `addr`, from ghidra_out/index.csv sizes."""
    i = bisect.bisect_right(_SPANS, (addr, float("inf"), "~")) - 1
    if i >= 0 and _SPANS[i][0] <= addr < _SPANS[i][1]:
        return _SPANS[i][0], _SPANS[i][1], _SPANS[i][2]
    return addr - 0x200, addr + 0x40, "?"


def main():
    out = Out()
    global _INS, _ORDER, _SPANS
    _INS, _ORDER = parse_text()
    _SPANS = load_spans()
    ins = _INS
    fnrows = load_index()
    out.p("M308 static instrument: .text insns parsed %d, functions %d"
          % (len(_INS), len(fnrows)))

    # ---------------- S1 stride from the encoding
    s480, acc480, t480 = analyze(*FUN_480)
    s630, acc630, t630 = analyze(*FUN_630)
    out.p("\n[S1] block-offset chain (symbolic; B = the function's first argument)")
    for tag, lo, hi in (("0x56d480", *FUN_480), ("0x56d630", *FUN_630)):
        for a, m, o in window(lo, min(hi, lo + 0x52)):
            out.p("   %s %s\t%-6s %s" % (tag, a, m, o))
        out.p("   -> %s" % "")
    out.p("   stride(FUN_0056d480)=%s   stride(FUN_0056d630)=%s" % (s480, s630))
    out.p("   (Ghidra C prints `param_1 * 0x82f` in ELEMENT units: 0x82f * 4 = %d)"
          % (0x82F * 4))

    # ---------------- S2 access classification
    out.p("\n[S2] memory accesses of the two functions, normalized to record base 0x%x" % SITE_BASE)
    fmap = {}
    for tag, accs in (("480", acc480), ("630", acc630)):
        seen, other, unst = {}, [], []
        for a, mn, w, c, k, raw, kind, is_st in accs:
            if kind == "site":
                seen.setdefault((c - SITE_BASE, w, "W" if is_st else "R"), []).append(
                    "%s@%s" % (mn, hex(a)))
            elif kind == "other":
                other.append("%s %s [%s] @%s" % (mn, w, raw, hex(a)))
            elif kind == "unresolved":
                unst.append("%s %s [%s] @%s" % (mn, w, raw, hex(a)))
        for key in sorted(seen):
            out.p("   %s field +0x%-2x %-1s %s x%d e.g. %s"
                  % (tag, key[0], key[1], key[2], len(seen[key]), seen[key][0]))
        glist = sorted({g for _, _mn, _w, g, _, raw, k, _s in accs if k == "global"})
        out.p("   %s 'other' (not stack, not site window): %d %s" % (tag, len(other), other[:3]))
        out.p("   %s unresolved (base not tracked): %d %s" % (tag, len(unst), unst[:3]))
        out.p("   %s DIRECT-GLOBAL accesses (not bracketed, still memory): %d %s"
              % (tag, len(glist), [hex(x) for x in glist]))
        fmap[tag] = {key for key in seen}
    out.p("   site READ map   480=%s  630=%s"
          % (sorted({(f, w) for f, w, r in fmap["480"] if r == "R"}),
             sorted({(f, w) for f, w, r in fmap["630"] if r == "R"})))
    out.p("   site WRITE map  480=%s  630=%s"
          % (sorted({(f, w) for f, w, r in fmap["480"] if r == "W"}),
             sorted({(f, w) for f, w, r in fmap["630"] if r == "W"})))

    # ---------------- S3 loop bounds and steps
    out.p("\n[S3] loop inventory from BACK-EDGES (a jcc whose target is at or below itself inside "
          "the function); bounds/steps are every immediate inside the body, NOT pre-filtered")

    def backedges(lo, hi):
        """Every backward jcc in [lo,hi): its head/tail, the trip bound feeding it, the adds/subs
        inside the body, the counters it decs/incs and where those counters were initialised."""
        rows = []
        for a, m, o in window(lo, hi):
            if m not in JCC:
                continue
            mt = re.fullmatch(r"0x([0-9a-f]+)", o.strip())
            if not mt:
                continue
            t = int(mt.group(1), 16)
            if not (lo <= t <= a):
                continue
            body = window(t, a + 1)
            bounds = sorted({int(x.split(",")[-1].strip(), 16) for _, mm, x in body
                             if mm == "cmp" and re.search(r",\s*0x[0-9a-f]+$", x)})
            steps = sorted({int(x.split(",")[-1].strip(), 16) for _, mm, x in body
                            if mm in ("add", "sub") and re.search(r",\s*0x[0-9a-f]+$", x)})
            ctr = sorted({reg_norm(x.split()[0]) for _, mm, x in body
                          if mm in ("dec", "inc") and x.strip()})
            inits = sorted({int(x.split(",")[-1].strip(), 16) for _, mm, x in window(lo, t)
                            if mm == "mov" and x.strip() and reg_norm(x.split(",")[0]) in ctr
                            and re.fullmatch(r"0x[0-9a-f]+", x.split(",")[-1].strip())})
            i = bisect.bisect_left(_ORDER, a)
            prev = _INS[_ORDER[i - 1]] if i else ("", "")
            pair = None
            if prev[0] == "cmp":
                mp = re.search(r",\s*0x([0-9a-f]+)$", prev[1])
                pair = int(mp.group(1), 16) if mp else None
            rows.append({"head": t, "tail": a, "jcc": m, "bounds": bounds, "steps": steps,
                         "counters": ctr, "counter_inits": inits, "cmp_pair": pair,
                         "n_body": len(body)})
        return rows

    def imm_inventory(lo, hi):
        """EVERY immediate that appears anywhere in [lo,hi) - nothing is pre-filtered, so an
        unexpected loop bound or step cannot hide from A12/A13 (Greptile #281 P2b)."""
        allim, cmpim, addim, addim_nostack = set(), set(), set(), set()
        for _a, m, o in window(lo, hi):
            for tok in split_ops(o):
                tok = tok.strip()
                mt = re.fullmatch(r"0x([0-9a-f]+)", tok)
                if mt:
                    allim.add(int(mt.group(1), 16))
            if m == "cmp" and re.search(r",\s*0x[0-9a-f]+$", o):
                cmpim.add(int(o.split(",")[-1].strip(), 16))
            if m in ("add", "sub") and re.search(r",\s*0x[0-9a-f]+$", o):
                v = int(o.split(",")[-1].strip(), 16)
                addim.add(v)
                if reg_norm(o.split(",")[0]) not in ("esp", "ebp"):
                    addim_nostack.add(v)
        return {"all": sorted(allim), "cmp": sorted(cmpim), "addsub": sorted(addim),
                "addsub_nostack": sorted(addim_nostack)}

    loops, inv = {}, {}
    for lo, hi, nm in ((FUN_480[0], FUN_480[1], "0x56d480"),
                       (FUN_630[0], FUN_630[1], "0x56d630"),
                       (FUN_690[0], FUN_690[1], "0x56d690")):
        be = backedges(lo, hi)
        loops[nm] = be
        inv[nm] = imm_inventory(lo, hi)
        out.p("   %-10s %d back-edge(s) | EVERY immediate in the function: %s"
              % (nm, len(be), [hex(x) for x in inv[nm]["all"]]))
        out.p("                | cmp-immediates=%s add/sub-immediates=%s (non-stack)=%s"
              % ([hex(x) for x in inv[nm]["cmp"]], [hex(x) for x in inv[nm]["addsub"]],
                 [hex(x) for x in inv[nm]["addsub_nostack"]]))
        for r in be:
            out.p("      head %s <- %-4s tail %s body=%d insns  trip-cmp=%s bounds-in-body=%s "
                  "steps-in-body=%s counters=%s counter-init=%s"
                  % (hex(r["head"]), r["jcc"], hex(r["tail"]), r["n_body"],
                     r["cmp_pair"] and hex(r["cmp_pair"]), [hex(x) for x in r["bounds"]],
                     [hex(x) for x in r["steps"]], r["counters"],
                     [hex(x) for x in r["counter_inits"]]))

    # ---------------- S4 stores / return values
    out.p("\n[S4] store census")
    st = {}
    for nm, lo, hi in (("480", *FUN_480), ("630", *FUN_630), ("690", *FUN_690)):
        rows = ["%s %s %s" % (hex(a), m, o) for a, m, o in window(lo, hi)
                if m == "mov" and re.match(r"^(DWORD|WORD|BYTE) PTR \[", o)]
        st[nm] = rows
        out.p("   FUN_0056d%s: %d stores" % (nm, len(rows)))
        for r in rows:
            out.p("      %s" % r)
    epilogue630 = [(a, m, o) for a, m, o in window(*FUN_630) if a >= 0x56D674]
    rets630 = ["%s %s" % (m, o) for a, m, o in epilogue630
               if (m == "mov" and o.startswith("eax,")) or m == "xor"]
    out.p("   FUN_0056d630 epilogue ops that set eax: %s" % rets630)

    found = [(a, m, o) for a, m, o in window(*FUN_480) if 0x56D59F <= a <= 0x56D5C3]
    out.p("\n[S5] found-path block 0x56d59f-0x56d5c3, decomposed as a RULE (operands + targets)")

    def succ(addr):
        i = bisect.bisect_left(_ORDER, addr)
        return _ORDER[i + 1] if i + 1 < len(_ORDER) else None

    # (1) the +2 field is read SIGNED, (2) compared with the incoming priority, (3) a jcc whose
    # target is the instruction right AFTER the fallback move (that is what makes it a max, not a
    # plain store), (4) the winner is stored back as a WORD to the same address expression.
    # NOTE the regexes match the OPERAND string only - the mnemonic is the separate field `m`.
    lds = next(((a, m, o, re.match(r"(\w+),WORD PTR \[([^]]+)\]$", o.strip()))
                for a, m, o in found if m == "movsx" and "WORD PTR" in o),
               (None, None, None, None))
    lo_field = (int(re.search(r"0x([0-9a-f]+)$", lds[3].group(2).strip()).group(1), 16)
                - SITE_BASE) if lds[3] and re.search(r"0x([0-9a-f]+)$", lds[3].group(2)) else None
    cmpi = next(((a, m, o, re.match(r"(\w+),(\w+)$", o.strip()))
                 for a, m, o in found if m == "cmp" and re.fullmatch(r"\w+,\w+", o.strip())),
                (None, None, None, None))
    jc1 = next(((a, m, o) for a, m, o in found if m in JCC), (None, None, None))
    fbk = next(((a, m, o) for a, m, o in found
                if m == "mov" and cmpi[3] and o.strip().lower() == "%s,%s"
                % (cmpi[3].group(1), cmpi[3].group(2))), (None, None, None))
    sto = next(((a, m, o, re.match(r"WORD PTR \[(\w+)\],(\w+)$", o.strip()))
                for a, m, o in found if m == "mov" and o.strip().startswith("WORD PTR [")),
               (None, None, None, None))
    def def_operand(addr, reg):
        """The SOURCE OPERAND of the instruction that last wrote `reg` before `addr` (def-walk),
        or None if the chain cannot be closed inside FUN_0056d480. Register aliasing is resolved,
        so a producer through a sub-register or a copy is still named."""
        prod, _ch = def_producer(addr, reg, *FUN_480)
        if not prod or prod[0] != "found":
            return None
        _pa, pm, po = prod[1]
        d = split_ops(po)
        return "%s %s" % (pm, d[1]) if len(d) > 1 else None

    maxlaw = {
        "read": lds[0] and "%s %s" % (hex(lds[0]), lds[2]),
        "read_dst": lds[3] and reg_norm(lds[3].group(1)),
        "read_field_off": lo_field,
        "cmp": cmpi[0] and "%s %s" % (hex(cmpi[0]), cmpi[2]),
        "cmp_lhs_is_the_signed_read": bool(lds[3] and cmpi[3] and
                                           reg_norm(cmpi[3].group(1)) == reg_norm(lds[3].group(1))),
        "jcc": "%s %s @%s" % (jc1[1], jc1[2], hex(jc1[0])) if jc1[0] else None,
        "jcc_is_jg": jc1[1] == "jg",
        "fallback": "%s %s @%s" % (fbk[1], fbk[2], hex(fbk[0])) if fbk[0] else None,
        "jg_target_is_just_past_fallback": bool(jc1[0] and fbk[0] and
                                                int(jc1[2].strip(), 16) == succ(fbk[0])),
        "store": sto[0] and "%s %s" % (hex(sto[0]), sto[2]),
        "store_is_cmp_lhs_low_half": bool(sto[3] and cmpi[3] and
                                          reg_norm(sto[3].group(2)) == reg_norm(cmpi[3].group(1))),
        "cmp_lhs_producer": cmpi[0] and cmpi[3] and def_operand(cmpi[0], cmpi[3].group(1)),
        "cmp_rhs_producer": cmpi[0] and cmpi[3] and def_operand(cmpi[0], cmpi[3].group(2)),
        "cmp_rhs_is_the_prio_argument": bool(cmpi[3] and
                                             (def_operand(cmpi[0], cmpi[3].group(2)) or "")
                                             .endswith("DWORD PTR [ebp+0x10]")),
    }
    for k in ("read", "cmp", "jcc", "fallback", "store"):
        out.p("   %-24s %s" % (k, maxlaw[k]))
    for k in ("read_field_off", "cmp_lhs_is_the_signed_read", "jcc_is_jg",
              "jg_target_is_just_past_fallback", "store_is_cmp_lhs_low_half", "cmp_lhs_producer",
              "cmp_rhs_producer", "cmp_rhs_is_the_prio_argument"):
        out.p("   %-24s %s" % (k, maxlaw[k]))

    evict = [(a, m, o) for a, m, o in window(*FUN_480) if 0x56D4FB <= a <= 0x56D541]
    out.p("\n[S6] eviction block 0x56d4fb-0x56d541, decomposed as RULES")

    def mem_field(token):
        """('reg', delta) inside a '[reg+-d]' operand, or None."""
        mm = re.fullmatch(r"(?:\w+ PTR )?\[(\w+)([+-]0x[0-9a-f]+)?\]", token.strip())
        if not mm:
            return None
        return reg_norm(mm.group(1)), int(mm.group(2).replace("0x", ""), 16) if mm.group(2) else 0

    # the loop pointer: `lea edx,[ebx+0x94f2da]` -> record base SITE_BASE + 2, walked by 0x10
    pt_lea = next(((a, m, o, re.match(r"(\w+),\[(\w+)\+0x([0-9a-f]+)\]$", o.strip()))
                   for a, m, o in window(*FUN_480)
                   if m == "lea" and re.fullmatch(r"\w+,\[\w+\+0x94f2da\]", o.strip())),
                  (None, None, None, None))
    ptr_reg = pt_lea[3] and reg_norm(pt_lea[3].group(1))
    ptr_base_off = (int(pt_lea[3].group(3), 16) - SITE_BASE) if pt_lea[3] else None

    def field_of(token):
        mf = mem_field(token)
        if not mf or not pt_lea[3] or mf[0] != ptr_reg:
            return None
        return ptr_base_off + mf[1]

    kind_ld = next(((a, m, o, re.match(r"(\w+),WORD PTR (\[.*\])$", o.strip()))
                    for a, m, o in evict if m == "mov" and "WORD PTR [" in o
                    and field_of(o.split(",", 1)[1]) == 0), (None, None, None, None))
    test1 = next(((a, m, o) for a, m, o in evict
                  if m == "test" and kind_ld[3] and o.strip().lower() == "%s,%s"
                  % (kind_ld[3].group(1), kind_ld[3].group(1))), (None, None, None))
    jl_free = next(((a, m, o) for a, m, o in evict if m == "jl" and test1[0] and a > test1[0]),
                   (None, None, None))
    pri_cmp = next(((a, m, o) for a, m, o in evict
                    if m == "cmp" and re.fullmatch(r"\w+,DWORD PTR \[ebp\+0x10\]", o.strip())),
                   (None, None, None))
    jge_skip = next(((a, m, o) for a, m, o in evict if m == "jge" and pri_cmp[0] and
                     a > pri_cmp[0]), (None, None, None))
    # the 1000 arm is a conditional select: xor / test(kind) / setge / dec / and 0x3e8 on ONE reg
    sel = [x for x in evict if x[1] in ("xor", "test", "setge", "dec", "and")]
    and1000 = next(((a, m, o) for a, m, o in sel if m == "and" and o.strip().endswith(",0x3e8")),
                   (None, None, None))
    setge_r = next(((a, m, o, re.match(r"(\w+)$", o.strip()))
                    for a, m, o in sel if m == "setge"), (None, None, None, None))
    dec_r = next(((a, m, o, re.match(r"(\w+)$", o.strip()))
                  for a, m, o in sel if m == "dec"), (None, None, None, None))
    jne_20 = next(((a, m, o) for a, m, o in evict if m == "jne" and and1000[0] and
                   a > and1000[0]), (None, None, None))
    # the 20-priority arm: mov reg,0x14 then sub reg,<prio reg>, prio read from the +2 field
    mov20 = next(((a, m, o, re.match(r"(\w+),0x14$", o.strip()))
                  for a, m, o in evict if m == "mov" and o.strip().endswith(",0x14")),
                 (None, None, None, None))
    sub20 = next(((a, m, o, re.match(r"(\w+),(\w+)$", o.strip()))
                  for a, m, o in evict if m == "sub" and re.fullmatch(r"\w+,\w+", o.strip())),
                 (None, None, None, None))
    pri_ld = next(((a, m, o, re.match(r"(\w+),WORD PTR (\[.*\])$", o.strip()))
                   for a, m, o in evict if m == "movsx" and field_of(o.split(",", 1)[1]) == 2),
                  (None, None, None, None))
    # the running best is held in [ebp-0x4]; the update must be guarded by a STRICT jle
    best_cmp = next(((a, m, o) for a, m, o in evict if m == "cmp" and "[ebp-0x4]" in o),
                    (None, None, None))
    strict = next(((a, m, o) for a, m, o in evict if m in JCC and best_cmp[0] and
                   a > best_cmp[0] and re.fullmatch(r"0x[0-9a-f]+", o.strip())),
                  (None, None, None))
    tgt = int(strict[2].strip(), 16) if strict[0] else None
    upd = [(a, m, o) for a, m, o in evict
           if m == "mov" and best_cmp[0] and strict[0] and best_cmp[0] < a < tgt]
    evlaw = {
        "loop_ptr": "%s %s @%s -> record base +0x%x" % (pt_lea[1], pt_lea[2], hex(pt_lea[0]),
                                                        ptr_base_off) if pt_lea[0] else None,
        "kind_read": "%s %s @%s" % (kind_ld[1], kind_ld[2], hex(kind_ld[0])) if kind_ld[0] else None,
        "kind_read_field_off": field_of(kind_ld[2].split(",", 1)[1]) if kind_ld[3] else None,
        "prio_read": "%s %s @%s" % (pri_ld[1], pri_ld[2], hex(pri_ld[0])) if pri_ld[0] else None,
        "prio_read_field_off": field_of(pri_ld[2].split(",", 1)[1]) if pri_ld[3] else None,
        "free_slot_jl_skips_the_prio_cmp": bool(test1[0] and jl_free[0] and pri_cmp[0] and
                                                pri_cmp[0] < int(jl_free[2].strip(), 16) <=
                                                (and1000[0] or 0)),
        "1000_select_chain": " / ".join("%s %s" % (m, o) for _a, m, o in sel),
        "1000_is_and_on_the_setge_dec_reg": bool(and1000[0] and setge_r[3] and dec_r[3] and
                                                 reg_norm(dec_r[3].group(1)) ==
                                                 reg_norm(setge_r[3].group(1)) and
                                                 and1000[2].strip().lower().startswith(
                                                     dec_r[3].group(1).lower())),
        "setge_is_fed_by_the_kind_test": bool(
            setge_r[0] and any(x[1] == "test" and succ(x[0]) == setge_r[0] and kind_ld[3]
                               and x[2].strip().lower() == "%s,%s"
                               % (kind_ld[3].group(1), kind_ld[3].group(1)) for x in sel)),
        "free_slot_score_skips_20minus": bool(jne_20[0] and sub20[0] and
                                              int(jne_20[2].strip(), 16) > sub20[0]),
        "prio_score_20_minus": "%s ; %s" % (mov20[2], sub20[2]) if mov20[0] and sub20[0] else None,
        "20_and_sub_share_one_reg": bool(mov20[3] and sub20[3] and
                                         reg_norm(mov20[3].group(1)) == reg_norm(sub20[3].group(1))),
        "subtrahend_is_the_signed_prio": bool(sub20[3] and pri_ld[3] and
                                              reg_norm(sub20[3].group(2)) ==
                                              reg_norm(pri_ld[3].group(1))),
        "prio_cmp_lhs_def": pri_cmp[0] and def_operand(pri_cmp[0], split_ops(pri_cmp[2])[0]),
        "sub20_subtrahend_def": sub20[0] and def_operand(sub20[0], sub20[3].group(2)),
        "prio_cmp_lhs_is_signed_prio_field": bool(pri_cmp[0] and
                                                  (def_operand(pri_cmp[0],
                                                               split_ops(pri_cmp[2])[0]) or "")
                                                  .startswith("movsx WORD PTR")),
        "sub20_subtrahend_is_signed_prio_field": bool(
            sub20[0] and (def_operand(sub20[0], sub20[3].group(2)) or "")
            .startswith("movsx WORD PTR")),
        "already_beaten_slot_jumps_to_increment": bool(pri_cmp[0] and jge_skip[0] and tgt and
                                                       int(jge_skip[2].strip(), 16) == tgt),
        "strict_jcc": "%s %s @%s" % (strict[1], strict[2], hex(strict[0])) if strict[0] else None,
        "strict_is_jle_not_jl": strict[1] == "jle",
        "tie_skips_both_updates": bool(strict[0]) and len(upd) == 2 and
        all(x[0] < tgt for x in upd) and succ(upd[-1][0]) == tgt,
        "updates_between_jle_and_target": [hex(x) for x, _m, _o in upd],
    }
    for k in sorted(evlaw):
        out.p("   %-34s %s" % (k, evlaw[k]))
    # no-candidate path: test reg,reg then a jl that lands on a STORE-FREE epilogue, skipping the
    # whole insert body. Judged on the run from the target to its own `ret`, not on the found path
    # (which is entered from the scan loop by a different branch and does store).
    noc_test = next(((a, m, o) for a, m, o in window(*FUN_480)
                     if m == "test" and re.fullmatch(r"(\w+),\1", o.strip())
                     and o.strip().startswith("ecx")), (None, None, None))
    noc_jl = next(((a, m, o) for a, m, o in window(*FUN_480)
                   if m == "jl" and noc_test[0] and a > noc_test[0]), (None, None, None))
    site_stores = sorted({a for a, _mn, _w, _c, _k, _raw, kind, is_st in acc480
                          if is_st and kind == "site"})
    tgt_nc = int(noc_jl[2].strip(), 16) if noc_jl[0] else None
    epi_run = []
    if tgt_nc is not None:
        for a, m, o in window(tgt_nc, FUN_480[1]):
            epi_run.append((a, m, o))
            if m == "ret":
                break
    stores_in_epi = [(hex(x), ops) for x, mn, ops in epi_run
                     if mn == "mov" and ops.strip().startswith(
                         ("DWORD PTR", "WORD PTR", "BYTE PTR"))]
    noc = {
        "test": "%s %s @%s" % (noc_test[1], noc_test[2], hex(noc_test[0])) if noc_test[0] else None,
        "jl": "%s %s @%s" % (noc_jl[1], noc_jl[2], hex(noc_jl[0])) if noc_jl[0] else None,
        "jl_target": tgt_nc,
        "target_insn": "%s %s" % (_INS[tgt_nc][0], _INS[tgt_nc][1]) if tgt_nc else None,
        "epilogue_to_ret": ["%s %s" % (m, o.strip()) for _a, m, _o in epi_run],
        "stores_on_the_taken_path": stores_in_epi,
        "insert_stores_skipped": [hex(x) for x in site_stores
                                  if noc_jl[0] and noc_jl[0] < x < tgt_nc],
    }
    out.p("\n[S6b] no-candidate path")
    for k in sorted(noc):
        out.p("   %-24s %s" % (k, noc[k]))
    out.p("   every site store in FUN_0056d480: %s" % [hex(x) for x in site_stores])

    guard = [(a, m, o) for a, m, o in window(*FUN_480) if a <= 0x56D4B7]
    out.p("\n[S7] parity/debug guard head")
    for a, m, o in guard[:14]:
        out.p("   %s\t%-6s %s" % (hex(a), m, o))
    blob = open(EXE, "rb").read()
    ib, secs = pe_sections(blob)

    def rd(v, n):
        o, sec = va2off(secs, v)
        return (blob[o:o + n].split(b"\0")[0].decode("ascii", "replace"), sec, o) if o \
            else (None, sec, o)

    smsg, secmsg, offmsg = rd(0x691508, 32)
    sfmt, secfmt, offfmt = rd(0x673850, 48)
    out.p("   0x691508 [%s off %s] = %r" % (secmsg, offmsg and hex(offmsg), smsg))
    out.p("   0x673850 [%s off %s] = %r raw16=%r"
          % (secfmt, offfmt and hex(offfmt), sfmt,
             blob[offfmt:offfmt + 16] if offfmt else None))

    # ---------------- S8 caller census
    out.p("\n[S8] caller census (immediates walked back over the push sequence)")
    calls = {}
    for tgt in (0x56D480, 0x56D630):
        sites = [a for a in _ORDER if ins[a][0] == "call" and ins[a][1] == "0x%x" % tgt]
        rows = []
        for s in sites:
            push, a = [], s
            for _ in range(48):
                i = bisect.bisect_left(_ORDER, a) - 1
                if i < 0:
                    break
                a = _ORDER[i]
                mn, o = ins[a]
                if mn != "push":
                    break          # only the contiguous push run is the argument list
                push.append(o)
                if len(push) >= 8:
                    break
            rows.append((hex(s), contain(fnrows, s), len(push), list(reversed(push))))
        calls[tgt] = rows
        for r in rows:
            out.p("   0x%x -> %-12s site %s pushes=%d %s" % (tgt, r[1], r[0], r[2], r[3]))

    # ---------------- S9/S10 the two globals
    def census(addr):
        pat = "0x%x" % addr
        refs = [(a, ins[a][0], ins[a][1]) for a in _ORDER if pat in ins[a][1]]
        forms = {}
        for _, mn, _o in refs:
            forms[mn] = forms.get(mn, 0) + 1
        indexed = [hex(a) for a, mn, o in refs if "[" in o and pat in o and mn != "lea"]
        direct = [r for r in refs if "ds:" + pat in r[2]]
        wr = [r for r in refs if r[1] == "mov"
              and re.match(r"^(?:(DWORD|WORD|BYTE) PTR )?ds:", r[2])]
        cmpimm = sorted({int(o.split(",")[-1].strip(), 16) for _, mn, o in refs
                         if mn == "cmp" and re.search(r",0x[0-9a-f]+$", o)})
        return refs, forms, indexed, direct, wr, cmpimm

    out.p("\n[S9] ds:0x985b10 census")
    r10, f10, i10, d10, w10, c10 = census(0x985B10)
    out.p("   refs=%d forms=%s" % (len(r10), sorted(f10.items(), key=lambda x: (-x[1], x[0]))))
    out.p("   array-form (indexed) accesses=%d %s   direct ds: refs=%d   byte writers=%d"
          % (len(i10), i10[:4], len(d10), len(w10)))
    for a, mn, o in w10:
        out.p("      W %s\t%-6s %s" % (hex(a), mn, o))
    reb = [(a, m, o) for a, m, o in window(0x57F040, 0x57F075)]
    out.p("   the rebuild writer, 0x57f040-0x57f075:")
    for a, m, o in reb:
        out.p("   %s\t%-6s %s" % (hex(a), m, o))

    out.p("\n[S10] ds:0x985aec census")
    rec, fec, iec, dec, wec, cec = census(0x985AEC)
    out.p("   refs=%d forms=%s" % (len(rec), sorted(fec.items(), key=lambda x: (-x[1], x[0]))))
    out.p("   array-form=%d direct ds: refs=%d writers=%d cmp-immediates=%s"
          % (len(iec), len(dec), len(wec), [hex(x) for x in cec]))

    def around(addr, before=10, after=1):
        i = bisect.bisect_left(_ORDER, addr)
        return [(x, ins[x][0], ins[x][1])
                for x in _ORDER[max(0, i - before):min(len(_ORDER), i + after + 1)]]

    out.p("\n[S10b] the 4 writers of ds:0x985aec, attributed by BACKWARD DEF-WALK (not proximity)")
    out.p("        Greptile #281 P2d: the previous version accepted any 0x92bde8/0x8f0c11 token")
    out.p("        within 10 instructions, which an intervening write to the value register would")
    out.p("        not have broken. proximity_ok is kept in the table ONLY to show it disagrees.")
    mirror = {}
    for a, mn, o in wec:
        d = split_ops(o)
        src_reg = d[-1] if len(d) > 1 else None
        lo, hi, fname = span_of(a)
        srcs, chain = def_globals(a, src_reg, lo, hi) if src_reg else ({"unparsed"}, [])
        co = [x for x, _m2, o2 in chain
              if o2.strip().lower().startswith("ds:0x92bde8,") and len(split_ops(o2)) > 1
              and reg_norm(split_ops(o2)[-1]) == reg_norm(src_reg)]
        near = [x[2] for x in around(a)]
        win = around(a)
        p92 = any("0x92bde8" in x for x in near)
        p8f = any("0x8f0c11" in x for x in near)
        # what the OLD proximity rule would have credited this writer with, in full
        prox_globals = sorted({int(mm.group(1), 16) for o2 in near
                               for mm in [re.search(r"ds:(0x[0-9a-f]{6,8})", o2)] if mm})
        if srcs == {0x92BDE8}:
            kind = "DEF-WALK: loads ds:0x92bde8 (%s) crossing %d insn" % (
                [hex(x) for x in srcs], len(chain))
        elif co:
            kind = "DEF-WALK: co-store, the same %s is stored to ds:0x92bde8 at %s with no " \
                   "write to %s in between" % (src_reg, hex(co[0]), src_reg)
        elif srcs == {0x8F0C11}:
            kind = "DEF-WALK: loads ds:0x8f0c11 (the setup byte) crossing %d insn" % len(chain)
        else:
            prev_i = bisect.bisect_left(_ORDER, a) - 1
            boundary = _INS[_ORDER[prev_i]][0] if prev_i >= 0 else "?"
            kind = "UNRESOLVED in-function (chain=%s, previous dumped insn is `%s` -> the value " \
                   "arrives from outside this walk)" % (sorted(map(str, srcs)), boundary)
        mirror[hex(a)] = {"kind": kind, "srcs": sorted(map(str, srcs)), "chain": len(chain),
                          "fn": fname, "prox": [hex(x) for x in prox_globals],
                          "prox92": p92, "prox8f": p8f}
        out.p("   W %s %-6s %-24s | %s" % (hex(a), mn, o, kind))
        for x, m2, o2 in chain[:5]:
            out.p("       walked %s %-6s %s" % (hex(x), m2, o2))
        out.p("       (proximity would credit these ds-globals in the window: %s)" % mirror[
            hex(a)]["prox"])

    # ---------------- the asserts
    chk = []

    def ok(name, cond, detail=""):
        chk.append((name, bool(cond), detail))

    readmap = lambda tag: {(f, w) for f, w, r in fmap[tag] if r == "R"}
    writemap = lambda tag: {(f, w) for f, w, r in fmap[tag] if r == "W"}
    others = [(mn, raw) for _, mn, _, _, _, raw, kind, _ in acc480 + acc630 if kind == "other"]

    ok("A1 FUN_0056d480 block stride == 8380 (from the encoding)",
       s480 == RECORD_STRIDE, "got %s" % s480)
    ok("A2 FUN_0056d630 block stride == 8380 (from the encoding)",
       s630 == RECORD_STRIDE, "got %s" % s630)
    ok("A3 RIVAL R5 (stride = 0x82f = 2095 bytes, as the C text reads) FAILS",
       s480 not in (None, 0x82F) and s630 not in (None, 0x82F), "strides=%s/%s" % (s480, s630))
    gl = sorted({g for _a, _mn, _w, g, _k, _raw, kind, _s in acc480 + acc630 if kind == "global"})
    gl480 = sorted({g for _a, _mn, _w, g, _k, _raw, kind, _s in acc480 if kind == "global"})
    glst = [(hex(a), mn) for a, mn, _w, g, _k, _raw, kind, is_st in acc480 + acc630
            if kind == "global" and is_st]
    unst = [raw for _a, _mn, _w, _c, _k, raw, kind, _s in acc480 + acc630 if kind == "unresolved"]
    nsites = sum(1 for *_x, kind, _s in acc480 + acc630 if kind == "site")
    ok("A4 the two functions' ONLY out-of-frame, out-of-window memory is one named global READ "
       "(ds:0x985ae8, the debug flag the parity guard tests): the classifier now sees direct `ds:` "
       "operands, so an unclassified access lands in other/unresolved and this FAILS",
       not others and not unst and gl == [0x985AE8] and gl480 == [0x985AE8] and not glst
       and nsites >= 15,
       "other=%s unresolved=%s globals=%s global_stores=%s nsites=%d"
       % (others[:4], unst[:2], [hex(x) for x in gl], glst, nsites))
    ok("A4b the classifier is not blind: it classifies >0 stack, >0 site AND the 1 direct-global "
       "access in FUN_0056d480, i.e. all three kinds are non-empty in the same run",
       sum(1 for *_x, kind, _s in acc480 if kind == "stack") > 0
       and sum(1 for *_x, kind, _s in acc480 if kind == "site") > 0
       and len(gl480) == 1,
       "stack480=%d site480=%d globals480=%s"
       % (sum(1 for *_x, kind, _s in acc480 if kind == "stack"),
          sum(1 for *_x, kind, _s in acc480 if kind == "site"), [hex(x) for x in gl480]))
    ok("A5 FUN_0056d480 site READ map == {+0w,+2w,+4d,+8d}",
       readmap("480") == {(0, "w"), (2, "w"), (4, "d"), (8, "d")}, "map=%s" % sorted(readmap("480")))
    ok("A5b FUN_0056d630 site READ map == {+0w,+4d,+8d} (the probe ignores the +2 priority)",
       readmap("630") == {(0, "w"), (4, "d"), (8, "d")}, "map=%s" % sorted(readmap("630")))
    ok("A6 FUN_0056d630 is a PURE PROBE (0 stores) while the same regex counts 5+ stores in "
       "the inserter (so a blind regex cannot pass this)",
       len(st["630"]) == 0 and len(st["480"]) >= 4,
       "stores 630=%d 480=%d" % (len(st["630"]), len(st["480"])))
    ok("A7 FUN_0056d630 returns only 0/1 (xor eax,eax | mov eax,0x1 in the epilogue)",
       rets630 and all(r in ("mov eax,0x1", "xor eax,eax") for r in rets630), "%s" % rets630)
    ok("A8 FUN_0056d480 site WRITE map == {+0w,+2w,+4d,+8d} (all four fields on insert)",
       writemap("480") == {(0, "w"), (2, "w"), (4, "d"), (8, "d")},
       "map=%s" % sorted(writemap("480")))
    ok("A9 the found path is a max() on the +2 field AS A RULE: the +2 short is read sign-"
       "extended, that register is the cmp's LHS, the jcc is a jg whose TARGET is the instruction "
       "immediately after the `mov lhs,rhs` fallback (so the fallback runs only when old<=new), and "
       "the store back is a WORD of the cmp's own register to that same +2 address",
       maxlaw["read_field_off"] == 2 and maxlaw["cmp_lhs_is_the_signed_read"]
       and maxlaw["jcc_is_jg"] and maxlaw["jg_target_is_just_past_fallback"]
       and maxlaw["store_is_cmp_lhs_low_half"] and maxlaw["cmp_rhs_is_the_prio_argument"],
       "field=+%s jg=%s target_past_fallback=%s store=%s/%s lhs_def=%s rhs_def=%s"
       % (maxlaw["read_field_off"], maxlaw["jcc"], maxlaw["fallback"],
          maxlaw["store"], maxlaw["store_is_cmp_lhs_low_half"], maxlaw["cmp_lhs_producer"],
          maxlaw["cmp_rhs_producer"]))
    ok("A10 the eviction law AS A RULE: the free-slot test is on the +0 short, its 1000 comes from "
       "an `and r,0x3e8` on the SAME register the setge/dec wrote, the other arm is `mov r,0x14` + "
       "`sub r,prio` with prio read signed from +2, the already-beaten slot jumps to the loop "
       "increment, and the best-so-far guard is a STRICT jle whose target is one past BOTH update "
       "stores (so a tie keeps the first index)",
       evlaw["kind_read_field_off"] == 0 and evlaw["prio_read_field_off"] == 2
       and evlaw["1000_is_and_on_the_setge_dec_reg"] and evlaw["setge_is_fed_by_the_kind_test"]
       and evlaw["free_slot_jl_skips_the_prio_cmp"]
       and evlaw["free_slot_score_skips_20minus"] and evlaw["20_and_sub_share_one_reg"]
       and evlaw["prio_cmp_lhs_is_signed_prio_field"]
       and evlaw["sub20_subtrahend_is_signed_prio_field"] and evlaw["strict_is_jle_not_jl"]
       and evlaw["tie_skips_both_updates"] and evlaw["already_beaten_slot_jumps_to_increment"],
       "kind=+%s prio=+%s strict=%s updates=%s defs=%s/%s"
       % (evlaw["kind_read_field_off"], evlaw["prio_read_field_off"], evlaw["strict_jcc"],
          evlaw["updates_between_jle_and_target"], evlaw["prio_cmp_lhs_def"],
          evlaw["sub20_subtrahend_def"]))
    ok("A11 the no-candidate path RETURNS WITHOUT INSERTING as a rule: test ecx,ecx then a jl onto "
       "the epilogue head (%s); the taken path runs %s with ZERO stores, and the jump passes over "
       "all 4 insert stores (%s). A jl to anywhere else, or an epilogue that stores, FAILS."
       % (noc["target_insn"], " ".join(noc["epilogue_to_ret"]),
          ",".join(noc["insert_stores_skipped"])),
       noc["jl"] is not None and _INS[noc["jl_target"]][0] in ("pop", "ret", "mov")
       and not noc["stores_on_the_taken_path"] and len(noc["insert_stores_skipped"]) == 4
       and set(noc["insert_stores_skipped"]) == {"0x56d551", "0x56d55b", "0x56d561", "0x56d56b"},
       "target=%s epi=%s stores_on_path=%s skipped=%s"
       % (hex(noc["jl_target"]) if noc["jl_target"] else None, noc["epilogue_to_ret"],
          noc["stores_on_the_taken_path"], noc["insert_stores_skipped"]))
    def union(nm, key):
        return sorted({v for r in loops[nm] for v in r[key]})

    b480630 = set(union("0x56d480", "bounds")) | set(union("0x56d630", "bounds"))
    s480630 = set(union("0x56d480", "steps")) | set(union("0x56d630", "steps"))
    allcmp = inv["0x56d480"]["cmp"] + inv["0x56d630"]["cmp"]
    ok("A12 RIVAL R8 (the site list grows past 25) FAILS on an UNFILTERED inventory: the "
       "back-edges detected in 480/630 (%d/%d) carry ONLY bound 0x19 and step 0x10, AND the "
       "complete immediate inventory of both functions (printed in S3, nothing pre-filtered) "
       "contains no cmp bound above 0x19 and never mentions 0x4b=75"
       % (len(loops["0x56d480"]), len(loops["0x56d630"])),
       len(loops["0x56d480"]) == 2 and len(loops["0x56d630"]) == 1
       and b480630 == {0x19} and s480630 == {0x10} and allcmp
       and max(allcmp) == 0x19 and 0x4b not in inv["0x56d480"]["all"]
       and 0x4b not in inv["0x56d630"]["all"],
       "edges=%d/%d bounds=%s steps=%s cmp_imms=%s 75-in-480=%s 75-in-630=%s"
       % (len(loops["0x56d480"]), len(loops["0x56d630"]), [hex(x) for x in b480630],
          [hex(x) for x in s480630], [hex(x) for x in sorted(set(allcmp))],
          0x4b in inv["0x56d480"]["all"], 0x4b in inv["0x56d630"]["all"]))
    fam = {nm: set(union(nm, "bounds")) | set(union(nm, "counter_inits")) for nm in loops}
    sib_lea = sorted({int(mm.group(1), 16) for _a, m, o in window(*FUN_690) if m == "lea"
                      for mm in [re.search(r"\+0x([0-9a-f]{6,8})", o)] if mm})
    ok("A13 RIVAL R9 (the 75-entry sibling IS the site list) FAILS: FUN_0056d690 walks TWO loops "
       "with DIFFERENT counter inits %s, its leas address %s, and 75 appears nowhere in 480/630; "
       "the 75-entry band ends exactly where the site list starts (%s + 75*0x10 == %s -> adjacent "
       "arrays inside one block record, not one array)"
       % (sorted(fam["0x56d690"]), [hex(x) for x in sib_lea], hex(0x94EE28), hex(SITE_BASE)),
       fam["0x56d690"] == {0x19, 0x4b} and fam["0x56d480"] == {0x19} and fam["0x56d630"] == {0x19}
       and 0x94EE28 + 0x4B * SITE_STRIDE == SITE_BASE
       and len(sib_lea) == 2 and min(sib_lea) - 2 == 0x94EE28
       and max(sib_lea) - 4 == SITE_BASE,
       "counters=%s leas=%s adjacency=%s" % ({k: sorted(v) for k, v in fam.items()},
                                             [hex(x) for x in sib_lea],
                                             0x94EE28 + 0x4B * SITE_STRIDE == SITE_BASE))
    hidden = set(inv["0x56d480"]["all"]) - {0x19, 0x4b, 0x10}
    ok("A32 the S3 inventory is genuinely UNFILTERED (the P2b repair): FUN_0056d480's complete "
       "immediate set contains %d values the old `,0x(19|4b)$`/`,0x10$` regexes discarded (%s), "
       "so an unexpected bound or step would have shown up in the same table"
       % (len(hidden), ",".join(hex(x) for x in sorted(hidden))),
       len(hidden) >= 5, "inventory=%s" % [hex(x) for x in inv["0x56d480"]["all"]])
    je_lines = [(hex(a), o) for a, m, o in guard[:16] if m == "je"]
    ok("A14 parity guard exists: (x^y) then test al,0x1 and a second test on ds:0x985ae8 bit 0x10",
       any(m == "xor" for _, m, _ in guard)
       and any(m == "test" and o == "al,0x1" for _, m, o in guard)
       and any(m == "test" and o == "ah,0x10" for _, m, o in guard), "")
    ok("A15 RIVAL R7 (the guard can suppress the insert) FAILS: both guard je land on the body "
       "head 0x56d4b7; no ret in the guard",
       je_lines and all(int(o, 16) == 0x56D4B7 for _, o in je_lines)
       and not any(m == "ret" for _, m, _ in guard[:14]), "%s" % je_lines)
    ok("A16 the guard's first push resolves to the string 'Bad SITE' in the binary, and the "
       "second push 0x673850 is file-backed",
       smsg is not None and smsg.startswith("Bad SITE") and offfmt is not None,
       "str=%r sec=%s" % (smsg, secfmt))
    ok("A17 12 + 3 call sites, every one attributed to a function",
       len(calls[0x56D480]) == 12 and len(calls[0x56D630]) == 3
       and all(r[1] != "?" for r in calls[0x56D480] + calls[0x56D630]),
       "counts=%d/%d" % (len(calls[0x56D480]), len(calls[0x56D630])))
    kind3 = [r[0] for r in calls[0x56D480] if "0x3" in r[3] and "0x1" in r[3]]
    kind3p = [r[0] for r in calls[0x56D630] if "0x3" in r[3]]
    ok("A18 callers pass the literal kind=3 (and prio=1 for the inserter)",
       len(kind3) >= 1 and len(kind3p) >= 1, "inserter=%s probe=%s" % (kind3, kind3p))
    # a complete contiguous push run == the whole argument list (printed order is argN..arg1)
    full480 = [r for r in calls[0x56D480] if r[2] == 5]
    full630 = [r for r in calls[0x56D630] if r[2] == 4]
    ok("A18b 10 of 12 inserter sites show the full contiguous 5-push run and all 3 probe sites "
       "the 4-push run (2 sites split their pushes; printed as-is, not assumed)",
       len(full480) == 10 and len(full630) == 3,
       "pushes=%s / %s" % ([r[2] for r in calls[0x56D480]], [r[2] for r in calls[0x56D630]]))
    kinds480 = sorted({r[3][3] for r in full480 if r[3][3].startswith("0x")})
    kinds630 = sorted({r[3][2] for r in full630 if r[3][2].startswith("0x")})
    ok("A18c RIVAL R10 (the +0 'kind' is the constant 3 that the M303 dispatch passes) FAILS: "
       "the complete inserter sites and the probe sites each carry several distinct kind "
       "constants (printed in the detail)",
       len(kinds480) >= 3 and len(kinds630) >= 2,
       "kinds480=%s kinds630=%s" % (kinds480, kinds630))
    ok("A19 RIVAL R1 (ds:0x985b10 is an ARRAY) FAILS: 0 indexed accesses among %d refs"
       % len(r10), len(i10) == 0 and len(r10) > 200, "indexed=%d" % len(i10))
    ok("A20 RIVAL R2 (it is an accumulator) FAILS: no add/sub/inc/dec on the byte itself, over "
       "%d references" % len(r10),
       len(r10) > 200
       and not any(m in ("add", "sub", "inc", "dec") and "ds:0x985b10" in o for _, m, o in r10),
       "refs=%d forms=%s" % (len(r10), sorted(f10)))
    ok("A21 RIVAL R3 (its bits are set by read-modify-write on the global) FAILS: 0 or/and on "
       "the byte, and exactly 12 whole-byte stores",
       not any(m in ("or", "and", "xor") and "ds:0x985b10" in o for _, m, o in r10)
       and len(w10) == 12, "writers=%d" % len(w10))
    ntest = sum(1 for _, m, o in r10 if m == "test"
                and re.search(r",\s*(al|bl|cl|dl|ah|bh|ch|dh)$", o))
    ok("A22 ds:0x985b10 is used as a BIT MASK: >= 90 'test BYTE ds:0x985b10, <reg8>' sites",
       ntest >= 90, "tests=%d" % ntest)
    ok("A23 the rebuild law at 0x57f051-0x57f071: store the accumulator twice, and the loop body "
       "is movsx idx / mov dl,1 / shl dl,cl / or bl,dl",
       sum(1 for _, m, o in reb if m == "mov" and "ds:0x985b10" in o) == 2
       and any(m == "shl" and o == "dl,cl" for _, m, o in reb)
       and any(m == "or" and o == "bl,dl" for _, m, o in reb),
       "ops=%s" % sorted({m for _, m, _ in reb}))
    ok("A24 the rebuild walks 412-B records at 0x91e494 and takes the BIT INDEX from BYTE[rec]",
       any(m == "add" and "0x19c" in o for _, m, o in reb)
       and any("0x91e494" in o for _, m, o in reb)
       and any(m == "movsx" and "BYTE PTR [eax]" in o for _, m, o in reb), "")
    ok("A25 RIVAL R4 (ds:0x985aec is a counter) FAILS: 0 arithmetic among its %d refs" % len(rec),
       len(rec) >= 60
       and not any(m in ("add", "sub", "inc", "dec", "neg", "not", "xor", "or", "and")
                   and "ds:0x985aec" in o for _, m, o in rec), "forms=%s" % sorted(fec))
    ok("A26 ds:0x985aec is an ENUM: every immediate it is compared with is in {1,2,3,4}",
       cec and set(cec) <= {1, 2, 3, 4}, "cmps=%s" % [hex(x) for x in cec])
    nm92 = sorted(k for k, v in mirror.items() if "ds:0x92bde8" in v["kind"])
    n8f = sorted(k for k, v in mirror.items() if "ds:0x8f0c11" in v["kind"])
    nun = sorted(k for k, v in mirror.items() if v["kind"].startswith("UNRESOLVED"))
    ok("A27 ds:0x985aec has exactly 4 writers and 2 are attributed to ds:0x92bde8 by a BACKWARD "
       "DEF-WALK, one in LOAD form (the producer of the stored register is `mov reg,ds:0x92bde8`) "
       "and one in CO-STORE form (the same register had just been stored to ds:0x92bde8 with no "
       "write to that register between) - an intervening write would break the walk, so proximity "
       "alone cannot satisfy this",
       len(wec) == 4 and len(nm92) == 2 and any("loads" in mirror[k]["kind"] for k in nm92)
       and any("co-store" in mirror[k]["kind"] for k in nm92),
       "writers=%d mirror=%s" % (len(wec), {k: mirror[k]["kind"][:46] for k in nm92}))
    ok("A28 a 3rd writer's value is provably the setup byte: the def-walk of the stored register "
       "closes on `movsx reg,BYTE PTR ds:0x8f0c11` (a load, not an adjacency)",
       len(n8f) == 1 and "loads ds:0x8f0c11" in (mirror[n8f[0]]["kind"] if n8f else ""),
       "setup=%s chain=%s" % (n8f, mirror[n8f[0]]["chain"] if n8f else None))
    loads92 = [k for k in mirror if mirror[k]["kind"].startswith("DEF-WALK: loads ds:0x92bde8")]
    loads8f = [k for k in mirror if mirror[k]["kind"].startswith("DEF-WALK: loads ds:0x8f0c11")]
    closed = loads92 + loads8f
    ok("A28b RIVAL R11 (the new def-walk is just the old proximity test renamed) FAILS: every "
       "writer closed by the walk resolves to ONE numeric global address, and for every such "
       "writer the 10-instruction window names strictly MORE candidates - under the old rule the "
       "source is the literal token 'proximity', not a global, so this goes red",
       bool(closed) and all(len(mirror[k]["srcs"]) == 1 and mirror[k]["srcs"][0].isdigit()
                            for k in closed)
       and all(len(mirror[k]["srcs"]) < len(mirror[k]["prox"]) for k in closed),
       "closed=%s srcs_vs_window=%s" % (closed, {k: (mirror[k]["srcs"], mirror[k]["prox"])
                                                 for k in sorted(closed)}))
    ok("A28c the 4th writer stays DECLARED UNKNOWN, not silently mirror-attributed: the in-function "
       "walk cannot close its chain (the value arrives from outside the walk)",
       len(nun) == 1 and nun == ["0x4ddcf1"], "unattributed=%s" % nun)
    ok("A29 ds:0x985aec is scalar too (0 indexed accesses)", len(iec) == 0, "indexed=%d" % len(iec))

    out.p("\n[CHECKS]")
    bad = 0
    for name, good, detail in chk:
        out.p("   %s %s%s" % ("OK  " if good else "FAIL", name, ("  | " + detail) if detail else ""))
        bad += 0 if good else 1
    out.p("\n%d/%d checks OK" % (len(chk) - bad, len(chk)))
    out.p("table sha %s" % hashlib.sha256("\n".join(out.lines).encode()).hexdigest()[:16])
    if bad:
        print("RESULT: FAIL (%d checks red)" % bad, file=sys.stderr)
        return 1
    print("RESULT: PASS M308 site-list identities")
    return 0


if __name__ == "__main__":
    sys.exit(main())
