#!/usr/bin/env python3
"""M217-M221: the hotspot CONTAINER, who owns a list, the row triples' setter, the +0x15c
callback installer, and the 0x671d94 panel's +0xa8.

  M217  the hotspot list is a 3-dword CONTAINER {array@+0, capacity@+4, count@+8} of 24-byte
        items, with an 8-member API: FUN_005e75e5 reset (3 zero stores), FUN_005e760d free+reset,
        FUN_005e7665 wrapper over it (130 sites), FUN_005e764f reset-and-return-self, FUN_005e7678
        ALLOCATE n (imul 0x18 -> FUN_005be090, writes +0/+4/+8), FUN_005e774d ADD (ret 0x18:
        gate,payload,x,y,w,h -> item{+0x14,+0x10,+0,+4,+8=x+w,+0xc=y+h}, index or -1 when
        count>=capacity), FUN_005e78c7 REMOVE-BY-PAYLOAD (reverse scan on +0x10 -> FUN_005e77e7),
        FUN_005e7917 HIT-TEST (publishes +0x14->[out1], +0x10->[out2]).  The adder's arg1/arg2 are
        exactly the two fields M214's dispatcher gates on and dispatches: the container closes the
        click loop.  FUN_005e774d is the ONLY writer of an item's payload/gate in the image.
  M218  the list is a MEMBER, not an object: 130 clear-sites, 21 alloc-sites and 32 add-sites take
        it from this-relative displacements (0x3098 .. 0x402f0) or from stack locals; the dialog's
        +0x3098 list is cleared by 2 dialog ctors, allocated 10 items by FUN_005ef957, reset by
        FUN_005ee350, scanned by the +0x4c dispatcher and NEVER filled by an in-image add-site with
        that displacement; the only non-zero gates in the image are the 8 immediates 1..8 that
        FUN_00486c30 adds to its own list at +0xcc4.
  M219  the 9 row triples are written by 9 THREE-store setters (42 B, 18 insns, 3 args, 1 site
        each), all called in one straight run by ONE function FUN_00459bb0 (1722 B, 1 callsite,
        0 slots): 3 calls pass pointers into a 9-entry 0x2c-stride BSS table at 0x774c38, 6 pass
        (0,0,0).  RETRACTS M215's "one-store setters": the bare `mov ds:imm,eax` is only the FIRST
        of the 3 stores (9 of 27); the other 18 print as `mov dword ptr ds:imm,ecx/edx`.
  M220  FUN_005f3f5b = slot +0x15c of vtable 0x6717cc (70 installs) is a 10-case jump-table switch
        (cmp ,0x9 / jmp [ecx*4+0x5f5731]) and the ONLY writer of the three callback fields
        +0x2210/+0x2224/+0x2234 (3 stores, all the same immediate 0x5f5a11); it is called twice by
        FUN_00406990, the +0x15c of 0x67164c/0x6728c0/0x675cc4/0x6776c8 (396 installs).  Image-wide
        those 3 fields have 0 LOADS and 0 indirect calls carry any displacement in 0x21c0..0x2260:
        the callback slots are WRITE-ONLY, so FUN_005f5a11 is not reached through them.
  M221  the 0x671d94 PANEL (87 slots, 275 installs, size 0x2148 proven by two independent embedded
        arrays) is 74/87 identical to 0x6717cc and 71/87 to the row 0x67194c; it has NO click
        dispatcher (+0x4c = FUN_005f84ff) and its +0xa8 FUN_005f90d7 is a DETACH: it clears
        [this+0xa38], unlinks itself through the 0xa20/0xa24/0xa2c link block and dispatches
        [reg+0xb8] - vs the dialog's +0xa8 FUN_005f5759, which writes the RESULT field [this+0xa40]
        twice and never touches 0xa38/0xa2c.  The dialog embeds a panel at +0x3230 (ctor site).

    python3 scripts/m217_m221_panel.py            # the acceptance run
    python3 scripts/m217_m221_panel.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + programs/terran.exe bytes
(file offset = VA - 0x400000) + ghidra_out/index.csv.  No box time.
Every number the prose quotes is COMPUTED here.
"""
import bisect
import collections
import importlib.util
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
IMG = open(os.path.join(ROOT, "programs/terran.exe"), "rb").read()
PROBE = "--probe" in sys.argv
NORM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
PCS = [pc for pc, _ in NORM]
POS = {pc: i for i, pc in enumerate(PCS)}
NM = dict(NORM)
IDXMAP = {n: (a, z) for a, n, z in IDX}
ST = [r[0] for r in IDX]
TEXT_LO, TEXT_HI = 0x401000, 0x660000
DATA_LO, DATA_HI = 0x660000, 0x9a0000


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o + 4 <= len(IMG) else 0


def in_text(v):
    return TEXT_LO <= v < TEXT_HI


def name_of(addr):
    i = bisect.bisect_right(ST, addr) - 1
    if i >= 0 and addr < IDX[i][0] + IDX[i][2]:
        return IDX[i][1]
    return "X" + hex(addr)


def win(lo, hi):
    return NORM[bisect.bisect_left(PCS, lo):bisect.bisect_left(PCS, hi)]


def body(fn):
    a, z = IDXMAP[fn]
    return win(a, a + z)


def ops(s):
    m = re.match(r"^([a-z0-9*]+)\s*(.*)$", s)
    if not m:
        return s, []
    mn, rest, parts, depth, cur = m.group(1), m.group(2), [], 0, ""
    for ch in rest:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return mn, parts


def mem_disp(op):
    m = re.search(r"\[([^]]*)\]", op)
    if not m:
        return None
    inner = m.group(1)
    d = re.search(r"([+-])0x([0-9a-f]+)\s*$", inner)
    if d:
        return int(d.group(2), 16) * (1 if d.group(1) == "+" else -1)
    if re.search(r"[+-]\d+\s*$", inner):
        return None
    return 0


STOREMN = ("mov", "movzx", "movsx", "add", "and", "or", "xor", "sub", "shl", "shr", "inc", "dec")


def is_mem(op):
    if "[" in op:
        return True
    if re.search(r"\b(byte|word|dword|ptr)\s*(fs|gs|ds|es|ss)?:", op):
        return True
    return bool(re.match(r"^(?:[a-z]{2}:)?0x[0-9a-f]{5,8}$", op))


def bare_abs(op):
    """the a3-form store dest `ds:0x9978ac` - no brackets, no `ptr` keyword."""
    return not op.startswith("[") and bool(re.match(r"^(?:[a-z]{2}:)?0x[0-9a-f]{5,8}$", op))


def stores_of(b):
    out = []
    for pc, s in b:
        mn, parts = ops(s)
        if mn in STOREMN and parts and is_mem(parts[0]):
            out.append((pc, s, parts[0]))
    return out


def census(tok):
    refs = [(pc, s) for pc, s in NORM if tok in s]
    stores = [(pc, s) for pc, s in refs if s.split()[0] in STOREMN and ops(s)[1]
              and is_mem(ops(s)[1][0]) and tok in ops(s)[1][0]]
    return refs, stores


def direct_calls(addr):
    t = "call 0x%x" % addr
    return [(pc, fnof(pc)) for pc, s in NORM if s == t]


def callees(fn):
    out = collections.Counter()
    for pc, s in body(fn):
        m = re.match(r"^call\s+(0x[0-9a-f]+)$", s)
        if m:
            out[int(m.group(1), 16)] += 1
        elif re.match(r"^call\s+", s):
            out["indirect"] += 1
    return out


# ---------------------------------------------------------------- vtable model
bases = collections.Counter()
INSTALLS = collections.defaultdict(list)
RX_INS = re.compile(r"^mov\s+dword ptr \[([^\]]*)\],(0x[0-9a-f]{6,8})$")
for pc, s in NORM:
    m = RX_INS.match(s)
    if not m:
        continue
    v = int(m.group(2), 16)
    if DATA_LO <= v < DATA_HI and in_text(dw(v)):
        bases[v] += 1
        INSTALLS[v].append((pc, fnof(pc), m.group(1)))
B = sorted(bases)
VT = {}
for i, b in enumerate(B):
    nxt = B[i + 1] if i + 1 < len(B) else b + 0x4000
    n = 0
    while 4 * (n + 1) <= (nxt - b) and in_text(dw(b + 4 * (n + 1))):
        n += 1
    VT[b] = (n + 1, bases[b])


def vt_of(addr):
    k = bisect.bisect_right(B, addr) - 1
    if k < 0:
        return None
    b = B[k]
    return (b, addr - b) if addr < b + 4 * VT[b][0] else None


def slots_of(fnaddr):
    pat = struct.pack("<I", fnaddr)
    i, out = 0, []
    while True:
        j = IMG.find(pat, i)
        if j < 0:
            break
        ad = j + 0x400000
        i = j + 1
        if DATA_LO <= ad < DATA_HI:
            v = vt_of(ad)
            if v:
                out.append(v)
    return out


def slots(b):
    return [dw(b + 4 * i) for i in range(VT[b][0])]


def G(ok, desc, cond, numbers):
    ok.append((desc, cond, numbers))


def arg_pushes(pc, n=9):
    a = IDXMAP[fnof(pc)][0]
    i, out = POS[pc] - 1, []
    while i >= 0 and PCS[i] >= a and len(out) < n:
        t = NM[PCS[i]]
        if t.startswith("push "):
            out.append(t[5:])
        elif t.startswith("call "):
            break
        i -= 1
    return out[::-1]


def ecx_operand_before(pc, n=12):
    a = IDXMAP[fnof(pc)][0]
    i = POS[pc] - 1
    while i >= 0 and PCS[i] >= a and (POS[pc] - i) <= n:
        t = NM[PCS[i]]
        m = re.match(r"^add\s+ecx,(0x[0-9a-f]+)$", t)
        if m:
            return ("add", int(m.group(1), 16))
        m = re.match(r"^lea\s+ecx,\[([^]]*)\]$", t)
        if m:
            return ("lea", m.group(1))
        m = re.match(r"^mov\s+ecx,([^,]+)$", t)
        if m:
            return ("mov", m.group(1))
        if t.startswith("call "):
            break
        i -= 1
    return ("?", "")


def receiver(pc):
    """(kind, displacement) for the list/`this` register in front of a call site:
    'member' = this-relative displacement, 'stack' = a stack local, 'loaded'/'reg'/'other'/'?'.
    objdump prints the displacement in hex in BOTH the lea and the `add ecx,imm` form, so a
    hex-only grep finds them all; a DECIMAL grep finds none."""
    kind, val = ecx_operand_before(pc)
    if kind == "add":
        return ("member", val)
    if kind == "lea":
        m = re.match(r"^(\w+)\+0x([0-9a-f]+)$", val)
        if m:
            return ("member", int(m.group(2), 16))
        m = re.match(r"^(\w+)-0x([0-9a-f]+)$", val)
        if m:
            return ("stack", -int(m.group(2), 16))
        if re.match(r"^\w+$", val):
            return ("reg", val)
        return ("other", val)
    if kind == "mov":
        return ("loaded", val)
    return ("?", val)


def disp_hist(tgt):
    h = collections.Counter()
    per = collections.defaultdict(list)
    for pc, fn in direct_calls(tgt):
        k, d = receiver(pc)
        h[k] += 1
        per[k].append((pc, fn, d))
    return h, per


RESULTS = {}


def report(tag):
    ok = RESULTS[tag]
    for desc, cond, numbers in ok:
        print("  [%s] %s" % ("PASS" if cond else "FAIL", desc))
        for line in numbers:
            print("        %s" % line)
    print("  -> %s %s (%d/%d gates)" % (tag, "PASS" if all(c for _, c, _ in ok) else "FAIL",
                                        sum(1 for _, c, _ in ok if c), len(ok)))


# ---------------------------------------------------------------- M217
def m217():
    ok = RESULTS["M217"] = []
    FAM = set(n for a, n, z in IDX if 0x5e7300 <= a < 0x5e7d00)

    # 1. the header is 3 dwords and the reset zeroes exactly those three
    #    (a store census that does not drop the [ebp-..] frame spills counts the prologue as a field write)
    st = [x for x in stores_of(body("FUN_005e75e5")) if "[ebp" not in x[2]]
    disps = sorted(mem_disp(ops(s)[1][0]) for _, s, _ in st)
    vals = [ops(s)[1][1] if len(ops(s)) > 1 else "?" for _, s, _ in st]
    G(ok, "FUN_005e75e5 zeroes the container header: 3 stores, disps [0,4,8], all immediate 0",
      len(st) == 3 and disps == [0, 4, 8] and all(v == "0x0" for v in vals),
      ["stores=%d disps=%s vals=%s" % (len(st), disps, vals)])

    # 2. FUN_005e7678 ALLOCATES the item array: n * 0x18 bytes, capacity -> +4, count -> 8
    b = body("FUN_005e7678")
    st = [x for x in stores_of(b) if "[ebp" not in x[2]]
    disps = sorted(mem_disp(ops(s)[1][0]) for _, s, _ in st)
    cal = dict(callees("FUN_005e7678"))
    G(ok, "FUN_005e7678 (ret 0x4) allocates n*0x18 and writes +0 ptr / +4 capacity / +8 count=0",
      b[-1][1] == "ret 0x4" and disps == [0, 4, 8] and cal == {0x5e760d: 1, 0x5be090: 1}
      and any(s == "imul eax,eax,0x18" for _, s in b)
      and any(s == "mov dword ptr [eax+0x4],ecx" for _, s, _ in st),
      ["stores=%d disps=%s callees=%s ret=%s" % (len(st), disps, sorted(hex(k) for k in cal), b[-1][1])])

    # 3. FUN_005e774d is the ADDER and its argument map is the gate/payload/x/y/w/h sextuple
    b = body("FUN_005e774d")
    txt = [s for _, s in b]
    PAIRS = [("mov dword ptr [edx],eax", "mov eax,dword ptr [ebp+0x10]", "item+0x00 = arg3 (x)"),
             ("mov dword ptr [ecx+0x4],edx", "mov edx,dword ptr [ebp+0x14]", "item+0x04 = arg4 (y)"),
             ("mov dword ptr [ecx+0x8],eax", "add eax,dword ptr [ebp+0x18]", "item+0x08 = arg3+arg5 (x+w)"),
             ("mov dword ptr [eax+0xc],edx", "add edx,dword ptr [ebp+0x1c]", "item+0x0c = arg4+arg6 (y+h)"),
             ("mov dword ptr [eax+ecx*1+0x14],edx", "mov edx,dword ptr [ebp+0x8]", "item+0x14 = arg1 (the GATE M214 tests ==0)"),
             ("mov dword ptr [edx+eax*1+0x10],ecx", "mov ecx,dword ptr [ebp+0xc]", "item+0x10 = arg2 (the PAYLOAD M214 dispatches)")]
    rows, good = [], 0
    for store, load, what in PAIRS:
        # the same instruction text appears twice in this body (count++ writes [ecx+0x8] too),
        # so require THAT occurrence's own source, not the first textual match
        cand = [i for i, t in enumerate(txt) if t == store]
        hit = [j for j in cand if load in txt[max(0, j - 3):j]]
        good += 1 if hit else 0
        rows.append("%-42s store@%s from '%s' found=%s" % (what, [hex(b[j][0]) for j in hit], load, bool(hit)))
    st = [x for x in stores_of(b) if "[ebp" not in x[2]]
    adisp = sorted(mem_disp(ops(s)[1][0]) for _, s, _ in st)
    G(ok, "FUN_005e774d (ret 0x18) writes the 6 item fields (each from its argument) plus count at +8",
      good == 6 and len(st) == 7 and adisp == [0, 4, 8, 8, 0xc, 0x10, 0x14], rows +
      ["stores=%d disps=%s ret=%s" % (len(st), adisp, b[-1][1])])

    # 4. capacity guard + count++
    need = ["mov edx,dword ptr [eax+0x8]", "cmp edx,dword ptr [ecx+0x4]", "or eax,0xffffffff",
            "add eax,0x1", "mov dword ptr [ecx+0x8],eax"]
    have = [n in txt for n in need]
    G(ok, "the adder returns -1 when count >= capacity and increments count otherwise",
      all(have) and any(s.startswith("jl ") for _, s in b),
      ["%s=%s" % (n, h) for n, h in zip(need, have)])

    # 5. FUN_005e7917 publishes the two fields to the caller's out-params
    b = body("FUN_005e7917")
    txt = [s for _, s in b]
    PUB = [("mov ecx,dword ptr [ecx+edx*1+0x14]", "mov dword ptr [eax],ecx", "mov eax,dword ptr [ebp+0x10]", "gate -> out1"),
           ("mov ecx,dword ptr [ecx+edx*1+0x10]", "mov dword ptr [eax],ecx", "mov eax,dword ptr [ebp+0x14]", "payload -> out2")]
    pubs = [i for i, t in enumerate(txt) if t == "mov dword ptr [eax],ecx"]
    rows, hits = [], []
    for ld, stl, outp, what in PUB:
        h = [i for i in pubs if ld in txt[max(0, i - 4):i] and outp in txt[max(0, i - 4):i]]
        hits += h
        rows.append("%-14s %-40s out-param %s publish@%s found=%s" % (
            what, ld, outp, [hex(b[i][0]) for i in h], bool(h)))
    G(ok, "FUN_005e7917 hands item+0x14 to arg3 and item+0x10 to arg4 (M214's gate/payload pair)",
      all("found=True" in r for r in rows) and len(set(hits)) == 2, rows)

    # 6. containment: only the adder writes an item's payload/gate, image-wide
    W, R = collections.Counter(), collections.Counter()
    for pc, s in NORM:
        if not re.match(r"^imul\s+\w+,\w+,0x18$", s):
            continue
        for _, t in NORM[POS[pc] + 1:POS[pc] + 6]:
            if not re.search(r"\*1\+0x1[04]\]", t):
                continue
            if t.split()[0].startswith("f") or "qword" in t:
                continue  # x87 double-array arithmetic reuses the same index form
            fn = fnof(pc)
            if ops(t)[0] in STOREMN and is_mem(ops(t)[1][0]) and not ops(t)[1][0].startswith("[ebp"):
                W[fn] += 1
            else:
                R[fn] += 1
    G(ok, "image-wide, FUN_005e774d is the ONLY writer of a 24-B item's +0x10/+0x14 (2 stores); "
          "every reader is inside the 0x5e7300-0x5e7d00 family",
      list(W.items()) == [("FUN_005e774d", 2)] and set(R) <= FAM and len(R) == 6,
      ["writers=%s" % sorted("%s x%d" % (k, v) for k, v in W.items()),
       "readers=%s" % sorted("%s x%d" % (k, v) for k, v in R.items())])

    # 7. FUN_005e78c7 removes by PAYLOAD, scanning downward, via FUN_005e77e7
    b = body("FUN_005e78c7")
    txt = [s for _, s in b]
    G(ok, "FUN_005e78c7 (ret 0x4) scans count-1..0 for item+0x10 == arg1 and calls FUN_005e77e7 on the index",
      "mov ecx,dword ptr [eax+0x8]" in txt and "sub ecx,0x1" in txt
      and "mov eax,dword ptr [edx+eax*1+0x10]" in txt and "cmp eax,dword ptr [ebp+0x8]" in txt
      and dict(callees("FUN_005e78c7")) == {0x5e77e7: 1} and b[-1][1] == "ret 0x4",
      ["callees=%s ret=%s sites=%d" % (sorted(hex(k) for k in callees("FUN_005e78c7")), b[-1][1],
                                       len(direct_calls(0x5e78c7)))])

    # 8. the 19-byte wrapper is the ctor/clear everyone calls
    cal = dict(callees("FUN_005e7665"))
    G(ok, "FUN_005e7665 is a 9-insn wrapper whose only callee is the free+reset FUN_005e760d, 130 call sites",
      len(body("FUN_005e7665")) == 9 and cal == {0x5e760d: 1} and len(direct_calls(0x5e7665)) == 130,
      ["insns=%d callees=%s callsites=%d size=%d" % (len(body("FUN_005e7665")),
       sorted(hex(k) for k in cal), len(direct_calls(0x5e7665)), IDXMAP["FUN_005e7665"][1])])
    report("M217")


# ---------------------------------------------------------------- M218
def m218():
    ok = RESULTS["M218"] = []
    hclear, perclear = disp_hist(0x5e7665)
    total = sum(hclear.values())
    mem = [d for _, _, d in perclear.get("member", [])]
    stk = [d for _, _, d in perclear.get("stack", [])]
    G(ok, "the 130 clear-sites take the list from this-relative members or stack locals (a MEMBER, not an object)",
      total == 130 and hclear["member"] >= 30 and hclear["stack"] >= 30 and len(set(mem)) >= 12,
      ["kinds=%s (sum=%d)" % (sorted("%s=%d" % (k, v) for k, v in hclear.items()), total),
       "distinct member displacements=%d: %s" % (len(set(mem)), sorted(hex(d) for d in set(mem))),
       "stack locals=%d, frame offsets %s..%s" % (len(stk), hex(min(stk)), hex(max(stk)) if stk else "?")])

    halloc, peralloc = disp_hist(0x5e7678)
    caps = [(fn, receiver(pc)[1], arg_pushes(pc, 3)[-1]) for pc, fn in direct_calls(0x5e7678)]
    imm = sorted(set(int(v, 16) for _, _, v in caps if v.startswith("0x")))
    G(ok, "the 21 alloc-sites size each list explicitly (1..0x100 items) on a member or a stack local",
      len(caps) == 21 and imm and min(imm) == 1 and max(imm) == 0x100,
      ["kinds=%s" % sorted("%s=%d" % (k, v) for k, v in halloc.items()),
       "immediate capacities (%d distinct)=%s" % (len(imm), sorted(hex(x) for x in imm)),
       "register-passed capacities=%s" % sorted("%s %s" % (f, v) for f, d, v in caps if not v.startswith("0x"))])

    hadd, peradd = disp_hist(0x5e774d)
    gates = [(pc, fn, receiver(pc), arg_pushes(pc, 6)[-1]) for pc, fn in direct_calls(0x5e774d)]
    immgates = sorted(set(int(v, 16) for _, _, _, v in gates if v.startswith("0x")))
    nonzero = [g for g in gates if g[3].startswith("0x") and int(g[3], 16) != 0]
    owners = sorted(set(g[1] for g in nonzero))
    one2eight = sorted(set(int(g[3], 16) for g in nonzero if int(g[3], 16) <= 8))
    G(ok, "of the 32 add-sites the gate operand is either an immediate or a register; the non-zero "
          "immediates are 1..8 (one owner, its own list) plus 0x45",
      len(gates) == 32 and sum(hadd.values()) == 32 and one2eight == [1, 2, 3, 4, 5, 6, 7, 8]
      and len(owners) == 2 and 0x45 in immgates,
      ["kinds=%s" % sorted("%s=%d" % (k, v) for k, v in hadd.items()),
       "gate immediates=%s" % sorted(hex(x) for x in immgates),
       "non-zero-gate sites=%d owners=%s" % (len(nonzero), owners),
       "register-gate sites=%d" % sum(1 for g in gates if not g[3].startswith("0x"))])

    # the dialog's own list at +0x3098, end to end
    # Ghidra's index DOES name the SEH unwind stubs (Unwind@...), so "is it an indexed function"
    # does not exclude them - exclude the stub NAMES, and require the 2 real sites to be the ctors.
    cl = [(pc, fn) for pc, fn, d in perclear.get("member", []) if d == 0x3098 and not fn.startswith("Unwind@")]
    clunw = [pc for pc, fn, d in perclear.get("member", []) if d == 0x3098 and fn.startswith("Unwind@")]
    al = [(pc, fn, arg_pushes(pc, 3)[-1]) for pc, fn, d in peralloc.get("member", []) if d == 0x3098]
    ad = [pc for pc, fn, d in peradd.get("member", []) if d == 0x3098]
    rst = [pc for pc, fn, d in disp_hist(0x5e764f)[1].get("member", []) if d == 0x3098]
    sc = [pc for pc, fn, d in disp_hist(0x5e7917)[1].get("member", []) if d == 0x3098]
    G(ok, "the dialog's list at this+0x3098: cleared by 2 ctors, allocated 10 items by FUN_005ef957, "
          "reset by FUN_005ee350, scanned by the +0x4c dispatcher, and NEVER filled by an add-site",
      len(cl) == 2 and sorted(f for _, f in cl) == ["FUN_00405f60", "FUN_00421da0"]
      and len(al) == 1 and al and al[0][2] == "0xa" and len(ad) == 0 and len(rst) == 1 and len(sc) == 1,
      ["clear sites (ctors)=%s" % [(hex(p), f) for p, f in cl],
       "SEH unwind stubs that re-clear the same member=%s" % [hex(x) for x in clunw],
       "alloc site=%s" % [(hex(p), f, c) for p, f, c in al],
       "add sites=%d reset=%s scan=%s" % (len(ad), [hex(x) for x in rst], [hex(x) for x in sc])])

    memadd = sorted(set(d for _, _, d in peradd.get("member", [])))
    G(ok, "no add-site targets a list at +0x3098: the dialog's list is filled through a "
          "register-passed list pointer (loaded-value receivers)",
      0x3098 not in memadd and (hadd["loaded"] + hadd["reg"]) > 0,
      ["add-site member displacements=%s" % sorted(hex(d) for d in memadd),
       "loaded/reg receivers=%d of 32" % (hadd["loaded"] + hadd["reg"]),
       "loaded-receiver fns=%s" % sorted(set(f for _, f, _ in peradd.get("loaded", [])))])
    report("M218")


# ---------------------------------------------------------------- M219
def m219():
    ok = RESULTS["M219"] = []
    SET = [0x45a4d0 + 0x30 * i for i in range(9)]
    rows, allstores, bare = [], [], 0
    for i, ad in enumerate(SET):
        f = name_of(ad)
        b = body(f)
        st = stores_of(b)
        allstores += st
        base = 0x9978ac + 0xc * i
        disps = sorted(int(re.search(r"0x([0-9a-f]+)$", d).group(1), 16) - base for _, s, d in st)
        n_bare = sum(1 for _, s, d in st if bare_abs(d))
        bare += n_bare
        args = sorted(set(re.findall(r"\[ebp\+?(0x[0-9a-f]+)\]", " ".join(s for _, s in b))))
        rows.append("%s base=%s size=%d insns=%d stores=%d rel-disps=%s bare=%d frame-reads=%s sites=%d slots=%s" % (
            f, hex(base), IDXMAP[f][1], len(b), len(st), disps, n_bare, args,
            len(direct_calls(ad)), slots_of(ad)))
    G(ok, "the 9 setters are 42-B THREE-argument, THREE-store triple setters (RETRACTION of M215's 'one-store setters')",
      len(rows) == 9 and all("stores=3" in r and "insns=18" in r and "size=42" in r and "sites=1" in r
                             and "slots=[]" in r and "rel-disps=[0, 4, 8]" in r for r in rows), rows)

    G(ok, "27 stores write the 27 dwords 0x9978ac..0x997914; 9 of them are the BARE a3 form a bracket-only classifier misses",
      len(allstores) == 27 and bare == 9,
      ["total stores=%d bare-form=%d bracketed=%d" % (len(allstores), bare, len(allstores) - bare),
       "bare sites=%s" % [hex(pc) for pc, s, d in allstores if bare_abs(d)]])

    allcall = collections.Counter()
    for ad in SET:
        for pc, fn in direct_calls(ad):
            allcall[fn] += 1
    G(ok, "every setter has exactly ONE call site and all 9 are inside ONE function FUN_00459bb0 (1722 B, 450 insns, 1 callsite, 0 vtable slots)",
      len(allcall) == 1 and sum(allcall.values()) == 9 and IDXMAP["FUN_00459bb0"][1] == 1722
      and len(body("FUN_00459bb0")) == 450 and len(direct_calls(0x459bb0)) == 1 and slots_of(0x459bb0) == [],
      ["callers=%s" % dict(allcall), "FUN_00459bb0 size=%d insns=%d sites=%d slots=%s" % (
          IDXMAP["FUN_00459bb0"][1], len(body("FUN_00459bb0")), len(direct_calls(0x459bb0)), slots_of(0x459bb0))])

    clean, TAB, ZERO = [], [], []
    for ad in SET:
        for pc, fn in direct_calls(ad):
            p = arg_pushes(pc, 3)
            clean.append(NM[PCS[POS[pc] + 1]] if POS[pc] + 1 < len(PCS) else "")
            vals = [v for v in p if v.startswith("0x")]
            if vals and all(0x774c38 <= int(v, 16) <= 0x774dbc for v in vals):
                TAB.append((pc, vals))
            else:
                ZERO.append((pc, vals))
    tabvals = sorted(int(v, 16) for _, vs in TAB for v in vs)
    strides = sorted(set(tabvals[i + 1] - tabvals[i] for i in range(len(tabvals) - 1)))
    G(ok, "the run passes 3 stack args per setter: 3 calls hand over pointers into one 9-entry 0x2c-stride BSS table at 0x774c38, 6 pass (0,0,0)",
      all(c == "add esp,0xc" for c in clean) and len(tabvals) == 9
      and tabvals == [0x774c38 + 0x2c * i for i in range(9)] and len(ZERO) == 6,
      ["cleanup-after-every-site=%s" % sorted(set(clean)),
       "table pointers=%s" % [hex(v) for v in tabvals],
       "uniform stride=%s" % [hex(x) for x in strides],
       "zero-arg sites=%d (%s)" % (len(ZERO), [hex(p) for p, _ in ZERO])])

    FILEMAP_END = 0x400000 + len(IMG)
    G(ok, "both the triples and the table the 3 calls point at are ABOVE the file-mapped image (BSS at runtime) - runtime setter state, not load-time data",
      bool(tabvals) and min(tabvals) > FILEMAP_END and 0x9978ac > FILEMAP_END,
      ["file-mapped image ends at %s; table base %s, triple base 0x9978ac" % (
          hex(FILEMAP_END), hex(min(tabvals)) if tabvals else "?")])

    f = "FUN_005fb1a5"
    RXD = re.compile(r"\+0x([0-9a-f]{3,4})\]")
    grp, offgrid = collections.Counter(), 0
    for pc, s in body(f):
        m = RXD.search(s)
        if m and 0xae0 <= int(m.group(1), 16) < 0xb4c:
            v = int(m.group(1), 16)
            grp[(v - 0xae0) // 0xc] += 1
            if (v - 0xae0) % 4 == 0:
                offgrid += 1
    G(ok, "the row class's own vmethod +0x30 (FUN_005fb1a5 of vtable 0x67194c) is a consumer of the 0xae0..0xb48 copy: every site lands on the 4-byte grid inside the 9 triples",
      ("0x67194c", 0x30) in [(hex(a), d) for a, d in slots_of(0x5fb1a5)] and bool(grp) and offgrid == sum(grp.values()),
      ["slots=%s sites=%d on-grid=%d groups=%s" % (sorted("%s+%d" % (hex(a), d) for a, d in slots_of(0x5fb1a5)),
       sum(grp.values()), offgrid, sorted("group%d:%d" % (k, v) for k, v in grp.items()))])
    report("M219")


# ---------------------------------------------------------------- M220
def m220():
    ok = RESULTS["M220"] = []
    sl = sorted("%s+%d" % (hex(a), d) for a, d in slots_of(0x5f3f5b))
    G(ok, "FUN_005f3f5b is slot +0x15c of exactly one vtable (0x6717cc, 95 slots, 70 installs)",
      sl == ["0x6717cc+348"] and VT[0x6717cc] == (95, 70),
      ["slots=%s vt(0x6717cc)=%s" % (sl, VT[0x6717cc])])

    b = body("FUN_005f3f5b")
    txt = [s for _, s in b]
    tbl = [dw(0x5f5731 + 4 * i) for i in range(10)]
    a0, z0 = IDXMAP["FUN_005f3f5b"]
    inside = all(a0 <= t < a0 + z0 for t in tbl)
    G(ok, "it is a 10-case jump-table switch: cmp [ebp-0xf4],0x9 + jmp [ecx*4+0x5f5731] with all 10 targets inside the function",
      "cmp dword ptr [ebp-0xf4],0x9" in txt and "jmp dword ptr [ecx*4+0x5f5731]" in txt and inside,
      ["table=%s all-inside=%s fn=%s..%s" % ([hex(t) for t in tbl], inside, hex(a0), hex(a0 + z0))])

    refs, _ = census("0x5f5a11")
    # census()'s store half tests whether the DEST carries the token - right for a global, wrong for
    # a VALUE being stored: here the token is the SOURCE, so classify the store by its source operand.
    stores = [(pc, s) for pc, s in refs if ops(s)[0] in STOREMN and len(ops(s)[1]) > 1
              and "0x5f5a11" in ops(s)[1][1]]
    dests = sorted(set(ops(s)[1][0] for _, s in stores))
    G(ok, "the image holds exactly 3 references to 0x5f5a11 and all 3 are stores of it into +0x2210 / +0x2224 / +0x2234, all inside FUN_005f3f5b",
      len(refs) == 3 and len(stores) == 3 and len(dests) == 3
      and all(fnof(pc) == "FUN_005f3f5b" for pc, _ in refs),
      ["refs=%d stores=%d dests=%s" % (len(refs), len(stores), dests),
       "%s" % ["%08x %-16s %s" % (pc, fnof(pc), s) for pc, s in refs]])

    loads, calls, tot = 0, [], collections.Counter()
    for pc, s in NORM:
        for disp in ("+0x2210]", "+0x2224]", "+0x2234]"):
            if disp in s:
                tot[disp[:-1]] += 1
                if ops(s)[0] not in STOREMN:
                    loads += 1
        if s.startswith("call"):
            m = re.search(r"\+0x([0-9a-f]{3,4})\]", s)
            if m and 0x21c0 <= int(m.group(1), 16) <= 0x2260:
                calls.append((pc, s))
    G(ok, "those 3 fields are WRITE-ONLY: 0 loads of any width, and no indirect call anywhere carries a displacement in 0x21c0..0x2260",
      loads == 0 and not calls and tot["+0x2210"] == 2 and tot["+0x2224"] == 1 and tot["+0x2234"] == 1,
      ["refs=%s loads=%d calls-in-window=%s" % (dict((k, v) for k, v in tot.items()), loads, [hex(p) for p, _ in calls]),
       "the 2 +0x2210 refs = the callback store + the clear-loop store in FUN_00406990; push 0x2210 at 0x528000 "
       "and cmp eax,0x2210 at 0x52d1bf are the netcode LOCK message id (a value collision, not an offset)"])

    sl2 = sorted(slots_of(0x406990))
    cal = [(pc, fn) for pc, fn in direct_calls(0x5f3f5b)]
    G(ok, "FUN_00406990 is slot +0x15c of the 4 sibling vtables (396 installs) and calls FUN_005f3f5b twice, so the install runs for both dialog classes",
      sl2 == [(0x67164c, 0x15c), (0x6728c0, 0x15c), (0x675cc4, 0x15c), (0x6776c8, 0x15c)]
      and sum(VT[a][1] for a, _ in sl2) == 396 and len(cal) == 2,
      ["slots=%s installs=%d" % (sorted("%s+%d" % (hex(a), d) for a, d in sl2), sum(VT[a][1] for a, _ in sl2)),
       "call sites=%s in %s" % ([hex(p) for p, _ in cal], sorted(set(f for _, f in cal)))])

    G(ok, "FUN_005f5a11 has 0 direct calls and 0 vtable slots: those 3 stores are its only reachability in the image",
      len(direct_calls(0x5f5a11)) == 0 and slots_of(0x5f5a11) == [],
      ["direct calls=%d slots=%s size=%d insns=%d" % (len(direct_calls(0x5f5a11)), slots_of(0x5f5a11),
       IDXMAP["FUN_005f5a11"][1], len(body("FUN_005f5a11")))])
    report("M220")


# ---------------------------------------------------------------- M221
def m221():
    ok = RESULTS["M221"] = []
    n, ins = VT[0x671d94]
    sl = slots(0x671d94)
    same = {}
    for b2 in (0x6717cc, 0x67164c, 0x67194c):
        k = min(n, VT[b2][0])
        same[b2] = sum(1 for i in range(k) if sl[i] == dw(b2 + 4 * i))
    G(ok, "vtable 0x671d94 = 87 slots / 275 installs, 74/87 identical to 0x6717cc, 63/87 to 0x67164c, 71/87 to the row 0x67194c",
      (n, ins) == (87, 275) and same[0x6717cc] == 74 and same[0x67164c] == 63 and same[0x67194c] == 71,
      ["slots=%d installs=%d identical=%s" % (n, ins, sorted("%s:%d/%d" % (hex(k), v, n) for k, v in same.items()))])

    G(ok, "the panel has NO click dispatcher: +0x4c is FUN_005f84ff (not the click dispatcher FUN_005f6aa3) and +0xa8 is FUN_005f90d7 (not FUN_005f5759)",
      sl[0x4c // 4] == 0x5f84ff and sl[0xa8 // 4] == 0x5f90d7
      and 0x671d94 not in [a for a, _ in slots_of(0x5f6aa3)],
      ["+0x4c=%s +0xa8=%s click-dispatcher vtables=%s" % (name_of(sl[0x4c // 4]), name_of(sl[0xa8 // 4]),
       sorted(hex(a) for a, _ in slots_of(0x5f6aa3)))])

    b = body("FUN_005f6b8c")
    txt = [s for _, s in b]
    RXD = re.compile(r"\+0x([0-9a-f]{3,4})\]")
    blk, hi = collections.Counter(), 0
    for _, s, d in stores_of(b):
        m = RXD.search(d)
        if m:
            v = int(m.group(1), 16)
            hi = max(hi, v)
            if 0xa14 <= v <= 0xaa0:
                blk[v] += 1
    cal = dict(callees("FUN_005f6b8c"))
    G(ok, "the panel ctor FUN_005f6b8c builds 2 row subobjects (+0xaac, +0x15f8) plus the CPane subobject (0x671d8c, 3 slots, 268 installs) at +0x444 and initialises the 0xa14..0xaa0 block",
      IDXMAP["FUN_005f6b8c"][1] == 605 and len(b) == 136 and len(direct_calls(0x5f6b8c)) == 16
      and "mov dword ptr [eax],0x671d94" in txt and "mov dword ptr [ecx+0x444],0x671d8c" in txt
      and "add ecx,0xaac" in txt and "add ecx,0x15f8" in txt and txt.count("call 0x5faec0") == 2
      and cal == {0x5faec0: 2, 0x5e3b80: 1} and VT[0x671d8c] == (3, 268)
      and bool(blk) and min(blk) >= 0xa14 and max(blk) <= 0xaa0,
      ["size=%d insns=%d sites=%d callees=%s" % (IDXMAP["FUN_005f6b8c"][1], len(b), len(direct_calls(0x5f6b8c)),
       sorted("%s x%d" % (hex(k) if isinstance(k, int) else k, v) for k, v in cal.items())),
       "row-ctor calls=%s vt(0x671d8c)=%s block stores 0x%x..0x%x n=%d distinct=%d highest field store=0x%x" % (
           [hex(pc) for pc, s in b if s == "call 0x5faec0"], VT[0x671d8c], min(blk), max(blk),
           sum(blk.values()), len(blk), hi)])

    per = disp_hist(0x5f6b8c)[1]["member"]
    runs = {}
    for fnc in sorted(set(fn for _, fn, _ in per)):
        ds = sorted(d for _, fn, d in per if fn == fnc)
        if len(ds) > 1:
            runs[fnc] = (ds, sorted(set(ds[i + 1] - ds[i] for i in range(len(ds) - 1))))
    uniform = [fnc for fnc, (ds, dl) in runs.items() if dl == [0x214c]]
    G(ok, "the panel is 0x214c bytes: two independent containers embed panels at a uniform 0x214c stride (3 in FUN_00409e70, 4 in FUN_004947c0), row 2 ends at 0x15f8+0xb4c = 0x2144 and the ctor still writes +0x2144/+0x2148",
      len(uniform) >= 2 and 0x15f8 + 0xb4c == 0x2144 and hi == 0x2148,
      ["%s" % ["%s disps=%s deltas=%s" % (fnc, [hex(x) for x in ds], [hex(x) for x in dl])
               for fnc, (ds, dl) in sorted(runs.items())],
       "uniform-0x214c containers=%s highest ctor store=0x%x row2 end=0x%x" % (uniform, hi, 0x15f8 + 0xb4c)])

    def field(fn, disps):
        c = collections.Counter()
        for _, s, d in stores_of(body(fn)):
            m = re.search(r"\+0x([0-9a-f]{3,4})\]", d)
            if m and int(m.group(1), 16) in disps:
                c[int(m.group(1), 16)] += 1
        return c
    c90, c57 = field("FUN_005f90d7", {0xa38, 0xa2c, 0xa40}), field("FUN_005f5759", {0xa38, 0xa2c, 0xa40})
    ind = {f: dict(callees(f)).get("indirect", 0) for f in ("FUN_005f90d7", "FUN_005f5759")}
    G(ok, "the two +0xa8 implementations differ: the panel's clears [this+0xa38], unlinks itself through the 0xa20/0xa24/0xa2c link block and dispatches [reg+0xb8]; the dialog's writes the RESULT field [this+0xa40] (4 stores) and never touches 0xa38/0xa2c",
      c90[0xa38] == 1 and c90[0xa2c] == 2 and c90[0xa40] == 0 and c57[0xa40] == 4
      and c57[0xa38] == 0 and c57[0xa2c] == 0
      and any(s == "call dword ptr [edx+0xb8]" for _, s in body("FUN_005f90d7"))
      and any(s == "cmp eax,dword ptr [edx+0xa20]" for _, s in body("FUN_005f90d7"))
      and any(s == "cmp eax,dword ptr [edx+0xa24]" for _, s in body("FUN_005f90d7"))
      and ind == {"FUN_005f90d7": 7, "FUN_005f5759": 3},
      ["FUN_005f90d7 stores=%s insns=%d indirect=%d slots=%s" % (dict((hex(k), v) for k, v in c90.items()),
       len(body("FUN_005f90d7")), ind["FUN_005f90d7"], sorted("%s+%d" % (hex(a), d) for a, d in slots_of(0x5f90d7))),
       "FUN_005f5759 stores=%s insns=%d indirect=%d slots=%s" % (dict((hex(k), v) for k, v in c57.items()),
       len(body("FUN_005f5759")), ind["FUN_005f5759"], sorted("%s+%d" % (hex(a), d) for a, d in slots_of(0x5f5759)))])

    dial = [(pc, d) for pc, fn, d in per if fn == "FUN_00405ef0"]
    G(ok, "the dialog class ctor FUN_00405ef0 embeds exactly one panel, at this+0x3230",
      len(dial) == 1 and dial[0][1] == 0x3230,
      ["sites=%s disp=%s" % ([hex(p) for p, _ in dial], dial[0][1] if dial else None)])
    report("M221")


for tag, fn in (("M217", m217), ("M218", m218), ("M219", m219), ("M220", m220), ("M221", m221)):
    fn()
print()
res = []
for tag in ("M217", "M218", "M219", "M220", "M221"):
    v = RESULTS[tag]
    res.append("%s=%s" % (tag, "PASS" if all(c for _, c, _ in v) else "FAIL"))
tot = sum(len(RESULTS[t]) for t in RESULTS)
got = sum(sum(1 for _, c, _ in RESULTS[t] if c) for t in RESULTS)
print("SUMMARY %s (%d/%d gates)" % (" ".join(res), got, tot))
sys.exit(0 if got == tot else 1)
