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
  S10 ds:0x985aec: 4 writers, 2 provably mirroring ds:0x92bde8, 1 fed by the setup byte
      ds:0x8f0c11, and comparisons only against 1/2/3/4

RIVALS that FAIL on the printed numbers: R1 0x985b10 is a per-faction ARRAY; R2 it is an
accumulator; R3 its bits are set by read-modify-write on the global; R4 0x985aec is a counter;
R5 the site-record stride is 0x82f = 2095 BYTES (what the decompiled C literally says);
R6 the two functions are insert/probe twins (both write); R7 the parity guard can suppress the
insert; R8 the site list grows past 25; R9 the 75-entry sibling is the same list.

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
    val, acc, traces, stride = {}, [], [], None
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


def main():
    out = Out()
    global _INS, _ORDER
    _INS, _ORDER = parse_text()
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
        out.p("   %s 'other' (not stack, not site window): %d %s" % (tag, len(other), other[:3]))
        out.p("   %s unresolved (base not tracked): %d %s" % (tag, len(unst), unst[:3]))
        fmap[tag] = {key for key in seen}
    out.p("   site READ map   480=%s  630=%s"
          % (sorted({(f, w) for f, w, r in fmap["480"] if r == "R"}),
             sorted({(f, w) for f, w, r in fmap["630"] if r == "R"})))
    out.p("   site WRITE map  480=%s  630=%s"
          % (sorted({(f, w) for f, w, r in fmap["480"] if r == "W"}),
             sorted({(f, w) for f, w, r in fmap["630"] if r == "W"})))

    # ---------------- S3 loop bounds and steps
    out.p("\n[S3] loop bounds/steps in the family (immediates actually compared against a counter)")
    loops = {}
    for lo, hi, nm in ((FUN_480[0], FUN_480[1], "0x56d480"),
                       (FUN_630[0], FUN_630[1], "0x56d630"),
                       (FUN_690[0], FUN_690[1], "0x56d690")):
        bounds = sorted({int(o.split(",")[-1].strip(), 16) for _, m, o in window(lo, hi)
                         if m == "cmp" and re.search(r",0x(19|4b)$", o)})
        steps = sorted({int(o.split(",")[-1].strip(), 16) for _, m, o in window(lo, hi)
                        if m in ("add", "sub") and re.search(r",0x10$", o)})
        inits = sorted({int(o.split(",")[-1].strip(), 16) for _, m, o in window(lo, hi)
                        if m == "mov" and re.search(r",0x(19|4b)$", o)})
        loops[nm] = (bounds, steps, inits)
        out.p("   %-10s cmp-bounds=%s steps=%s counter-inits=%s" % (nm, bounds, steps, inits))

    # ---------------- S4 stores / return values
    out.p("\n[S4] store census")
    st = {}
    for nm, lo, hi in (("480", *FUN_480), ("630", *FUN_630), ("690", *FUN_690)):
        rows = ["%s %s" % (hex(a), o) for a, m, o in window(lo, hi)
                if re.match(r"^mov\s+(DWORD|WORD|BYTE) PTR \[", o)]
        st[nm] = rows
        out.p("   FUN_0056d%s: %d stores" % (nm, len(rows)))
        for r in rows:
            out.p("      %s" % r)
    epilogue630 = [(a, m, o) for a, m, o in window(*FUN_630) if a >= 0x56D674]
    rets630 = ["%s %s" % (m, o) for a, m, o in epilogue630
               if (m == "mov" and o.startswith("eax,")) or m == "xor"]
    out.p("   FUN_0056d630 epilogue ops that set eax: %s" % rets630)

    found = [(a, m, o) for a, m, o in window(*FUN_480) if 0x56D59F <= a <= 0x56D5C3]
    out.p("\n[S5] found-path block 0x56d59f-0x56d5c3")
    for a, m, o in found:
        out.p("   %s\t%-6s %s" % (hex(a), m, o))

    evict = [(a, m, o) for a, m, o in window(*FUN_480) if 0x56D4FB <= a <= 0x56D541]
    out.p("\n[S6] eviction block 0x56d4fb-0x56d541")
    for a, m, o in evict:
        out.p("   %s\t%-6s %s" % (hex(a), m, o))
    imm_3e8 = any(m == "and" and "0x3e8" in o for _, m, o in evict)
    imm_14 = any(m == "mov" and o == "eax,0x14" for _, m, o in evict)

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
                if mn == "call":
                    break
                if mn == "push":
                    push.append(o)
                elif mn == "add" and o.startswith("esp,"):
                    break
                if len(push) >= 6:
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

    mirror = {}
    for a, mn, o in wec:
        near = around(a)
        out.p("   W %s\t%-6s %s" % (hex(a), mn, o))
        for x, m, o2 in near[-6:]:
            out.p("       ctx %s\t%-6s %s" % (hex(x), m, o2))
        mirror[hex(a)] = {"92bde8": any("0x92bde8" in o2 for _, _, o2 in near),
                          "8f0c11": any("0x8f0c11" in o2 for _, _, o2 in near)}
    out.p("   writer producers (a 0x92bde8 / 0x8f0c11 reference within 10 insns before):")
    for k in sorted(mirror):
        out.p("      %s %s" % (k, mirror[k]))

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
    ok("A4 the two functions touch NO memory outside the stack frame and the site window",
       not others, "other=%s" % others[:4])
    ok("A5 FUN_0056d480 site READ map == {+0w,+2w,+4d,+8d}",
       readmap("480") == {(0, "w"), (2, "w"), (4, "d"), (8, "d")}, "map=%s" % sorted(readmap("480")))
    ok("A5b FUN_0056d630 site READ map == {+0w,+4d,+8d} (the probe ignores the +2 priority)",
       readmap("630") == {(0, "w"), (4, "d"), (8, "d")}, "map=%s" % sorted(readmap("630")))
    ok("A6 FUN_0056d630 is a PURE PROBE (0 stores in its 41 insns)",
       len(st["630"]) == 0, "stores=%d" % len(st["630"]))
    ok("A7 FUN_0056d630 returns only 0/1 (xor eax,eax | mov eax,0x1 in the epilogue)",
       rets630 and all(r in ("mov eax,0x1", "xor eax,eax") for r in rets630), "%s" % rets630)
    ok("A8 FUN_0056d480 site WRITE map == {+0w,+2w,+4d,+8d} (all four fields on insert)",
       writemap("480") == {(0, "w"), (2, "w"), (4, "d"), (8, "d")},
       "map=%s" % sorted(writemap("480")))
    ok("A9 found path is a max() on +2 (movsx + cmp + jg + fallback mov eax,edx + WORD store)",
       any(m == "movsx" for _, m, _ in found) and any(m == "jg" for _, m, _ in found)
       and any(m == "mov" and o == "eax,edx" for _, m, o in found)
       and any(m == "mov" and "WORD PTR" in o for _, m, o in found),
       "ops=%s" % sorted({m for _, m, _ in found}))
    ok("A10 eviction law: empty-slot score 1000 (and 0x3e8) and 20-priority (mov eax,0x14 / sub) "
       "with a STRICT jle (ties keep the first index)",
       imm_3e8 and imm_14 and any(m == "jle" for _, m, _ in evict),
       "3e8=%s 0x14=%s" % (imm_3e8, imm_14))
    ok("A11 no-candidate path returns WITHOUT inserting (test ecx,ecx / jl to the epilogue)",
       any(m == "test" and o == "ecx,ecx" for _, m, o in evict)
       and any(m == "jl" for _, m, o in evict), "")
    ok("A12 RIVAL R8 (the list grows past 25) FAILS: 480/630 have ONLY bound 0x19 and step 0x10",
       loops["0x56d480"][0] == [0x19] and loops["0x56d630"][0] == [0x19]
       and loops["0x56d480"][1] == [0x10] and loops["0x56d630"][1] == [0x10],
       "loops=%s" % loops)
    ok("A13 RIVAL R9 (the 75-entry sibling is the same list) FAILS: 0x56d690 counts 0x4b=75 "
       "entries; 480/630 never mention 0x4b",
       loops["0x56d690"][2] == [0x4b] and 0x4b not in loops["0x56d480"][2]
       and 0x4b not in loops["0x56d630"][2],
       "690=%s 480=%s 630=%s" % (loops["0x56d690"][2], loops["0x56d480"][2],
                                 loops["0x56d630"][2]))
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
    ok("A18b every call site pushes exactly the parameter count (5 for 480, 4 for 630)",
       all(r[2] == 5 for r in calls[0x56D480]) and all(r[2] == 4 for r in calls[0x56D630]),
       "pushes=%s / %s" % ([r[2] for r in calls[0x56D480]], [r[2] for r in calls[0x56D630]]))
    ok("A19 RIVAL R1 (ds:0x985b10 is an ARRAY) FAILS: 0 indexed accesses among %d refs"
       % len(r10), len(i10) == 0 and len(r10) > 200, "indexed=%d" % len(i10))
    ok("A20 RIVAL R2 (it is an accumulator) FAILS: no add/sub/inc/dec on the byte itself",
       not any(m in ("add", "sub", "inc", "dec") and "ds:0x985b10" in o for _, m, o in r10),
       "forms=%s" % sorted(f10))
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
       not any(m in ("add", "sub", "inc", "dec", "neg", "not", "xor", "or", "and")
               and "ds:0x985aec" in o for _, m, o in rec), "forms=%s" % sorted(fec))
    ok("A26 ds:0x985aec is an ENUM: every immediate it is compared with is in {1,2,3,4}",
       cec and set(cec) <= {1, 2, 3, 4}, "cmps=%s" % [hex(x) for x in cec])
    nm = [k for k in sorted(mirror) if mirror[k]["92bde8"]]
    ns = [k for k in sorted(mirror) if mirror[k]["8f0c11"]]
    ok("A27 ds:0x985aec has exactly 4 writers and 2 provably mirror ds:0x92bde8",
       len(wec) == 4 and len(nm) == 2, "writers=%d mirrors=%s" % (len(wec), nm))
    ok("A28 a 3rd writer is fed by the setup byte ds:0x8f0c11 (movsx within 10 insns)",
       len(ns) >= 1, "setup-linked=%s" % ns)
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
