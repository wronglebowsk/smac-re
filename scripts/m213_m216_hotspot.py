#!/usr/bin/env python3
"""M213-M216: the point-in-rect hotspot layer, who owns a hotspot list and who dispatches
+0x4c, the 0xb4c row object and where its label text comes from, the 0x6738e4 class and
the two readers of the modal handle.

  M213  FUN_005e75a0 is a PURE POINT-IN-RECT test (16-byte {l,t,r,b}, half-open, 4 cmp / 4
        zero-arms / 1 hit-arm / 0 stores) and FUN_005e7917 is a REVERSE scan over a 24-byte
        item list ([obj+0] array base, [obj+8] count) that returns the HIGHEST matching index
        and publishes item[+0x14]/item[+0x10]; FUN_00478080 runs the test 4x on one stack rect
        built by FUN_00403a40 (pos+size) / FUN_00403a80 (inflate both corners) and dispatches
        +0xa8 with the ZONE NUMBER 0..3.
  M214  FUN_005f6aa3 (the dialog family's +0x4c, 5 vtables / 466 installs / 0 direct calls) is
        a CLICK DISPATCHER: it hit-tests the point against the hotspot list EMBEDDED AT
        this+0x3098 and dispatches its own class's +0xa8 with item[+0x10], gated on
        item[+0x14] == 0.  The list is a reusable member: the 44 scan sites take it from 19
        distinct this-relative displacements + 1 global + 9 stack locals.  Of the 12
        `call [reg+0x4c]` sites image-wide, 0 dispatch a family class.
  M215  the 0xb4c-byte ROW object (vtable 0x67194c, embedded in the 0x671d94 class at +0xaac
        and +0x15f8): ctor FUN_005faec0 writes 21 dwords, 27 of them copied from 9 read-only
        BSS triples at 0x9978ac..0x99790c; FUN_005f9e85 is NOT a vmethod (0 slots) - it is the
        labelled-control creator (id -> [this+0xa78], label copy -> [this+0xa7c]) and its 90
        sites' label argument is 15 NULL / 44 the shared BSS scratch buffer 0x997120 / 1 a
        .rdata literal / 30 a register or field.
  M216  vtable 0x6738e4 (87 slots, 2 installs) is a dialog-family class (75/87 slots identical
        to 0x6717cc) whose +0xa8 is the handle forwarder FUN_0043fee0 (0 direct calls); ds:0x9977f0
        has 9 refs, 2 stores (both inside the pump FUN_005f1394) and its 7 loads sit in exactly 4
        functions - the pump, the forwarder, FUN_005d69fa (picks the CURRENT object from 4 globals,
        publishes it to ds:0x9939ac, returns its [+0xa8] DELEGATE pointer, 3 callers
        that dispatch +0x12c/+0x130/+0x134 on it) and FUN_005f5a11 (no vtable slot at all - it
        is installed as a CALLBACK FIELD at [reg+0x2210/0x2224/0x2234] and dispatches +0xe0 on
        [handle+0xa14] or the handle, writing [handle+0xa40]).

    python3 scripts/m213_m216_hotspot.py            # the acceptance run (17 gates)
    python3 scripts/m213_m216_hotspot.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + programs/terran.exe bytes
(file offset = VA - 0x400000) + ghidra_out/ (index.csv, decompiled shards).  No box time.
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
FILEMAP_END = 0x400000 + len(IMG)          # above this the VA is BSS: no bytes in the image


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
    """byte displacement of a memory operand, or None when the operand is not memory."""
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
    """a memory operand: bracketed, `d?word ptr ds:0x...`, or the BARE absolute form
    `mov ds:0x9977f0,eax` - a store census that demands brackets or even the `ptr` keyword
    misses stores and reports zero writers (the 2nd of the 2 stores to ds:0x9977f0 is bare)."""
    if "[" in op:
        return True
    if re.search(r"\b(byte|word|dword|ptr)\s*(fs|gs|ds|es|ss)?:", op):
        return True
    return bool(re.match(r"^(?:[a-z]{2}:)?0x[0-9a-f]{5,8}$", op))


def stores_of(b):
    """[(pc, s, dest_operand)] for every store instruction (mnemonic writes its first operand)."""
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
    """pushes in front of a call site, CHRONOLOGICAL (argN first ... arg1 LAST); starts one
    instruction before the site (law: walking back from the site itself hits the call first)."""
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
    """how ecx (the this / list pointer) was set in front of a call."""
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


# ---------------------------------------------------------------- M213
def m213():
    ok = []
    b = body("FUN_005e75a0")
    cmps = []
    for pc, s in b:
        if s.startswith("cmp "):
            ps = ops(s)[1]
            cmps.append((pc, s, mem_disp(ps[-1] if ps else "")))
    disps = sorted({d for _, _, d in cmps})
    zeroarms = sum(1 for pc, s in b if s == "xor eax,eax")
    hitarm = sum(1 for pc, s in b if s == "mov eax,0x1")
    memstores = [x for x in stores_of(b) if "ebp" not in x[2]]
    last = b[-1][1]
    G(ok, "FUN_005e75a0 (%d B, %d insns, 0 callees) is a PURE POINT-IN-RECT test: %d cmp sites reading "
          "the 4 dword fields of its 3rd operand at displacements %s, %d `xor eax,eax` miss-arms, "
          "exactly %d `mov eax,1` hit-arm, %d stores to memory, ends `%s` (cdecl, 3 args) - it returns "
          "1 iff rect[0] <= x < rect[2] and rect[1] <= y < rect[3]: a 16-byte {l,t,r,b} box, HALF-OPEN"
      % (IDXMAP["FUN_005e75a0"][1], len(b), len(cmps), [hex(d) for d in disps], zeroarms, hitarm,
         len(memstores), last),
      len(b) == 29 and len(cmps) == 4 and disps == [0, 4, 8, 12] and zeroarms == 4 and hitarm == 1
      and len(memstores) == 0 and last == "ret",
      "insns=%d cmp=%d disp=%s xor0=%d one=%d stores=%d last=%s" % (len(b), len(cmps), disps, zeroarms,
                                                                    hitarm, len(memstores), last))

    b = body("FUN_005e7917")
    imul18 = sum(1 for pc, s in b if re.match(r"^imul\s+\w+,\w+,0x18$", s))
    countload = sum(1 for pc, s in b if s == "mov ecx,dword ptr [eax+0x8]")
    baseloads = sum(1 for pc, s in b if re.match(r"^mov \w+,dword ptr \[(e[a-z]{2}|esi|edi)\]$", s))
    puboff = sorted(mem_disp(ops(s)[1][1]) for pc, s in b
                    if re.match(r"^mov \w+,dword ptr \[\w+\+\w+\*1\+0x1[04]\]$", s))
    outstores = sum(1 for pc, s in b if s == "mov dword ptr [eax],ecx")
    guards = sum(1 for pc, s in b if s in ("cmp dword ptr [ebp+0x10],0x0", "cmp dword ptr [ebp+0x14],0x0"))
    neg1 = sum(1 for pc, s in b if s == "or eax,0xffffffff")
    retw = sum(1 for pc, s in b if s == "ret 0x10")
    subs = sum(1 for pc, s in b if re.match(r"^sub \w+,0x1$", s))
    G(ok, "FUN_005e7917 (%d insns) is the SCAN: %d load of `[obj+8]` = the item COUNT, %d `sub ,1` "
          "(starts at count-1 and walks DOWN to 0), %d `imul ,0x18` = 24-BYTE items, %d bare-register "
          "loads of `[obj+0]` = the item ARRAY BASE, publishes offsets %s into the two out-params (%d "
          "guarded stores, %d null-guards), `%s` is the no-match arm, ends `ret 0x10` (4 stack args) - "
          "it returns the HIGHEST index whose box contains the point: LAST-DRAWN WINS"
      % (len(b), countload, subs, imul18, baseloads, [hex(x) for x in puboff], outstores, guards,
         "or eax,0xffffffff" if neg1 else "?"),
      len(b) == 53 and countload == 1 and subs == 2 and imul18 == 3 and baseloads == 3
      and puboff == [0x10, 0x14] and outstores == 2 and guards == 2 and neg1 == 1 and retw == 1,
      "insns=%d count=%d sub1=%d imul18=%d baseload=%d pub=%s stores=%d guards=%d neg1=%d ret=%d"
      % (len(b), countload, subs, imul18, baseloads, [hex(x) for x in puboff], outstores, guards, neg1, retw))

    s5a0 = direct_calls(0x5e75a0)
    s7917 = direct_calls(0x5e7917)
    G(ok, "the primitive's reach: `call 0x5e75a0` has %d sites in %d functions, `call 0x5e7917` has %d "
          "sites in %d functions - the test is called directly (on stack rects, on static rect tables "
          "like 0x7a7538/0x7a9784/0x7a9794/0x7a97a4, on object fields) far more often than through the "
          "list scan" % (len(s5a0), len(set(f for _, f in s5a0)), len(s7917), len(set(f for _, f in s7917))),
      len(s5a0) == 61 and len(s7917) == 44 and len(set(f for _, f in s7917)) == 43,
      "5a0=%d/%d 7917=%d/%d" % (len(s5a0), len(set(f for _, f in s5a0)), len(s7917), len(set(f for _, f in s7917))))

    b = body("FUN_00478080")
    n5a0 = sum(1 for pc, s in b if s == "call 0x5e75a0")
    disp4c = [(pc, s) for pc, s in b if s.startswith("call ") and "+0xa8]" in s]
    zone = []
    for pc, s in disp4c:
        ps = arg_pushes(pc)
        zone.append(ps[-1] if ps else "?")
    nbuild = (sum(1 for pc, s in b if s == "call 0x403a40"), sum(1 for pc, s in b if s == "call 0x403a80"))
    s40 = stores_of(body("FUN_00403a40"))
    d40 = sorted({mem_disp(d) for _, _, d in s40 if mem_disp(d) is not None})
    b80 = body("FUN_00403a80")
    s80 = stores_of(b80)
    d80 = sorted({mem_disp(d) for _, _, d in s80 if mem_disp(d) is not None})
    rmw80 = sum(1 for pc, s in b80 if s.startswith("add "))
    G(ok, "FUN_00478080 (%d insns, %d direct call sites image-wide) is the 4-ZONE version: %d "
          "rect-builder calls (FUN_00403a40 pos+size -> offsets %s in %d stores; FUN_00403a80 "
          "inflate-both-corners -> offsets %s in %d stores, %d of them `add` read-modify-writes), %d "
          "test calls on ONE 16-byte stack rect, and %d dispatches of `[reg+0xa8]` whose pushed "
          "argument is %s - the callee gets the ZONE NUMBER, not a key"
      % (len(b), len(direct_calls(0x478080)), nbuild[0] + nbuild[1], [hex(x) for x in d40], len(s40),
         [hex(x) for x in d80], len(s80), rmw80, n5a0, len(disp4c), sorted(zone)),
      n5a0 == 4 and len(disp4c) == 4 and sorted(zone) == ["0x0", "0x1", "0x2", "0x3"]
      and nbuild == (1, 4) and d40 == [0, 4, 8, 12] and len(s40) == 4 and d80 == [0, 4, 8, 12]
      and len(s80) == 4,
      "build=%s test=%d disp=%d zone=%s 403a40=%d/%s 403a80=%d/%s rmw=%d callers=%d"
      % (nbuild, n5a0, len(disp4c), zone, len(s40), d40, len(s80), d80, rmw80, len(direct_calls(0x478080))))
    return ok


# ---------------------------------------------------------------- M214
def m214():
    ok = []
    w4c = sorted(b for b in B if 0x4c < 4 * VT[b][0] and dw(b + 0x4c) == 0x5f6aa3)
    inst = sum(VT[b][1] for b in w4c)
    dc = direct_calls(0x5f6aa3)
    G(ok, "FUN_005f6aa3 is +0x4c of exactly %d vtables %s (%d installs total) and has %d direct call "
          "sites - it is reached ONLY by dispatch" % (len(w4c), [hex(x) for x in w4c], inst, len(dc)),
      [hex(x) for x in w4c] == ["0x67164c", "0x6717cc", "0x6728c0", "0x675cc4", "0x6776c8"]
      and inst == 466 and len(dc) == 0,
      "vtables=%s installs=%d direct=%d" % ([hex(x) for x in w4c], inst, len(dc)))

    b = body("FUN_005f6aa3")
    seq = [s for pc, s in b]
    i_call = next(i for i, s in enumerate(seq) if s == "call 0x5e7917")
    pre = seq[i_call - 1]
    gate = sum(1 for pc, s in b if s == "cmp dword ptr [ebp-0x4],0x0")
    carg = sum(1 for pc, s in b if s == "mov ecx,dword ptr [ebp-0x8]")
    vtload = sum(1 for pc, s in b if s == "mov eax,dword ptr [edx]")
    disp = sum(1 for pc, s in b if s == "call dword ptr [eax+0xa8]")
    retw = sum(1 for pc, s in b if s == "ret 0x8")
    spill = sum(1 for pc, s in b if s == "mov dword ptr [ebp-0xc],ecx")
    G(ok, "the +0x4c vmethod IS a click dispatcher: the insn before `call 0x5e7917` is `%s` - the "
          "hotspot list is a member EMBEDDED AT this+0x3098, not the object itself (which is what the "
          "C rendering suggests) - plus %d spill of this to a frame slot, the gate `cmp [ebp-0x4],0` on "
          "the value published from item[+0x14], the dispatched argument reloaded from the frame slot "
          "that holds item[+0x10] (%d loads), the vtable loaded bare (%d), `%s` self-dispatch and "
          "`ret 0x8` = 2 stack args (x,y)" % (pre, spill, carg, vtload, "call [eax+0xa8]"),
      pre == "add ecx,0x3098" and gate == 1 and carg == 1 and vtload == 1 and disp == 1
      and retw == 1 and spill == 1,
      "pre=%s spill=%d gate=%d arg=%d vt=%d disp=%d ret=%d" % (pre, spill, gate, carg, vtload, disp, retw))

    disp_map = collections.Counter()
    kind = collections.Counter()
    for pc, s in NORM:
        if s != "call 0x5e7917":
            continue
        k, v = ecx_operand_before(pc)
        if k == "add":
            disp_map["+0x%x" % v] += 1
            kind["this-relative"] += 1
        elif k == "lea":
            m = re.search(r"([+-])0x([0-9a-f]{3,})$", v)
            if m:
                disp_map[("%s0x%s" % (m.group(1), m.group(2)))] += 1
                kind["this-relative"] += 1
            else:
                kind["lea-bare"] += 1
        elif k == "mov" and re.match(r"^0x[0-9a-f]{6}$", v):
            disp_map["GLOBAL " + v] += 1
            kind["global-object"] += 1
        elif k == "mov" and "ebp" in v:
            kind["stack-local"] += 1
        else:
            kind["unresolved-" + str(k)] += 1
    site3098 = disp_map.get("+0x3098", 0)
    G(ok, "the list is a REUSABLE MEMBER, not a dialog structure: the %d `call 0x5e7917` sites take the "
          "list object from %d distinct this-relative displacements (%d sites) plus %d global-object "
          "site (0x8a9108) and %d stack-local sites; the dialog family's list is at +0x3098 (%d site - "
          "FUN_005f6aa3 itself), and `[reg+0x3098]`/`+0x309c`/`+0x30a0` have 1/0/0 direct sites "
          "image-wide: the header is never touched outside the accessor"
      % (sum(kind.values()), len([d for d in disp_map if not d.startswith("GLOBAL")]),
         kind["this-relative"], kind["global-object"], kind["stack-local"], site3098),
      sum(kind.values()) == 44 and len(disp_map) == 20 and kind["this-relative"] == 34
      and kind["global-object"] == 1 and kind["stack-local"] == 9 and site3098 == 1,
      "kinds=%s displacements=%d %s" % (dict(kind), len(disp_map), dict(disp_map)))

    sites = [(pc, s) for pc, s in NORM if s.startswith("call ") and "+0x4c]" in s]
    tags = collections.Counter()
    detail = []
    for pc, s in sites:
        f = fnof(pc)
        sl = slots_of(int(f[4:], 16)) if f.startswith("FUN_") else []
        if any(b in w4c and off == 0x4c for b, off in sl):
            t = "SELF-of-family"
        elif any(b in w4c for b, off in sl):
            t = "family-other-slot"
        elif any(off == 0x4c for b, off in sl):
            t = "other-class-+0x4c"
        elif sl:
            t = "other-vmethod"
        else:
            t = "not-a-vmethod"
        tags[t] += 1
        detail.append((hex(pc), f, t, sorted("0x%x+0x%x" % (b, o) for b, o in sl)[:3]))
    G(ok, "WHO DISPATCHES +0x4c: %d `call [reg+0x4c]` sites image-wide; %d sit in a function that is "
          "itself the +0x4c vmethod of one of the 5 family vtables, %d in functions that are +0x4c "
          "vmethods of OTHER classes, %d in other vmethods, %d in functions that are no vmethod at all "
          "- the family's 466-install +0x4c has NO statically nameable dispatcher, and 2 sites "
          "(0x5b7cec/0x5b7dc4) are not even inside an indexed function"
      % (len(sites), tags["SELF-of-family"], tags["other-class-+0x4c"], tags["other-vmethod"],
         tags["not-a-vmethod"]),
      len(sites) == 12 and tags["SELF-of-family"] == 0 and tags["other-class-+0x4c"] == 3
      and tags["other-vmethod"] == 2 and tags["not-a-vmethod"] == 7,
      "tags=%s detail=%s" % (dict(tags), detail))
    return ok


# ---------------------------------------------------------------- M215
def m215():
    ok = []
    seq = [s for pc, s in body("FUN_005f6b8c")]
    subs = [seq[i - 1] for i, s in enumerate(seq) if s == "call 0x5faec0"]
    delta = 0x15f8 - 0xaac
    ctor = body("FUN_005faec0")
    st = stores_of(ctor)
    maxd = max(mem_disp(d) for _, _, d in st if "ebp" not in d)
    scaled = sorted({mem_disp(d) for _, _, d in st if "*4" in d and "ebp" not in d})
    hi = max(scaled) + 8                        # the 0..2 loop index reaches disp+8
    bound = sorted({s for pc, s in ctor if s.startswith("cmp ")})
    installs = [s for pc, s in ctor if re.match(r"^mov dword ptr \[[^\]]*\],0x6719", s)]
    G(ok, "the row size 0xb4c is VERIFIED two ways: FUN_005f6b8c's ctor calls the row ctor FUN_005faec0 "
          "%d times with the ecx arithmetic %s (0x15f8-0xaac = 0x%x), and the row ctor's own highest "
          "field store is the scaled `[X+idx*4+0x%x]`, written for idx 0..2 (%s), whose last element is "
          "dword 0x%x: a row ends at 0x%x - exactly where the next row begins"
      % (len(subs), subs, delta, max(scaled), bound, hi, delta),
      len(subs) == 2 and subs == ["add ecx,0xaac", "add ecx,0x15f8"] and delta == 0xb4c
      and max(scaled) == 0xb40 and hi + 4 == delta,
      "subctors=%s delta=%s maxstore=%s scaled=%s hi=%s bound=%s installs=%s"
      % (subs, hex(delta), hex(maxd), [hex(x) for x in scaled], hex(hi), bound, installs))

    gset = [0x9978ac + 0xc * i for i in range(9)]
    cref = {hex(g): len(census("0x%x" % g)[0]) for g in gset}
    cst = {hex(g): census("0x%x" % g)[1] for g in gset}
    stn = {k: len(v) for k, v in cst.items()}
    wsite = sorted(pc for v in cst.values() for pc, _ in v)
    wstride = sorted({wsite[i + 1] - wsite[i] for i in range(len(wsite) - 1)})
    wfns = sorted({name_of(pc) for pc in wsite})
    block = sorted({mem_disp(d) for _, _, d in st if mem_disp(d) is not None and "ebp" not in d
                    and 0xaac <= mem_disp(d) <= 0xb48})
    G(ok, "the row ctor installs %d vtables (%s: main 0x67194c + the CPane subobject 0x671944 at "
          "[ecx+0x444]) and writes %d dwords, copying a 27-dword block from 9 stride-0xc triples at "
          "0x9978ac..0x99790c into [ecx+0xae0+12j+4i]. Those 9 globals have %d refs each (the copy loop) "
          "and exactly %d store each: all %d writers are the bare no-`ptr`-keyword form `mov "
          "ds:0x9978xx,eax` at %s - one store per triple, %s bytes apart, in %d DISTINCT one-store "
          "setter functions %s. So the block is RUNTIME SETTER STATE (not load-time data, not per-row "
          "state): each triple has exactly one writer and the row ctor copies into the row whatever that "
          "setter last computed. The row's own field displacements in 0xaac..0xb48 are %d distinct (%s)"
      % (len(installs), installs, len(st), min(cref.values()), max(stn.values()), len(wsite),
         [hex(x) for x in wsite], [hex(x) for x in wstride], len(wfns), wfns, len(block),
         [hex(x) for x in block]),
      len(installs) == 2 and all(v == 1 for v in stn.values()) and sum(cref.values()) == 27
      and len(wsite) == 9 and wstride == [0x30] and len(block) == 13,
      "installs=%s stores=%d refs=%s stores_of_globals=%s writers=%s %s block=%s"
      % (installs, len(st), cref, stn, wfns, [(hex(p), s) for v in cst.values() for p, s in v],
         [hex(x) for x in block]))

    sl = slots_of(0x5f9e85)
    sites = direct_calls(0x5f9e85)
    b = body("FUN_005f9e85")
    fieldst = sorted({mem_disp(d) for _, _, d in stores_of(b)
                      if "ebp" not in d and mem_disp(d)})
    nul = sum(1 for pc, s in b if s == "mov byte ptr [edx],0x0")
    callees = sorted({s[5:] for pc, s in b if s.startswith("call ")})
    cn = sorted({(name_of(int(c, 16)) if re.fullmatch(r"0x[0-9a-f]{6,8}", c) else "indirect " + c)
                 for c in callees})
    G(ok, "FUN_005f9e85 sits in %d vtable slots and is called from %d sites in %d functions; its body's "
          "only NON-FRAME stores are [this+0xa78] (the id), [this+0xa7c] (the allocated label-buffer "
          "pointer) and the `%s` NUL terminator it writes into the fresh allocation; it makes %d distinct "
          "call targets (%d of them indirect vmethod calls), which name as %s - the LABELLED-CONTROL "
          "CREATOR (x,y,w,h = param_3..param_6, parent = param_7, style = 0x1000320 | -(param_8 != 0) "
          "& 0x8000), NOT a vmethod"
      % (len(sl), len(sites), len(set(f for _, f in sites)), "mov byte ptr [edx],0x0", len(callees),
         sum(1 for c in callees if not re.fullmatch(r"0x[0-9a-f]{6,8}", c)), cn),
      len(sl) == 0 and len(sites) == 90 and len(set(f for _, f in sites)) == 23
      and fieldst == [0xa78, 0xa7c] and nul == 1 and len(callees) == 10,
      "slots=%d sites=%d fns=%d fieldstores=%s nul=%d callees=%s names=%s"
      % (len(sl), len(sites), len(set(f for _, f in sites)), [hex(x) for x in fieldst], nul,
         callees, cn))

    cls = collections.Counter()
    a1map = collections.Counter()
    lit = []
    for pc, f in sites:
        ps = arg_pushes(pc)
        a1 = ps[-1] if ps else "?"
        if a1 == "0x0":
            cls["null"] += 1
        elif re.fullmatch(r"0x[0-9a-f]{6,8}", a1):
            v = int(a1, 16)
            if v < 0x660000:
                cls["imm-small"] += 1
            elif v < FILEMAP_END:
                cls["rdata-literal"] += 1
                o = v - 0x400000
                lit.append((hex(v), IMG[o:o + 48].split(b"\0")[0].decode("latin1", "replace")[:40]))
            else:
                cls["bss-buffer"] += 1
                a1map[a1] += 1
        else:
            cls["register-or-field"] += 1
    refs9120, stores9120 = census("0x997120")

    def indexed(s):
        ps = ops(s)[1]
        m = re.search(r"\[([^]]*)\]", ps[0] if ps else "")
        return bool(m and re.search(r"[a-z]{2,3}", m.group(1)))

    idxstores = [(pc, s) for pc, s in stores9120 if indexed(s)]
    clears = sum(1 for pc, s in stores9120 if s == "mov byte ptr ds:0x997120,0x0")
    feeders = collections.Counter()
    for pc, s in NORM:
        if s != "push 0x997120":
            continue
        f = fnof(pc)
        if f not in IDXMAP:
            feeders["outside-any-function"] += 1
            continue
        a, z = IDXMAP[f]
        i = POS[pc] + 1
        while i < len(PCS) and PCS[i] < a + z:
            if NM[PCS[i]].startswith("call "):
                t = NM[PCS[i]][5:]
                feeders[name_of(int(t, 16)) if re.fullmatch(r"0x[0-9a-f]{6,8}", t)
                        else "indirect " + t] += 1
                break
            i += 1
    pushn = sum(1 for pc, s in NORM if s == "push 0x997120")
    G(ok, "WHERE THE LABEL TEXT COMES FROM: the %d sites' label argument is %s; the BSS buffer pushed as "
          "a label is ONE address (%s). It is a GLOBAL SCRATCH TEXT BUFFER, not an array: %d refs and %d "
          "stores of any width image-wide, of which %d are INDEXED (`[reg*4+0x997120]` - the code only "
          "ever uses the base address) and %d are the base-clear `mov byte ptr ds:0x997120,0x0`; %d of "
          "the %d `push 0x997120` sites hand the buffer straight to %s, the string emitter M201-M204 "
          "named, and %d hand it to the indirect call through ds:0x671324: the row label is text "
          "FORMATTED INTO THIS GLOBAL BUFFER by the emitter, never a literal - the only literal label in "
          "the whole 90-site set is %s"
      % (sum(cls.values()), dict(cls), dict(a1map), len(refs9120), len(stores9120), len(idxstores),
         clears, feeders["FUN_0064b9e0"], pushn, feeders.most_common(1)[0][0],
         feeders["indirect dword ptr ds:0x671324"], lit),
      sum(cls.values()) == 90 and cls["null"] == 15 and cls["rdata-literal"] == 1
      and cls["bss-buffer"] == 44 and len(a1map) == 1 and list(a1map)[0] == "0x997120"
      and len(stores9120) == 668 and len(idxstores) == 0 and clears == 466
      and feeders.most_common(1)[0][0] == "FUN_0064b9e0" and feeders["FUN_0064b9e0"] > 1000
      and lit and lit[0][1].startswith("Create Session"),
      "cls=%s buffers=%s refs=%d stores=%d indexed=%d clears=%d pushes=%d feeders=%s literal=%s"
      % (dict(cls), dict(a1map), len(refs9120), len(stores9120), len(idxstores), clears, pushn,
         feeders.most_common(8), lit))
    return ok


# ---------------------------------------------------------------- M216
def m216():
    ok = []
    ins = INSTALLS.get(0x6738e4, [])
    sl_a8 = slots_of(0x43fee0)
    dc = direct_calls(0x43fee0)
    G(ok, "vtable 0x6738e4 has %d slots and %d installs (%s) and its +0xa8 IS FUN_0043fee0, which "
          "appears in exactly %d vtable slot image-wide and has %d direct call sites - reached only by "
          "dispatch on that class"
      % (VT[0x6738e4][0], VT[0x6738e4][1], ["%x in %s -> [%s]" % (pc, f, r) for pc, f, r in ins],
         len(sl_a8), len(dc)),
      VT[0x6738e4][0] == 87 and len(ins) == 2 and dw(0x6738e4 + 0xa8) == 0x43fee0
      and len(sl_a8) == 1 and len(dc) == 0,
      "slots=%d installs=%s a8-slots=%d direct=%d" % (VT[0x6738e4][0], ins, len(sl_a8), len(dc)))

    sb = slots(0x6738e4)
    comp = {}
    for a in (0x6717cc, 0x671d94, 0x67164c, 0x67194c):
        sa = slots(a)
        n = min(len(sa), len(sb))
        diff = [i * 4 for i in range(n) if sa[i] != sb[i]]
        comp["0x%x" % a] = (n - len(diff), len(sb), len(sa), diff)
    G(ok, "0x6738e4 IS a dialog-family class: it shares %d of %d slots with 0x6717cc, %d with 0x671d94, "
          "%d with 0x67164c, %d with the row 0x67194c; every differing set contains 0x0 (its own ctor), "
          "0x4c (the click dispatcher) and 0xa8 (the handle forwarder) - it is the family member that "
          "replaced the hotspot dispatcher with a global-handle forwarder"
      % (comp["0x6717cc"][0], comp["0x6717cc"][1], comp["0x671d94"][0], comp["0x67164c"][0],
         comp["0x67194c"][0]),
      all(all(x in d for x in (0x0, 0x4c, 0xa8)) for _, _, _, d in comp.values())
      and comp["0x6717cc"][0] >= 70 and comp["0x671d94"][0] >= 70,
      "share=%s" % {k: (v[0], v[1], v[2], [hex(x) for x in v[3]]) for k, v in comp.items()})

    refs, stores = census("0x9977f0")
    store_fns = sorted({name_of(pc) for pc, _ in stores})
    readers_fns = sorted({name_of(pc) for pc, s in refs if (pc, s) not in stores})
    readers = sorted({(name_of(pc), hex(pc)) for pc, s in refs if (pc, s) not in stores})
    G(ok, "the modal handle ds:0x9977f0: %d refs, %d stores (%s) - both written by ONE function (%s) - "
          "and %d loads spread over exactly %s; nothing else in the image reads it"
      % (len(refs), len(stores), [hex(pc) for pc, _ in stores], store_fns, len(refs) - len(stores),
         readers_fns),
      len(refs) == 9 and len(stores) == 2 and len(store_fns) == 1
      and set(readers_fns) <= set(store_fns) | {"FUN_0043fee0", "FUN_005d69fa", "FUN_005f5a11"}
      and "FUN_005d69fa" in readers_fns and "FUN_005f5a11" in readers_fns,
      "refs=%d stores=%s store_fns=%s readers=%s %s"
      % (len(refs), [(hex(p), s) for p, s in stores], store_fns, readers_fns, readers))

    b = body("FUN_005d69fa")
    glob = [re.search(r"ds:(0x[0-9a-f]+)", s).group(1) for pc, s in b if "ds:0x99" in s]
    pub = sum(1 for pc, s in b if s == "mov dword ptr ds:0x9939ac,ecx")
    fld = sum(1 for pc, s in b if re.match(r"^mov \w+,dword ptr \[\w+\+0xa8\]$", s))
    callers = direct_calls(0x5d69fa)
    sl69 = slots_of(0x5d69fa)
    dispatched = collections.Counter()
    for pc, f in callers:
        a, z = IDXMAP[f]
        i = POS[pc]
        while i < len(PCS) and PCS[i] < a + z:
            m = re.match(r"^call dword ptr \[\w+\+0x([0-9a-f]+)\]$", NM[PCS[i]])
            if m:
                dispatched["+0x" + m.group(1)] += 1
                break
            i += 1
    G(ok, "FUN_005d69fa (%d vtable slots, %d direct callers %s) reads %d distinct globals in the order "
          "%s: dialog-current 0x9939c4 first, and when the MODAL HANDLE ds:0x9977f0 is set IT wins; "
          "otherwise 0x9939a8 then 0x9939d0. It publishes the winner to ds:0x9939ac (%d store) and "
          "returns the object's [+0xa8] FIELD (%d load) - a DELEGATE object pointer, not a slot value - "
          "gated on FUN_005d8123; its 3 callers dispatch %s on that delegate"
      % (len(sl69), len(callers), [hex(p) for p, _ in callers], len(set(glob)), glob[:8], pub, fld,
         dict(dispatched)),
      len(sl69) == 0 and len(callers) == 3 and pub == 1 and fld == 1
      and sorted(dispatched) == ["+0x12c", "+0x130", "+0x134"] and "0x9977f0" in glob,
      "slots=%d callers=%s globals=%s pub=%d field=%d dispatch=%s"
      % (len(sl69), [hex(p) for p, _ in callers], collections.Counter(glob).most_common(8), pub, fld,
         dict(dispatched)))

    refs511 = [(pc, s) for pc, s in NORM if "5f5a11" in s]
    imms = stores_of(refs511)
    disp511 = sorted({mem_disp(d) for _, _, d in imms})
    dc511 = direct_calls(0x5f5a11)
    sl511 = slots_of(0x5f5a11)
    b = body("FUN_005f5a11")
    disps = sorted({mem_disp(p) for pc, s in b for p in ops(s)[1]
                    if mem_disp(p) is not None and "ebp" not in p})
    callslots = sorted({m.group(1) for pc, s in b
                        for m in [re.match(r"^call dword ptr \[\w+\+0x([0-9a-f]+)\]$", s)] if m})
    G(ok, "FUN_005f5a11 has %d direct call sites and %d vtable slots, yet its address appears %d times "
          "in the image, each time as an immediate stored into an object FIELD at %s - a CALLBACK "
          "installed in a field, not a vmethod. Its body treats the handle as an object (field "
          "displacements %s, incl. +0xa14 the child-dialog link and +0xa40 the pump's result field) and "
          "dispatches %s" % (len(dc511), len(sl511), len(refs511), [hex(x) for x in disp511],
                             [hex(x) for x in disps][:10], callslots),
      len(dc511) == 0 and len(sl511) == 0 and len(imms) == 3
      and disp511 == [0x2210, 0x2224, 0x2234] and 0xa14 in disps and 0xa40 in disps
      and "e0" in callslots and "8" in callslots,
      "direct=%d slots=%d imm-stores=%s refs=%s disps=%s callslots=%s"
      % (len(dc511), len(sl511), [(hex(p), s) for p, s, _ in imms], refs511, [hex(x) for x in disps],
         callslots))
    return ok


CHECKS = [("M213", m213), ("M214", m214), ("M215", m215), ("M216", m216)]
res = {}
for mid, fn in CHECKS:
    try:
        oks = fn()
    except Exception as e:
        oks = [("%s instrument error" % mid, False, repr(e))]
    for desc, passed, numbers in oks:
        res.setdefault(mid, []).append((passed, desc, numbers))
tot = sum(len(v) for v in res.values())
good = sum(1 for v in res.values() for p, _, _ in v if p)
for mid, oks in res.items():
    print("== %s ==" % mid)
    for p, desc, numbers in oks:
        print("  [%s] %s" % ("PASS" if p else "FAIL", desc))
        if PROBE or not p:
            print("        numbers: %s" % numbers)
print("SUMMARY %s (%d/%d gates)" % (" ".join("%s=%s" % (m, "PASS" if all(p for p, _, _ in v) else "FAIL")
                                             for m, v in res.items()), good, tot))
sys.exit(0 if good == tot and tot == 17 else 1)
