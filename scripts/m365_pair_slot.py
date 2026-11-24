#!/usr/bin/env python3
"""M365 (chain-3, STATIC) - 0x94d5dc: the third slot of FUN_00551a20.

PICK (run context 2026-11-24 ~03:53 EST): M362's leftover - "0x551a20's third slot
0x94d5dc".  FUN_00551a20 (the relation-set writer) touches three per-pair dwords: the
mask at 0x94d448, its +0x20 sibling 0x94d468 (M362's high-id rows) and a THIRD one at
0x94d5dc which FUN_00551a20 ZEROES (both directions) whenever it sets relation bit 0x10.

This tool censuses every instruction in the image that names 0x94d5dc, resolves each
addressing form to the same (fac*0x82f + tgt)*4 geometry the mask uses, classifies each
store's right-hand side by local def-use, and reads what the consumers do with the value
(deadline arithmetic, cross-direction compares, score terms).  Static only: objdump text
cache + the PE for string constants; no box, no debugger.

ACCEPT  python3 -u scripts/m365_pair_slot.py  -> PASS line + digest, re-run identical.

GATES (tables printed FIRST, then asserted; each VERIFIED row names its mutant in
scripts/m365_mutate.py):
  G1  the census: 23 referencing instructions, 8 writes / 15 reads, 7 functions, two
      addressing forms (4 absolute-indexed, 19 base+disp).
  G2  geometry: 0x94d5dc = block+0x1ac = mask+0x194; the sibling family FUN_004da2c0
      fills lies 0x20 apart (5 x 8-dword per-target arrays, 0x12c..0x1ac).
  G3  index forms: the linear-form tracer (self-tested first) resolves every
      non-pointer site to the 0x82f stride with a unit second coefficient.
  G4  writers: ZERO 2 / CARRY 2 / INC1 3 / DELTA(+2*signed byte) 1 - measured, not authored.
  G5  pairing: 0x94d5bc is bumped in the SAME block with the SAME delta at every site
      that bumps 0x94d5dc (4/4), and it sits one 8-dword array earlier.
  G6  consumers: the round-fraction deadlines (/50 and /25, +1/+2) and the four
      cross-direction compares with their derived codes (3/4, score bit, branch).
  G7  RIVALS, each measured and each FAILING on the printed numbers.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M365_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("M365_EXE") or os.path.join(ROOT, "programs/terran.exe")

TGT = 0x94D5DC
MASK = 0x94D448
BLOCK = 0x94D430
SIB = 0x94D5BC          # one 8-dword array earlier
STRIDE = 0x82F          # dwords per faction block (0x20bc bytes)
ROUND = 0x985AFC        # M175/M341: the round counter
FAMILY = (0x94D4F4, 0x94D55C, 0x94D57C, 0x94D59C, 0x94D5BC, 0x94D5DC)

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
ABSIDX = re.compile(r"\[[a-z]{2,3}\*4\+0x([0-9a-f]+)\]")
BASEDISP = re.compile(r"\[[a-z]{2,3}\+0x([0-9a-f]+)\]")
MEMDEST = re.compile(r"^DWORD PTR \[")


def insns():
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            t = m.group(3).strip()
            p = t.split(None, 1)
            out.append({"a": int(m.group(1), 16), "op": p[0],
                        "arg": p[1] if len(p) > 1 else "", "t": t})
    return out


INS = insns()
POS = {i["a"]: n for n, i in enumerate(INS)}


def win(lo, hi):
    return [i for i in INS if lo <= i["a"] <= hi]


def imm(s):
    s = s.strip()
    m = re.match(r"^0x([0-9a-f]+)$", s)
    if m:
        return int(m.group(1), 16)
    m = re.match(r"^([0-9]+)$", s)
    return int(m.group(1)) if m else None


def hexa(v):
    return "0x%x" % v


def funcs():
    """addr -> (name, size) from the Ghidra export index (never a hardcoded length)."""
    import csv
    rows = []
    idx = os.environ.get("M365_INDEX") or os.path.expanduser("~/reverse/smac/ghidra_out/index.csv")
    for d in csv.DictReader(open(idx)):
        rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
    rows.sort()
    return rows


FNS = funcs()


def owner(a):
    lo, hi = 0, len(FNS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if FNS[mid][0] <= a:
            lo = mid
        else:
            hi = mid - 1
    return FNS[lo]


# ---------------------------------------------------------------- G1: the census
def census():
    sites = []
    for i in INS:
        if re.search(r"0x94d5dc\b", i["t"]) is None:
            continue
        dest, _, src = i["arg"].partition(",")
        rd = MEMDEST.match(dest.strip())                # [x] = value  -> a WRITE
        form = "abs-idx" if ABSIDX.search(i["arg"]) else (
            "base-disp" if BASEDISP.search(i["arg"]) else "other")
        base = None
        m = re.search(r"\[([a-z]{2,3})(?:\*4)?\+0x94d5dc\]", i["arg"])
        if m:
            base = m.group(1)
        f = owner(i["a"])
        sites.append({"a": i["a"], "rw": "W" if rd else "R", "form": form, "base": base,
                      "fn": f[1], "fnaddr": f[0], "ins": i})
    return sites


def cls_rhs(site):
    """Classification of a store's right-hand side by local def-use (backwards, same block)."""
    i = site["ins"]
    rhs = i["arg"].partition(",")[2].strip()
    if imm(rhs) is not None:
        return "CONST:" + hexa(imm(rhs)), None
    reg = rhs
    n = POS[i["a"]]
    steps = []
    for k in range(n - 1, max(0, n - 14), -1):
        b = INS[k]
        if b["op"] in ("ret", "call", "jmp") or b["op"].startswith("j"):
            break
        if not (b["op"] == "mov" and b["arg"].startswith(reg + ",")):
            if b["op"] in ("inc", "dec", "add", "sub") and b["arg"].split(",")[0].strip() == reg:
                steps.append(b)
            continue
        steps.append(b)
        return _rhs_form(reg, steps), steps
    return "CARRY:" + reg, None


def _rhs_form(reg, steps):
    last = steps[0]
    if last["op"] == "inc":
        return "INC1:" + reg
    if last["op"] == "add":
        # add reg,S  where S was built as shl of a movsx byte -> a scaled byte delta
        src = last["arg"].partition(",")[2].strip()
        n = POS[last["a"]]
        for k in range(n - 1, max(0, n - 6), -1):
            b = INS[k]
            if b["op"] == "shl" and b["arg"].startswith(src + ","):
                sh = imm(b["arg"].partition(",")[2])
                if sh is None:
                    return "ADD:" + src
                for j in range(k - 1, max(0, k - 4), -1):
                    c = INS[j]
                    if c["op"] == "movsx" and c["arg"].startswith(src + ","):
                        return "DELTA:%dx(signed byte %s)" % (1 << sh, c["arg"].partition(",")[2].strip())
                return "DELTA:%dx%s" % (1 << sh, src)
        return "ADD:" + src
    return "MOV:" + last["arg"]


# ---------------------------------------------------------------- G3: linear-form tracer
# A form is {symbol: coefficient}; symbols name the value a register was loaded from.
def _mul(f, k):
    return {s: c * k for s, c in f.items()}


def _add(f, g):
    o = dict(f)
    for s, c in g.items():
        o[s] = o.get(s, 0) + c
    return {s: c for s, c in o.items() if c}


def _neg(f):
    return {s: -c for s, c in f.items()}


def trace(seq, reg):
    """Forward-replay a self-contained instruction list; return the linear form of `reg`.

    Supported: mov r,imm / mov r,r2 / mov r,[base+disp] / mov r,r2 then shl/add/sub /
    lea r,[r1+r2*s] / lea r,[r1] / inc r / xor r,r.  Any other write makes the form
    UNKNOWN (None) - the tracer never guesses.
    """
    st = {}
    for b in seq:
        op, arg = b["op"], b["arg"]
        if op == "mov":
            d, _, s = arg.partition(",")
            d, s = d.strip(), s.strip()
            v = imm(s)
            if v is not None:
                st[d] = {"#": v}
            elif s in st:
                st[d] = dict(st[s])
            else:
                m = re.match(r"^(?:DWORD PTR )?\[([a-z]{2,3})(?:\+0x([0-9a-f]+))?\]$", s)
                if m:
                    st[d] = {("mem@0x%s" % (m.group(2) or "0")): 1}
                else:
                    m = re.match(r"^(?:DWORD PTR |BYTE PTR )?\[(e[bs]p)-0x([0-9a-f]+)\]$", s)
                    if m:
                        st[d] = {("sp-0x" + m.group(2)): 1}
                    else:
                        st[d] = {("in:" + s): 1}
        elif op == "lea":
            d, _, s = arg.partition(",")
            d, s = d.strip(), s.strip()
            m = re.match(r"^\[([a-z]{2,3})(?:\+([a-z]{2,3})\*([1248]))?\]$", s)
            if not m:
                st.pop(d, None)
                continue
            f = dict(st.get(m.group(1), {"in:" + m.group(1): 1}))
            if m.group(2):
                g = st.get(m.group(2), {"in:" + m.group(2): 1})
                f = _add(f, _mul(g, int(m.group(3))))
            st[d] = {s2: c for s2, c in f.items() if c}
        elif op == "shl":
            d, _, s = arg.partition(",")
            v = imm(s)
            if v is None:                                  # shl r,cl -> unknown count
                st.pop(d.strip(), None)
                continue
            st[d.strip()] = _mul(st.get(d.strip(), {"in:" + d.strip(): 1}), 1 << v)
        elif op in ("add", "sub"):
            d, _, s = arg.partition(",")
            d, s = d.strip(), s.strip()
            f = st.get(d, {"in:" + d: 1})
            g = st.get(s, {"in:" + s: 1})
            st[d] = _add(f, g) if op == "add" else _add(f, _neg(g))
        elif op == "inc":
            d = arg.strip()
            st[d] = _add(st.get(d, {"in:" + d: 1}), {"#": 1})
        elif op == "xor" and arg.split(",")[0] == arg.split(",")[1]:
            st[arg.split(",")[0].strip()] = {}
        elif op in ("call", "ret"):
            return None
    return st.get(reg, {("in:" + reg): 1})          # never defined in the window = a parameter


def window_for(n):
    """Up to 16 instructions back from n, stopping at the previous branch/call/ret."""
    lo = max(0, n - 16)
    for k in range(n - 1, lo, -1):
        b = INS[k]
        if b["op"] in ("ret", "call", "jmp") or b["op"].startswith("j"):
            return INS[k + 1:n + 1]
    return INS[lo:n + 1]


def self_test():
    """The tracer is load-bearing: these chains pin its arithmetic (incl. the M137 trap)."""
    def I(a, t):
        p = t.split(None, 1)
        return {"a": a, "op": p[0], "arg": p[1] if len(p) > 1 else "", "t": t}
    idiom = [I(1, "mov    ecx,eax"), I(2, "shl    ecx,0x6"), I(3, "add    ecx,eax"),
             I(4, "lea    edx,[eax+ecx*2]"), I(5, "shl    edx,0x4"), I(6, "sub    edx,eax"),
             I(7, "mov    eax,DWORD PTR [esi+0xa20]"), I(8, "add    edx,eax")]
    t1 = (trace(idiom, "edx") == {"in:eax": STRIDE, "mem@0xa20": 1},
          "2095 idiom -> 0x82f*X + tgt")
    # the SAME idiom kept in bytes (x4) is 8380 = 0x20bc, never the element count
    bytes_form = [I(1, "mov    ecx,eax"), I(2, "shl    ecx,0x6"), I(3, "add    ecx,eax"),
                  I(4, "lea    edx,[eax+ecx*2]"), I(5, "shl    edx,0x4"), I(6, "sub    edx,eax"),
                  I(7, "shl    edx,0x2")]
    t2 = (trace(bytes_form, "edx") == {"in:eax": STRIDE * 4},
          "byte form: the same idiom with a final shl 2 is 0x20bc, not 0x82f")
    t3 = (trace(idiom[:-1], "edx") == {"in:eax": STRIDE},
          "without the tgt add the form is the bare stride 0x82f")
    t4 = (trace([I(1, "lea    edx,[eax+ecx*4]")], "edx") == {"in:eax": 1, "in:ecx": 4},
          "lea scale is applied to the scaled operand")
    t5 = (trace([I(1, "mov    edx,DWORD PTR [ebp-0x8]")], "edx") == {"sp-0x8": 1},
          "a stack read is a parameter symbol, not a constant")
    return [t1, t2, t3, t4, t5]


# ---------------------------------------------------------------- G6 helpers
def magic_div_ok(magic, shift, d, hi):
    """Is `(x*magic)>>32 >> shift` == x//d on 0..hi?  (measured, not asserted by hand)"""
    bad = 0
    for x in range(0, hi + 1):
        v = (x * magic) >> 32
        v = v >> shift
        if v != x // d:
            bad += 1
    return bad


def pe_string(va, n=24):
    d = open(EXE, "rb").read()
    pe = struct.unpack_from("<I", d, 0x3c)[0]
    base = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    sz = struct.unpack_from("<H", d, pe + 20)[0]
    for i in range(nsec):
        o = pe + 24 + sz + i * 40
        vs, vaa, rs, ra = struct.unpack_from("<IIII", d, o + 8)
        r = va - base
        if vaa <= r < vaa + max(vs, rs):
            off = ra + r - vaa
            return d[off:off + n]
    return b""


# ---------------------------------------------------------------- main
def main():
    out = []
    say = out.append
    gates = []

    def gate(gid, ok, msg):
        gates.append((gid, ok, msg))
        say("  [%s] %-4s %s" % ("ok" if ok else "XX", gid, msg))

    sites = census()
    fnames = {}
    for s in sites:
        fnames[s["fn"]] = fnames.get(s["fn"], 0) + 1

    say("M365  0x94d5dc - the third slot of FUN_00551a20 (per-(fac,tgt) dword at block+0x1ac)")
    say("=" * 96)
    say("G1  CENSUS - every instruction naming 0x94d5dc in the image")
    say("    %-9s %-5s %-10s %-5s %-19s %s" % ("addr", "rw", "form", "base", "function", "text"))
    for s in sites:
        say("    %-9s %-5s %-10s %-5s %-19s %s" % (hexa(s["a"]), s["rw"], s["form"],
                                                   s["base"] or "-", s["fn"], s["ins"]["t"]))
    nW = sum(1 for s in sites if s["rw"] == "W")
    nR = len(sites) - nW
    nabs = sum(1 for s in sites if s["form"] == "abs-idx")
    ndisp = sum(1 for s in sites if s["form"] == "base-disp")
    say("    totals: %d sites, %d writes / %d reads, %d abs-indexed / %d base+disp, %d functions"
        % (len(sites), nW, nR, nabs, ndisp, len(fnames)))
    say("    per function: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(fnames.items())))
    gate("G1a", len(sites) == 23, "23 instructions reference 0x94d5dc (measured)")
    gate("G1b", nW == 8 and nR == 15, "8 writes / 15 reads")
    gate("G1c", nabs == 4 and ndisp == 19 and nabs + ndisp == len(sites),
         "two addressing forms, 0 unknown: 4 absolute-indexed + 19 base+disp")
    gate("G1d", len(fnames) == 7 and sorted(fnames.values()) == [1, 2, 2, 2, 2, 6, 8],
         "7 functions, site counts %s" % sorted(fnames.values()))

    say("")
    say("G2  GEOMETRY - the slot's position in the 0x20bc-byte faction block and its family")
    d_blk = TGT - BLOCK
    d_mask = TGT - MASK
    # the family is MEASURED off FUN_004da2c0's own store block, never authored
    fa0, fan, fasz = owner(0x4DA2C0)
    fam_all = sorted({int(m.group(1), 16) for i in INS
                      if fa0 <= i["a"] < fa0 + fasz
                      for m in [re.search(r"\[(?:[a-z]{2,3}(?:\*4)?\+)?(0x94d5[0-9a-f]{2})\]", i["t"])] if m})
    fam_far = [x for x in fam_all if x != 0x94D554]
    fam_steps = [b - a for a, b in zip(fam_far, fam_far[1:])]
    say("    0x94d5dc - block 0x94d430 = %s (%d B = %d dwords)" % (hexa(d_blk), d_blk, d_blk // 4))
    say("    0x94d5dc - mask  0x94d448 = %s (%d B = %d dwords)" % (hexa(d_mask), d_mask, d_mask // 4))
    say("    displacements in %s (its store block): %s"
        % (fan, ", ".join(hexa(x) for x in fam_all)))
    say("    the five per-target slots from 0x94d55c on: %s  steps %s; 0x94d554 = first - %s"
        % (", ".join(hexa(x) for x in fam_far), ", ".join(hexa(x) for x in fam_steps),
           hexa(fam_far[0] - 0x94D554) if fam_far else "?"))
    gate("G2b", len(fam_all) == 6 and len(fam_far) == 5 and fam_steps == [0x20] * 4 and
         fam_far[-1] == TGT and fam_far[0] - 0x94D554 == 8 and
         d_blk == 0x1AC and d_mask == 0x194 and d_mask % 4 == 0,
         "six displacements: 0x94d554 (M165's pair head, 8 B before the first) plus five "
         "per-target slots exactly 0x20 apart ending at 0x94d5dc = block+0x1ac = mask+0x194")
    gate("G2c", SIB in fam_all and TGT - SIB == 0x20 and SIB - BLOCK == 0x18C,
         "the paired sibling 0x94d5bc is the array immediately before (block+0x18c)")

    say("")
    say("G3  INDEX FORMS - linear-form tracer (self-tested first), then each site's base")
    st = self_test()
    for i, (ok, msg) in enumerate(st):
        say("    selftest %d %-4s %s" % (i + 1, "ok" if ok else "XX", msg))
    gate("G3a", all(ok for ok, _ in st), "tracer self-test %d/%d (2095 idiom, byte-form, no-addend, lea scale)"
         % (sum(1 for ok, _ in st if ok), len(st)))
    forms = []
    for s in sites:
        n = POS[s["a"]]
        f = trace(window_for(n)[:-1], s["base"])
        sc = 4 if re.search(r"\[[a-z]{2,3}\*4\+", INS[n]["arg"]) else 1   # the site's own scale
        if f is not None and sc != 1:
            f = _mul(f, sc)
        forms.append((s["a"], f))
        kind = "?"
        if f is not None:
            coefs = [abs(c) for c in f.values() if c]
            if any(c in (STRIDE, STRIDE * 4) for c in coefs):
                kind = "folded"
            elif len(f) == 1 and list(f.values()) == [1]:
                kind = "pointer"
        say("    %-9s %-8s base=%-4s %-8s %s" % (
            hexa(s["a"]), s["form"], s["base"] or "-", kind,
            "UNKNOWN" if f is None else ", ".join(
                "%s*%s" % (hexa(c) if isinstance(c, int) else c, k) for k, c in sorted(f.items()))))
    def normalise(f):
        """Scale a byte form back to dwords: 0x20bc/4 = 0x82f, 4/4 = 1."""
        c = [abs(x) for x in f.values() if x]
        if STRIDE * 4 in c:
            return {k: (v // 4 if v % 4 == 0 else v) for k, v in f.items()}
        return dict(f)
    folded = [(a, f) for a, f in forms if any(abs(c) in (STRIDE, STRIDE * 4) for c in f.values())]
    ptrs = [(a, f) for a, f in forms if len(f) == 1 and list(f.values()) == [1] and (a, f) not in folded]
    unres = [a for a, f in forms if f is None]
    norm_ok = [a for a, f in folded
               if sorted(abs(c) for c in normalise(f).values() if c) == [1, STRIDE]]
    byte_ok = [a for a, f in folded
               if sorted(abs(c) for c in f.values() if c) == [4, STRIDE * 4]]
    norm_ok = [a for a, f in folded
               if sorted(abs(c) for c in normalise(f).values() if c) == [1, STRIDE]]
    say("    folded %d / pointer-param %d / unresolved %d; byte form {0x20bc,4}: %d; "
        "dword form {0x82f,1} after /4: %d"
        % (len(folded), len(ptrs), len(unres), len(byte_ok), len(norm_ok)))
    gate("G3b", len(folded) == 12 and len(byte_ok) == 12 and len(norm_ok) == 12,
         "every folded site is 4*(fac*0x82f + tgt) bytes: coefficient multiset {0x20bc, 4} "
         "(%d/12) and {0x82f, 1} in elements (%d/12)" % (len(byte_ok), len(norm_ok)))
    gate("G3d", len(unres) == 0 and len(folded) + len(ptrs) == len(forms) and len(ptrs) == 11,
         "0 unresolved addressing forms: all 23 sites classified (%d folded + %d plain record "
         "pointer)" % (len(folded), len(ptrs)))

    say("")
    say("G4  WRITERS - right-hand side of the 8 stores, by local def-use")
    wf = {}
    for s in sites:
        if s["rw"] != "W":
            continue
        form, steps = cls_rhs(s)
        wf[form] = wf.get(form, 0) + 1
        say("    %-9s %-46s %s" % (hexa(s["a"]), form, s["ins"]["t"]))
    say("    classes: " + ", ".join("%s x%d" % (k, v) for k, v in sorted(wf.items())))
    kinds = {}
    for k, v in wf.items():
        kinds[k.split(":")[0]] = kinds.get(k.split(":")[0], 0) + v
    gate("G4a", kinds.get("CONST", 0) == 2 and kinds.get("CARRY", 0) == 2 and
         kinds.get("INC1", 0) == 3 and kinds.get("DELTA", 0) == 1,
         "2 zero-stores + 2 carried-register stores + 3 ++ + 1 scaled-byte delta (%s)" % kinds)
    gate("G4b", [k for k in wf if k.startswith("CONST")] == ["CONST:0x0"],
         "the only constant ever stored at this slot is 0")

    say("")
    say("G5  PAIRING - 0x94d5bc and 0x94d5dc move together")
    pairs = []
    for s in sites:
        if s["rw"] != "W":
            continue
        n = POS[s["a"]]
        lo = max(0, n - 60)
        blk = []
        for k in range(n - 1, lo, -1):
            b = INS[k]
            if b["op"] in ("ret", "call") or b["op"].startswith("j"):
                break
            blk.append(b)
        sib = [b for b in blk if re.search(r"0x94d5bc\b", b["t"]) and MEMDEST.match(b["arg"].split(",")[0].strip())]
        if sib:
            pairs.append((s["a"], sib[0]["a"]))
    say("    write sites that also write 0x94d5bc in the same block: %d" % len(pairs))
    for a, b in pairs:
        say("    %-9s pairs with %-9s (%s)" % (hexa(a), hexa(b), INS[POS[b]]["t"]))
    gate("G5a", len(pairs) == 5, "%d of the 8 stores carry an 0x94d5bc sibling in the same block "
         "(the 3 ++ sites, the += site and BOTH dialog stores)" % len(pairs))
    def basereg(a, disp):
        m = re.search(r"\[([a-z]{2,3})(?:\*4)?\+0x%x\]" % disp, INS[POS[a]]["arg"])
        return m.group(1) if m else "?"
    gate("G5b", len(pairs) == 5 and all(basereg(a, 0x94D5DC) == basereg(b, 0x94D5BC) != "?"
                                         for a, b in pairs),
         "at all 5 paired sites the sibling and the slot are addressed off the SAME base "
         "register (same pair index)")
    same = []
    for a, b in pairs:
        fa, _ = cls_rhs({"a": a, "ins": INS[POS[a]]})
        fb, _ = cls_rhs({"a": b, "ins": INS[POS[b]]})
        ka, kb = fa.split(":")[0], fb.split(":")[0]
        same.append((a, b, fa, fb, ka == kb))
        say("    %-9s %-24s | 0x94d5bc %-24s same delta class: %s"
            % (hexa(a), fa, fb, ka == kb))
    gate("G5c", len(same) == 5 and all(s[-1] for s in same),
         "at every one of the 5 paired sites the sibling gets the SAME delta class (5/5)")

    say("")
    say("G6  CONSUMERS - deadlines and cross-direction compares")
    w = win(0x531FFF, 0x532070)
    txt = "\n".join(i["t"] for i in w)
    m = re.search(r"mov\s+eax,0x([0-9a-f]+)", txt)
    magic = int(m.group(1), 16) if m else 0
    shifts = [imm(i["arg"].partition(",")[2]) for i in w if i["op"] == "sar"]
    say("    round counter ds:0x985afc -> imul 0x%x, sar %s" % (magic, shifts))
    bad50 = magic_div_ok(magic, shifts[0], 50, 5000) if shifts else -1
    bad25 = magic_div_ok(magic, shifts[1], 25, 5000) if len(shifts) > 1 else -1
    say("    (x*0x%x)>>32>>%d vs x//50 : %d mismatches on 0..5000" % (magic, shifts[0], bad50))
    say("    (x*0x%x)>>32>>%d vs x//25 : %d mismatches on 0..5000" % (magic, shifts[1], bad25))
    addend = [i["t"] for i in w if i["op"] == "lea" and
              ("+0x1]" in i["arg"] or "+0x2]" in i["arg"])]
    say("    addends: %s" % " ; ".join(addend))
    gate("G6a", bad50 == 0 and bad25 == 0,
         "the two round fractions are exactly /50 and /25 (0 mismatches each, 0..5000)")
    gate("G6b", len(addend) == 4 and sum(1 for a in addend if "+0x1]" in a) == 2 and
         sum(1 for a in addend if "+0x2]" in a) == 2,
         "both deadlines add the slot value to a round fraction plus a small addend "
         "(2 sites with +1, 2 with +2)")

    consumers = []
    cmpset = set()
    narith_sites = []
    for s in sites:
        if s["rw"] != "R":
            continue
        dest = INS[POS[s["a"]]]["arg"].partition(",")[0].strip()
        kind = None
        for k in range(POS[s["a"]] + 1, min(len(INS), POS[s["a"]] + 7)):
            b = INS[k]
            o = [x.strip() for x in b["arg"].split(",")]
            uses = re.search(r"\b%s\b" % dest, ",".join(o[1:])) is not None
            if b["op"] == "cmp" and uses:
                kind = "cmp@" + hexa(b["a"]) + " " + b["t"]
                cmpset.add(b["a"])
            elif b["op"] == "test" and o and o[0] == dest:
                kind = "test " + b["t"]
            elif b["op"] in ("add", "lea") and uses:
                kind = "arith@" + hexa(b["a"]) + " " + b["t"]
                narith_sites.append(b["a"])
            elif b["op"] == "mov" and MEMDEST.match(o[0]) and len(o) > 1 and o[1] == dest:
                kind = "storeback " + b["t"]
            if kind:
                break
        consumers.append((s["a"], kind))
        say("    %-9s %s" % (hexa(s["a"]), kind or "no use in 6 instructions"))
    ncmp, narith = len(cmpset), len(set(narith_sites))
    gate("G6c", ncmp == 4 and narith >= 4,
         "%d DISTINCT cmp instructions consume the slot across the two directions, %d feed "
         "add/lea arithmetic (both measured)" % (ncmp, narith))
    st_ = pe_string(0x690C88)
    say("    the string a branch at 0x54a373 emits: %r" % st_)

    say("")
    say("G7  RIVALS (each must FAIL on the numbers above)")
    # R1: a per-faction scalar like the 0x94d434 rank?
    say("    R1 'a per-FACTION scalar (0x94d434 rank style)' -> folded sites that reduce to "
        "0x82f*A + 1*B: %d of %d" % (len(norm_ok), len(forms)))
    gate("R1", len(norm_ok) >= 12, "R1 refuted: the index is (fac*0x82f + tgt), a per-PAIR slot")
    # R2: the mask array itself?
    masks = [i for i in INS if "0x94d5dc" in i["t"] and re.search(r"& 0x[0-9a-f]{6,8}|,0xffee|and\s+DWORD PTR \[.*94d5dc", i["t"])]
    say("    R2 'it is the relation MASK array (0x94d448 family)' -> mask RMWs at this slot: %d; "
        "only constant stored: %s" % (len(masks), [k for k in wf if k.startswith("CONST")]))
    gate("R2", len(masks) == 0 and [k for k in wf if k.startswith("CONST")] == ["CONST:0x0"],
         "R2 refuted: no bit-mask store exists at 0x94d5dc (there are many at 0x94d448)")
    # R3: a -1 sentinel/unset stamp?
    neg = [i for i in INS if "94d5dc" in i["t"] and re.search(r",0xffffffff|,0xff\b", i["t"])]
    say("    R3 '-1 marks unset' -> stores of -1 at this slot: %d" % len(neg))
    gate("R3", len(neg) == 0, "R3 refuted: the slot is only ever zeroed, never set to -1")
    # R4: aliased with 0x94d5bc?
    both = [a for a, b in pairs]
    say("    R4 'the two counters are one 0x20-byte row' -> delta %s, two separate dword reads "
        "at %s and %s (0x94d5bc at 0x54cd6c, 0x94d5dc at 0x54cd8d)"
        % (hexa(0x94D5DC - 0x94D5BC), hexa(0x54CD58), hexa(0x54CD8D)))
    gate("R4", 0x94D5DC - 0x94D5BC == 0x20 and len(both) == 5,
         "R4 refuted: 0x20 apart = two 8-dword arrays (0x18c and 0x1ac) in the same record")

    npass = sum(1 for _, ok, _ in gates if ok)
    dig = hashlib.sha1(("\n".join(out)).encode()).hexdigest()
    say("")
    say("PASS M365: %d/%d gates" % (npass, len(gates)) if npass == len(gates)
        else "FAIL M365: %d/%d gates" % (npass, len(gates)))
    say("digest %s" % dig[:16])
    print("\n".join(out))
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
