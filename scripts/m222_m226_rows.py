#!/usr/bin/env python3
"""M222-M226: who fills a hotspot list, the unreached callback, the 0x774c38 grid,
the panel's detach dispatch and its row vmethod.

  M222  FUN_00403b00 is the image's only ADD WRAPPER: `mov [ebp-0x4],ecx` in its prologue, 3 args
        (ret 0xc), and its 6 pushes to FUN_005e774d are exactly (arg1, arg2, rect+0, rect+4,
        rect+8-rect+0, rect+0xc-rect+4) - a (gate, payload, RECT) call form.  All 22 sites in 16
        functions pass the container as the caller's own ecx plus ONE of 8 member displacements
        (a48/cc4/e40/15e0/28ac/5994/12758/12764); 1 site (FUN_00403ad0) forwards ecx bare.  The
        dialog's this+0x3098 list carries NONE of them: it is allocated and reset but never
        appended, and its fill sites are the 4 register-passed adders, which all run on the GLOBAL
        pane object at 0x6a9480 (FUN_0041f310 = its slot +0x30 vmethod, 3 callers all `mov
        ecx,0x6a9480`; FUN_004105b0's container is this+0x402f0, FUN_00411840/FUN_00415d10/FUN_0040f830
        take theirs from this too).  RETRACTS M218's "the only non-zero gates are the 8 immediates
        1..8": the immediates sit in the PAYLOAD slot (item+0x10); the gate slot (item+0x14) is
        filled from pointers, loaded values and rect locals.
  M223  FUN_005f5a11 is reached by NO mechanism: 0 direct calls, 0 vtable slots, 0 data occurrences
        of the dword 0x5f5a11 outside the 3 store immediates, 0 loads and 0 lea-address-takes of the
        3 fields it was installed into, 0 indirect calls with any displacement in 0x21c0..0x2260, and
        0 rep movs in the 0x21c0..0x2260 window.  Its body proves it is a method of the MODAL object
        class: it reads ds:0x9977f0 (the handle the pump publishes) and gates on [h+0x2350] in {1,-1}
        before reading [h+0x21d0], [h+0x30a8] and dispatching [reg+0xe0] / [reg+8].
  M224  FUN_00459bb0 (1722 B) has exactly ONE call site (0x45a755, in FUN_0045a740, itself 56 B with
        1 caller) and 39 calls in a straight run: 15 to FUN_00455c70, 12 to a 0x45a320..0x45a6e0
        family that takes GRID pointers, and the 9 row-triple setters - M219's split CONFIRMED, 3
        receive the 0x2c-stride grid 0x774c38 + 0x2c*i (i=0..8) three entries at a time and 6 receive
        (0,0,0); the grid is all-zero in the image (BSS).  Its only other window reference FUN_0041f450
        does not read the grid, it INSTALLS it: 4 stores of 0x774c0c (one entry below the grid base)
        and 1 of 0x774a80 (nine entries below) into [obj+0xb24], which other functions then load.
  M225  FUN_005f90d7 (panel slot +0xa8, DETACH) dispatches 7 times: [reg+0xb8] x2 on the two link
        objects it unlinks, [reg+0xf0] on itself, [reg+0x5c] then [reg+0x1c] on a third object, and
        [reg+0x2144] x2 - an offset BIGGER than every vtable slot in the image (max 0x178 over 188
        vtables), so it is a call through the panel's own last field: 17 functions write that field and
        7 read or call it, and the DETACH calls it twice.
  M226  the row class's slot +0x30 FUN_005fb1a5 (4202 B, 1000 insns) is a DRAW: 14 of its calls
        switch ecx to the CPane subobject (`add ecx,0x444`) and it reads the 9 groups as a dword
        array [obj+eax*4+0xabc] plus the 0xac8/0xa88/0xa8c/0xa7c/0x98 fields, emitting text through
        FUN_005dd09c x5 / FUN_005c153f x5 / FUN_005ca7c3 x4 and calling only ONE indirect, [reg+0x14].

    python3 scripts/m222_m226_rows.py            # the acceptance run

Static only: scratch/m574/text.txt + programs/terran.exe bytes + ghidra_out/index.csv.  No box time.
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



# ---------------------------------------------------------------- M222-M226 helpers
def argw(pc, n):
    """walk back from a call site collecting push operands; the NEAREST push is arg1."""
    a = IDXMAP[fnof(pc)][0]
    i, out = POS[pc] - 1, []
    while i >= 0 and PCS[i] >= a and len(out) < n:
        t = NM[PCS[i]]
        if t.startswith("push "):
            out.append(t[5:])
        elif t.startswith("call "):
            break
        i -= 1
    return out


def argw_pc(pc, n):
    """like argw but returns (operand, the pc of ITS OWN push) so provenance resolves there."""
    a = IDXMAP[fnof(pc)][0]
    i, out = POS[pc] - 1, []
    while i >= 0 and PCS[i] >= a and len(out) < n:
        t = NM[PCS[i]]
        if t.startswith("push "):
            out.append((t[5:], PCS[i]))
        elif t.startswith("call "):
            break
        i -= 1
    return out


def definsn(fn, pc, reg, back=60):
    a = IDXMAP[fn][0]
    i = POS[pc] - 1
    while i >= 0 and PCS[i] >= a and (POS[pc] - i) <= back:
        t = NM[PCS[i]]
        if re.match(r"^(mov|lea|add|sub|xor|shl|imul|or|and|inc|dec)\s+" + reg + r",", t):
            return (PCS[i], t)
        i -= 1
    return None


def canon(op, fn, pc, depth=0):
    """canonical expression for an operand: M[base+disp] / IMM0x.. / REG:r / OP(a,b)."""
    op = op.strip()
    m = re.match(r"^(?:d?word ptr )?\[([^]]*)\]$", op)
    if m:
        inner = m.group(1)
        d = re.search(r"([+-])0x([0-9a-f]+)\s*$", inner)
        disp = d.group(0) if d else "+0x0"
        base = (inner[:d.start()] if d else inner).strip()
        if depth < 4 and re.match(r"^\w+$", base):
            dd = definsn(fn, pc, base)
            if dd:
                sub = canon(dd[1].split(",", 1)[1], fn, dd[0], depth + 1)
                mm = re.match(r"^M\[(.*)\]$", sub)
                if mm or sub.startswith("IMM"):
                    return "M[%s%s]" % (mm.group(1) if mm else sub, disp)
        return "M[%s%s]" % (base, disp)
    if re.match(r"^0x[0-9a-f]+$", op):
        return "IMM" + op
    if re.match(r"^\w+$", op):
        if depth >= 4:
            return "REG:" + op
        dd = definsn(fn, pc, op)
        if not dd:
            return "REG:" + op
        dpc, dt = dd
        rest = dt.split(",", 1)[1]
        m2 = re.match(r"^(add|sub|xor|shl|imul|or|and)\s+\w+,(.*)$", dt)
        if m2:
            return m2.group(1).upper() + "(" + canon(op, fn, dpc, depth + 1) + "," + canon(m2.group(2), fn, dpc, depth + 1) + ")"
        return canon(rest, fn, dpc, depth + 1)
    return "?" + op


def sites_of(addr):
    t = "call 0x%x" % addr
    return [(pc, fnof(pc)) for pc, s in NORM if s == t]


def m222():
    ok = RESULTS["M222"] = []
    b = body("FUN_005e774d")
    item = {}
    for pc, s in b:
        m = re.match(r"^mov dword ptr \[([^\]]*)\],(\w+)$", s)
        if not m:
            continue
        dm = re.search(r"\+0x([0-9a-f]+)$", m.group(1))
        disp, src = (int(dm.group(1), 16) if dm else 0), m.group(2)
        dd = definsn("FUN_005e774d", pc, src)
        if not dd:
            continue
        m2 = re.match(r"^mov \w+,dword ptr \[ebp\+(0x[0-9a-f]+)\]$", dd[1])
        m3 = re.match(r"^add \w+,dword ptr \[ebp\+(0x[0-9a-f]+)\]$", dd[1])
        if m2:
            item[disp] = ("arg", int(m2.group(1), 16))
        elif m3:
            pv = definsn("FUN_005e774d", dd[0], src)
            m4 = re.match(r"^mov \w+,dword ptr \[ebp\+(0x[0-9a-f]+)\]$", pv[1]) if pv else None
            if m4:
                item[disp] = ("arg+arg", int(m4.group(1), 16), int(m3.group(1), 16))
    retv = [pc for pc, s in b if s == "ret 0x18"]
    G(ok, "the adder FUN_005e774d (ret 0x18) writes item+0x14=arg1, +0x10=arg2, +0=arg3, +4=arg4, "
          "+8=arg3+arg5, +0xc=arg4+arg6 - read out of its own body",
      [item.get(k) for k in (0x14, 0x10, 0, 4)] == [("arg", 8), ("arg", 0xc), ("arg", 0x10), ("arg", 0x14)]
      and item.get(8) == ("arg+arg", 0x10, 0x18) and item.get(0xc) == ("arg+arg", 0x14, 0x1c) and len(retv) == 1,
      ["map=%s" % sorted((hex(k), str(v)) for k, v in item.items()), "ret=%s" % [hex(p) for p in retv]])
    G(ok, "its only failure path is count>=capacity -> return -1: it never allocates and never grows",
      any(s == "cmp edx,dword ptr [ecx+0x4]" for _, s in b) and any(s == "or eax,0xffffffff" for _, s in b)
      and not any(s == "call 0x5be090" for _, s in b),
      ["full-test and or-eax-0xffffffff present; allocator calls=%d" % len([1 for _, s in b if s == "call 0x5be090"])])
    wb = body("FUN_00403b00")
    spill = [pc for pc, s in wb[:14] if s == "mov dword ptr [ebp-0x4],ecx"]
    cl = [pc for pc, s in wb if s.startswith("call ")]
    r = [s for _, s in wb if s.startswith("ret ")]
    G(ok, "FUN_00403b00 (75 B) spills ecx to [ebp-0x4] in its prologue, calls FUN_005e774d exactly once "
          "and returns 0xc: the CONTAINER is its own `this`, its 3 args are (gate, payload, RECT)",
      len(spill) == 1 and cl == [0x403b3d] and r == ["ret 0xc"],
      ["spill=%s call sites=%s ret=%s size=%d" % ([hex(p) for p in spill], [hex(p) for p in cl], r, IDXMAP["FUN_00403b00"][1])])
    pushed = [canon(o, "FUN_00403b00", q) for o, q in argw_pc(0x403b3d, 6)]
    want = ["M[ebp+0x8]", "M[ebp+0xc]", "M[ebp+0x10+0x0]", "M[ebp+0x10+0x4]",
            "SUB(M[ebp+0x10+0x8],M[ebp+0x10+0x0])", "SUB(M[ebp+0x10+0xc],M[ebp+0x10+0x4])"]
    G(ok, "its 6 pushes resolve to arg1, arg2, [rect+0], [rect+4], [rect+8]-[rect+0], [rect+0xc]-[rect+4]: "
          "the 3rd arg is an {x,y,right,bottom} RECT turned into (x,y,w,h)",
      pushed == want, ["pushed=%s" % pushed])
    h, per = disp_hist(0x403b00)
    disps = collections.Counter(d for _, _, d in per.get("member", []))
    nsites = sum(h.values())
    nfun = len(set(f for _, f in sites_of(0x403b00)))
    G(ok, "all %d sites of the wrapper sit in %d functions: %d pass the container as their own ecx plus "
          "ONE of 8 member displacements, %d forwards ecx bare (FUN_00403ad0)" % (nsites, nfun, h.get("member", 0), h.get("loaded", 0)),
      nsites == 23 and h.get("member") == 22 and h.get("loaded") == 1 and nfun == 16
      and sorted(disps.items()) == sorted([(0xa48, 1), (0xcc4, 5), (0xe40, 1), (0x15e0, 5), (0x28ac, 4),
                                           (0x5994, 3), (0x12758, 2), (0x12764, 1)]),
      ["kinds=%s" % dict(h), "disps=%s" % sorted((hex(k), v) for k, v in disps.items())])
    add3098 = [pc for pc, _ in direct_calls(0x5e774d) if receiver(pc)[1] == 0x3098]
    G(ok, "NO wrapper site and NO direct add-site carries the dialog's container displacement 0x3098: its "
          "10-item list is allocated, reset and scanned but never appended anywhere in the image",
      0x3098 not in disps and add3098 == [],
      ["wrapper disps=%s" % sorted(hex(k) for k in disps), "direct add-sites at +0x3098=%d" % len(add3098)])
    a1i, a2i, a1r, a2r = collections.Counter(), collections.Counter(), 0, 0
    for pc, f in sites_of(0x403b00):
        pp = argw_pc(pc, 3)
        aa = [o for o, _ in pp]
        c = [canon(o, f, q) for o, q in pp]
        if c[0].startswith("IMM"):
            a1i[aa[0]] += 1
        else:
            a1r += 1
        if c[1].startswith("IMM"):
            a2i[aa[1]] += 1
        else:
            a2r += 1
    G(ok, "at those 23 sites the slot written to item+0x14 (the one the click dispatcher tests for 0) is "
          "an immediate %d times and a register/loaded value %d times; the slot written to item+0x10 (the "
          "one it hands to +0xa8) is an immediate %d times with values %s - 0xa/0xb lie OUTSIDE M218's "
          "{0,1..8,0x45} gate set" % (sum(a1i.values()), a1r, sum(a2i.values()), sorted(a2i, key=lambda x: int(x, 16))),
      sum(a1i.values()) == 4 and a1r == 19 and sum(a2i.values()) == 19 and a2r == 4
      and sorted(a2i) == sorted(["0x0", "0x1", "0x2", "0x3", "0x4", "0xa", "0xb"])
      and sorted(a1i) == ["0x0", "0x3", "0x64"],
      ["slot+0x14 imms=%s" % sorted(a1i.items(), key=lambda kv: -kv[1]), "slot+0x10 imms=%s" % sorted(a2i.items(), key=lambda kv: -kv[1])])
    npane = 0
    for tgt in (0x40f830, 0x4105b0, 0x411840, 0x415d10):
        for pc, f in sites_of(tgt):
            if ecx_operand_before(pc) == ("mov", "0x6a9480"):
                npane += 1
    hubc = [(pc, ecx_operand_before(pc)) for pc, f in sites_of(0x41f310)]
    ebx = [s for _, s in win(0x4105b0, 0x41066c) if re.match(r"^(mov|lea|add) ebx,", s)][-1]
    G(ok, "the 4 remaining register-passed adders run on the GLOBAL object at 0x6a9480: FUN_0041f310 is "
          "slot +0x30 of vtable 0x672448 and all %d of its sites pass ecx = 0x6a9480, and %d of the 15 "
          "adder sites pass the same immediate; FUN_004105b0's container is this+0x402f0 (`%s`), a "
          "DIFFERENT member from the dialog's +0x3098" % (len(hubc), npane, ebx),
      slots_of(0x41f310) == [(0x672448, 0x30)] and len(hubc) == 3
      and all(t == ("mov", "0x6a9480") for p, t in hubc) and npane == 8 and ebx == "lea ebx,[edi+0x402f0]",
      ["hub sites=%s" % [(hex(p), str(v)) for p, v in hubc], "pane-immediate add-sites=%d" % npane, "ebx=%s" % ebx])
    report("M222")

def m223():
    ok = RESULTS["M223"] = []
    calls = [(pc, fnof(pc)) for pc, s in NORM if s == "call 0x5f5a11"]
    pat = struct.pack("<I", 0x5f5a11)
    hits, i = [], 0
    while True:
        j = IMG.find(pat, i)
        if j < 0:
            break
        i = j + 1
        hits.append(j + 0x400000)
    stores = [(pc, s) for pc, s in NORM if s.endswith("],0x5f5a11")]
    G(ok, "FUN_005f5a11 has %d direct call sites, sits in NO vtable, and the dword 0x5f5a11 occurs in the "
          "image only as the imm32 of the 3 stores that install it (hit-6 == a store pc)" % len(calls),
      len(calls) == 0 and slots_of(0x5f5a11) == [] and len(stores) == 3
      and sorted(h - 6 for h in hits) == sorted(pc for pc, _ in stores),
      ["direct=%d slots=%s" % (len(calls), slots_of(0x5f5a11)),
       "data hits=%s stores=%s" % ([hex(x) for x in hits], [hex(p) for p, _ in stores])])
    DERE = re.compile(r"\[([^\]]*)\+0x(2210|2224|2234)\]")
    DERE2 = re.compile(r"\+0x(21[c-f][0-9a-f]|22[0-6][0-9a-f])\]")
    refs = [(pc, s) for pc, s in NORM if DERE.search(s)]
    st = [(pc, s) for pc, s in refs if ops(s)[0] in STOREMN and ops(s)[1] and DERE.search(ops(s)[1][0])]
    reads = [(pc, s) for pc, s in refs if (pc, s) not in st]
    letak = [(pc, s) for pc, s in NORM if re.search(r"lea \w+,\[[^]]*\+0x(2210|2224|2234)\]", s)]
    ind = [(pc, s) for pc, s in NORM if s.startswith("call ") and re.search(r"\+0x(21[c-f][0-9a-f]|22[0-5][0-9a-f])\]", s)]
    reps = [(pc, fnof(pc)) for pc, s in NORM if "rep movs" in s and fnof(pc) in IDXMAP and any(DERE2.search(x) for _, x in body(fnof(pc)))]
    G(ok, "the 3 installed fields are READ by nothing: %d dereferences that are not stores, %d "
          "lea-address-takes, %d indirect calls with a displacement in 0x21c0..0x2260, %d rep movs in a "
          "function touching the window (all %d bracket refs are stores)"
          % (len(reads), len(letak), len(ind), len(reps), len(refs)),
      reads == [] and letak == [] and ind == [] and len(st) == 4,
      ["refs=%s" % [(hex(p), s) for p, s in refs], "reads=%s lea=%s ind=%s reps=%s" % (reads, letak[:2], ind[:2], reps[:2])])
    G(ok, "the writers are 2 functions and the readers 0: FUN_005f3f5b installs the callback 3x and "
          "FUN_00406990 zeroes one field in a loop",
      len(st) == 4 and sorted(set(fnof(p) for p, _ in st)) == ["FUN_00406990", "FUN_005f3f5b"]
      and len([pc for pc, s in st if fnof(pc) == "FUN_005f3f5b"]) == 3,
      ["stores=%s" % [(hex(p), fnof(p)) for p, _ in st]])
    b = body("FUN_005f5a11")
    rd = sorted(set(int(m.group(1), 16) for _, s in b for m in [re.search(r"^mov \w+,dword ptr \[[^\]]*\+0x([0-9a-f]+)\]$", s)] if m))
    dsp = sorted(set(int(m.group(1), 16) for _, s in b for m in [re.search(r"^call dword ptr \[[^\]]*\+0x([0-9a-f]+)\]$", s)] if m))
    G(ok, "its body proves it is a method of the MODAL object: it reads ds:0x9977f0 (the handle the pump "
          "publishes), gates [h+0x2350] against 1 and -1, reads 0x21d0/0x30a8 and dispatches slots +0x8 "
          "and +0xe0",
      any(s == "mov eax,ds:0x9977f0" for _, s in b) and all(x in rd for x in (0x2350, 0x21d0, 0x30a8)) and dsp == [0x8, 0xe0],
      ["read disps=%s" % [hex(x) for x in rd], "dispatched=%s" % [hex(x) for x in dsp],
       "size=%d insns=%d" % (IDXMAP["FUN_005f5a11"][1], len(b))])
    site = [pc for pc, s in body("FUN_005f1394") if s == "call 0x60c436"]
    G(ok, "the window IS live through its other members: the dialog runner FUN_005f1394 calls "
          "FUN_0060c436 with ecx = obj+0x21d0 and pushes [obj+0x2350] as an argument",
      len(site) == 1 and ecx_operand_before(site[0]) == ("add", 0x21d0) and any("0x2350" in canon(o, fnof(site[0]), q) for o, q in argw_pc(site[0], 3)),
      ["site=%s ecx=%s args=%s" % ([hex(p) for p in site], str(ecx_operand_before(site[0])),
                                    [canon(o, fnof(site[0]), q) for o, q in argw_pc(site[0], 3)])])
    sub = [pc for pc, s in body("FUN_00607eca") if s == "call 0x5e774d"]
    G(ok, "and it is live as a CONTAINER: FUN_0060c436 hands its own this+0xb14 to FUN_00607eca, which "
          "subtracts 0xa94 before the adder, so the list is this+0x80 = obj+0x2250 - 0x1c above the last "
          "write-only field, in the same block",
      0xb14 - 0xa94 == 0x80 and 0x21d0 + 0x80 == 0x2250 and len(sub) == 1
      and ecx_operand_before(sub[0]) == ("mov", "dword ptr [ebp-0x70]") and any(s == "sub ecx,0xa94" for _, s in body("FUN_00607eca")),
      ["adder site=%s ecx=%s" % ([hex(p) for p in sub], str(ecx_operand_before(sub[0]))),
       "0xb14-0xa94=0x%x  0x21d0+0x80=0x%x  fields 0x2210/0x2224/0x2234" % (0xb14 - 0xa94, 0x21d0 + 0x80)])
    report("M223")


def m224():
    ok = RESULTS["M224"] = []
    cs = sites_of(0x459bb0)
    up = [(pc, fnof(pc)) for pc, s in NORM if s == "call 0x45a740"]
    G(ok, "FUN_00459bb0 (%d B) has exactly ONE call site (0x45a755, inside FUN_0045a740, itself %d B with "
          "%d caller) and sits in no vtable" % (IDXMAP["FUN_00459bb0"][1], IDXMAP["FUN_0045a740"][1], len(set(f for _, f in up))),
      len(cs) == 1 and cs[0] == (0x45a755, "FUN_0045a740") and IDXMAP["FUN_0045a740"][1] == 56
      and slots_of(0x459bb0) == [] and slots_of(0x45a740) == [],
      ["sites=%s callers of 45a740=%s" % ([hex(p) for p, _ in cs], sorted(set(f for _, f in up)))])
    toks = ["0x%x" % (0x9978ac + 4 * j) for j in range(27)]
    wr = collections.Counter()
    for pc, s in NORM:
        if any(t in s for t in toks):
            wr[fnof(pc)] += 1
    setters = sorted(w for w, n in wr.items() if w in IDXMAP and IDXMAP[w][1] == 42 and n == 3)
    per1 = all(len(sites_of(IDXMAP[w][0])) == 1 and sites_of(IDXMAP[w][0])[0][1] == "FUN_00459bb0" for w in setters)
    G(ok, "the 27 globals 0x9978ac..0x997914 are written by exactly %d functions of 42 B (3 refs each), "
          "each called once and only from FUN_00459bb0 - M219's setter set re-derived from the stores" % len(setters),
      len(setters) == 9 and per1,
      ["setters=%s" % setters, "other writers=%s" % sorted(set(wr) - set(setters))])
    grid = [0x774c38 + 0x2c * i for i in range(9)]
    gs = lambda a: isinstance(a, str) and a.startswith("0x") and int(a, 16) in grid
    args = {w: argw(sites_of(IDXMAP[w][0])[0][0], 3) for w in setters}
    withg = [w for w in setters if any(gs(a) for a in args[w])]
    zeros = [w for w in setters if args[w] == ["0x0", "0x0", "0x0"]]
    G(ok, "M219's split CONFIRMED: %d of the 9 setter calls pass three grid pointers each, %d pass (0,0,0)" % (len(withg), len(zeros)),
      len(withg) == 3 and len(zeros) == 6,
      ["pointer calls=%s" % {w: args[w] for w in withg}, "zero calls=%d" % len(zeros)])
    allp = [a for pc, s in body("FUN_00459bb0") if s.startswith("call ") for a in argw(pc, 3) if gs(a)]
    G(ok, "the pointers are the 0x2c-stride grid 0x774c38+0x2c*i (i=0..8): %d pushes drawn from exactly "
          "%d addresses, each used %s times" % (len(allp), len(set(allp)), sorted(collections.Counter(allp).values())),
      sorted(set(int(x, 16) for x in allp)) == sorted(grid) and len(allp) == 24,
      ["grid=%s" % sorted(set(allp)), "per-entry counts=%s" % sorted(collections.Counter(allp).values())])
    zero = [dw(v) for v in range(0x774c38, 0x774dc4, 4)]
    past = 0x774c38 - 0x400000 >= len(IMG)
    G(ok, "the grid is all-zero across the window 0x774c38..0x774dc4 (%d dwords, %d nonzero; the file "
          "image ends at 0x%x so the block is %s): runtime state, not load-time data"
          % (len(zero), sum(1 for v in zero if v), 0x400000 + len(IMG), "past the last mapped byte (BSS)" if past else "mapped and zero"),
      all(v == 0 for v in zero),
      ["dwords=%d nonzero=%d file_end=0x%x past_eof=%s" % (len(zero), sum(1 for v in zero if v), 0x400000 + len(IMG), past)])
    f450 = body("FUN_0041f450")
    ins = [(hex(pc), s) for pc, s in f450 if re.match(r"^mov dword ptr \[\w+\+0xb24\],", s)]
    nref = len([1 for _, s in f450 if re.search(r"0x774[a-f][0-9a-f]{2}", s)])
    b24 = [(pc, s, fnof(pc)) for pc, s in NORM if re.search(r"\+0xb24\]", s)]
    lds = [(pc, s, f) for pc, s, f in b24 if not (ops(s)[0] in STOREMN and ops(s)[1] and "+0xb24]" in ops(s)[1][0])]
    rders = sorted(set(f for _, _, f in lds if f != "FUN_0041f450"))
    G(ok, "its only other window reference FUN_0041f450 (%d B, 1 caller) touches the 0x774xxx region %d "
          "times and INSTALLS the page bases: its %d stores all go to [obj+0xb24] - 0x774c0c x4 (one "
          "entry below the grid base) and 0x774a80 x1 (nine entries below) - and %d other functions "
          "load [obj+0xb24], so the grid is reached through that field"
          % (IDXMAP["FUN_0041f450"][1], nref, len(ins), len(rders)),
      len(ins) == 5 and collections.Counter(s.split(",")[-1] for _, s in ins) == collections.Counter({"0x774c0c": 4, "0x774a80": 1})
      and 0x774c38 - 0x774c0c == 0x2c and 0x774c0c - 0x774a80 == 9 * 0x2c and len(rders) >= 3,
      ["installs=%s" % ins, "region refs=%d" % nref, "loaders of +0xb24=%s" % rders])
    report("M224")


def m225():
    ok = RESULTS["M225"] = []
    b = body("FUN_005f90d7")
    cnt = collections.Counter(int(m.group(1), 16) for _, s in b for m in [re.search(r"^call dword ptr \[[^\]]*\+0x([0-9a-f]+)\]$", s)] if m)
    maxslot = max(4 * (v[0] - 1) for v in VT.values())
    G(ok, "the panel's slot +0xa8 dispatches %d times: +0xb8 x%d, +0x2144 x%d, +0x5c, +0x1c, +0xf0 - and "
          "+0x2144 is larger than EVERY vtable slot in the image (max 0x%x over %d vtables), so it is a "
          "call through the panel's own last field, not a vmethod" % (sum(cnt.values()), cnt.get(0xb8, 0), cnt.get(0x2144, 0), maxslot, len(VT)),
      sum(cnt.values()) == 7 and dict(cnt) == {0xb8: 2, 0x2144: 2, 0x5c: 1, 0x1c: 1, 0xf0: 1} and 0x2144 > maxslot,
      ["dispatches=%s" % sorted((hex(k), v) for k, v in cnt.items()), "max vtable slot=0x%x over %d vtables" % (maxslot, len(VT))])
    sl = slots_of(0x5f90d7)
    link = [s for _, s in b if re.search(r"0xa(18|20|24|2c|38|3c)", s)]
    G(ok, "it is slot +0xa8 of exactly 1 vtable (the panel 0x671d94) and its 2 +0xb8 calls are made on the "
          "link neighbours it unlinks: %d references to the 0xa18/0xa20/0xa24/0xa2c/0xa38/0xa3c block, "
          "including 2 stores of the relink `mov [eax+0xa2c],edx`" % len(link),
      sl == [(0x671d94, 0xa8)] and len([s for s in link if s == "mov dword ptr [eax+0xa2c],edx"]) == 2
      and any(s == "mov dword ptr [eax+0xa38],0x0" for _, s in b) and any(s == "mov dword ptr [eax+0xa3c],0xffffffff" for _, s in b),
      ["slots=%s" % [(hex(a), hex(o)) for a, o in sl], "link refs=%d" % len(link)])
    f = [(pc, s, fnof(pc)) for pc, s in NORM if re.search(r"\+0x2144\]", s)]
    wr = sorted(set(fnof(pc) for pc, s, _ in f if ops(s)[0] in STOREMN and ops(s)[1] and "0x2144" in ops(s)[1][0]))
    rd = sorted(set(fnof(pc) for pc, _, _ in f if fnof(pc) not in wr))
    G(ok, "that field has %d writers (%s) and %d reader/caller functions over %d sites - a stored callback "
          "in the object's last dword, not a vtable slot" % (len(wr), wr, len(rd), len(f)),
      len(wr) == 17 and len(rd) >= 5 and len(f) == 54,
      ["sites=%d writers=%s readers=%s" % (len(f), wr, rd[:10])])
    report("M225")


def m226():
    ok = RESULTS["M226"] = []
    fn = "FUN_005fb1a5"
    b = body(fn)
    sl = slots_of(0x5fb1a5)
    cp = len([1 for _, s in b if s == "add ecx,0x444"])
    calls = collections.Counter(m.group(1) for _, s in b for m in [re.match(r"^call (0x[0-9a-f]+)$", s)] if m)
    ind = [(hex(pc), s) for pc, s in b if s.startswith("call dword ptr ")]
    G(ok, "the row class's slot +0x30 FUN_005fb1a5 (%d B, %d insns) is a DRAW: %d of its calls switch ecx "
          "to the CPane subobject (`add ecx,0x444`) and it makes exactly ONE indirect call, [reg+0x14]"
          % (IDXMAP[fn][1], len(b), cp),
      sl == [(0x67194c, 0x30)] and cp >= 10 and len(ind) == 1 and ind[0][1] == "call dword ptr [edx+0x14]",
      ["slots=%s" % [(hex(a), hex(o)) for a, o in sl], "add ecx,0x444 sites=%d" % cp, "indirect=%s" % ind])
    idx = [(hex(pc), s) for pc, s in b if re.search(r"\*4\+0x(abc|ac8)\]$", s)]
    flds = collections.Counter(int(m.group(1), 16) for _, s in b for m in [re.search(r"\+0x([0-9a-f]{2,4})\]$", s)] if m)
    G(ok, "it reads the group fields as an INDEXED dword array (%d sites of the form `[reg+reg*4+0xabc]` / "
          "`+0xac8`) and also loads 0x98/0xa7c/0xa88/0xa8c: the 9 groups are arrays inside the row, not 9 "
          "separate members" % len(idx),
      len(idx) >= 2 and all(x in flds for x in (0x98, 0xa7c, 0xa88, 0xa8c)),
      ["indexed sites=%d" % len(idx), "field reads=%s" % sorted((hex(k), v) for k, v in flds.items() if k >= 0x90)])
    em = {k: v for k, v in calls.items() if k in ("0x5dd09c", "0x5c153f", "0x5ca7c3")}
    G(ok, "its callees are the text/label emitters FUN_005dd09c x%d, FUN_005c153f x%d, FUN_005ca7c3 x%d"
          % (em.get("0x5dd09c", 0), em.get("0x5c153f", 0), em.get("0x5ca7c3", 0)),
      em.get("0x5dd09c") == 5 and em.get("0x5c153f") == 5 and em.get("0x5ca7c3") == 4,
      ["emitters=%s" % sorted(em.items(), key=lambda kv: -kv[1]), "distinct direct callees=%d" % len(calls)])
    report("M226")


for tag, fn in (("M222", m222), ("M223", m223), ("M224", m224), ("M225", m225), ("M226", m226)):
    fn()
print()
res = []
for tag in ("M222", "M223", "M224", "M225", "M226"):
    v = RESULTS[tag]
    res.append("%s=%s" % (tag, "PASS" if all(c for _, c, _ in v) else "FAIL"))
tot = sum(len(RESULTS[t]) for t in RESULTS)
got = sum(sum(1 for _, c, _ in RESULTS[t] if c) for t in RESULTS)
print("SUMMARY %s (%d/%d gates)" % (" ".join(res), got, tot))
sys.exit(0 if got == tot else 1)
