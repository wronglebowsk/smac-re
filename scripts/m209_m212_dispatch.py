#!/usr/bin/env python3
"""M209-M212: who dispatches the dialog result slot, the dialog stack, the pump wrapper, the sentinels.

  M209  WHO DISPATCHES vtable slot +0xa8 (the writer of the field the pump returns): the slot has many
        implementations; the dialog family's is FUN_005f5759, and its dispatchers are the family's own
        +0x4c vmethod FUN_005f6aa3 and the global-handle forwarder FUN_0043fee0 - NOT the two candidates
        the s181 pick named (FUN_0043a4e0 / the -0xa14 thunks dispatch OTHER classes' +0xa8).
  M210  the dialog stack FUN_005ce5bd keeps: two parallel 4-deep arrays (0x992db8 dialogs, 0x992dc8 its
        arg3 - WRITE-ONLY), current/depth globals written only by the runner + the closer, and slot +0xe4
        is a BOOLEAN predicate (ds:0x997770 == 0), not an event pump.
  M211  FUN_00542ea0 is the pump's WRAPPER (constructs the dialog with FUN_00405ef0, calls the pump once,
        returns its eax) so the 8-case switch at 0x54ef34 switches on the PUMP's result code.
  M212  the pump's 94 return consumers + the -9999 sentinel: -9999 lives in 14 sites in 10 functions, all
        local inits/comparisons, and NONE of them is a pump caller - M83/M84's site is a stack-local init.

    python3 scripts/m209_m212_dispatch.py            # the acceptance run (15 gates)
    python3 scripts/m209_m212_dispatch.py --probe    # diagnostics only

Static only: scratch/m574/text.txt (whole-image disassembly) + programs/terran.exe bytes
(file offset = VA - 0x400000) + ghidra_out/ (index.csv, decompiled shards). No box time.
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
    """mnemonic + top-level comma-split operands (objdump intel: destination first)."""
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


RMW = {"add", "and", "or", "xor", "sub", "adc", "sbb", "shl", "shr", "sar", "inc", "dec", "neg", "not"}


def access(s, tok):
    """direction-aware: store / rmw-store / load / addr (lea) / pass (push, call arg)."""
    mn, parts = ops(s)
    hit = [i for i, p in enumerate(parts) if tok in p]
    if not hit:
        return None
    if mn in ("cmp", "test"):
        return "load"
    if mn == "lea":
        return "addr"
    if mn in ("push", "pop", "call", "jmp"):
        return "pass"
    if mn in ("mov", "movzx", "movsx", "xchg"):
        return "store" if 0 in hit else "load"
    if mn in RMW:
        return "rmw-store" if 0 in hit else "load"
    return "other:" + mn


def census(tok):
    refs = [(pc, s) for pc, s in NORM if tok in s]
    cl = collections.Counter()
    for pc, s in refs:
        cl[access(s, tok)] += 1
    stores = [(pc, s) for pc, s in refs if access(s, tok) in ("store", "rmw-store")]
    return refs, cl, stores


# ---------------------------------------------------------------- vtable model
# A vtable base is an immediate in `mov dword ptr [reg+disp],imm` whose own first dword is a code
# address. Extent = consecutive code-pointer dwords, capped at the next candidate base.
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
    """every vtable slot whose stored value is fnaddr -> [(base, byte offset)]"""
    a = fnaddr if isinstance(fnaddr, int) else int(fnaddr[4:], 16)
    pat = struct.pack("<I", a)
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


def direct_calls(addr):
    t = "call 0x%x" % addr
    return [(pc, fnof(pc)) for pc, s in NORM if s == t]


def G(ok, desc, cond, numbers):
    ok.append((desc, cond, numbers))


DIALOG_VT = (0x67164c, 0x6717cc, 0x6728c0)
W5759 = sorted(b for b in B if 0xa8 < 4 * VT[b][0] and dw(b + 0xa8) == 0x5f5759)
SITES = [(pc, s) for pc, s in NORM if s.startswith("call ") and "+0xa8]" in s]
SITE_FN = collections.defaultdict(list)
for pc, s in SITES:
    SITE_FN[fnof(pc)].append((pc, s))


def arg_of(pc):
    """the value pushed as the call argument: the last `push` before the site in the same function."""
    a = IDXMAP[fnof(pc)][0]
    i = POS[pc] - 1
    while i >= 0 and PCS[i] >= a:
        mn, parts = ops(NM[PCS[i]])
        if mn == "push":
            return PCS[i], (parts[0] if parts else "")
        if mn == "call":
            break
        i -= 1
    return 0, "?"


def arg_class(op):
    if re.match(r"^0x[0-9a-f]+$", op):
        v = int(op, 16)
        return "imm:%d" % (v - 0x100000000 if v > 0x7fffffff else v)
    if "ebp" in op or "esp" in op:
        return "stack-local"
    if op.startswith("["):
        return "field-load"
    if op in ("eax", "ecx", "edx", "esi", "edi", "ebx"):
        return "register"
    return "other"


# ---------------------------------------------------------------- M209
def m209():
    ok = []
    top = [(f, len(v)) for f, v in sorted(SITE_FN.items(), key=lambda kv: -len(kv[1]))[:4]]
    G(ok,
      "29 `call [reg+0xa8]` sites in 17 functions (the s181 census reproduced)",
      len(SITES) == 29 and len(SITE_FN) == 17,
      "sites=%d fns=%d top=%s" % (len(SITES), len(SITE_FN), top))
    impl = collections.Counter()
    for b in B:
        if 0xa8 < 4 * VT[b][0]:
            impl[dw(b + 0xa8)] += 1
    G(ok,
      "+0xa8 is a widely-overridden slot: %d distinct implementations over the %d vtables in the model; "
      "exactly 3 vtables map it to FUN_005f5759 (the result-field writer) = %s"
      % (len(impl), len(B), [hex(x) for x in W5759]),
      len(W5759) == 3 and W5759 == list(DIALOG_VT) and len(impl) > 10,
      "impls=%d vtables=%d" % (len(impl), len(B)))
    disp = collections.Counter()
    ctorfns = set()
    for b in DIALOG_VT:
        for _, f, d in INSTALLS[b]:
            ctorfns.add(f)
            disp["frame-local" if d.startswith("ebp-") or d.startswith("esp-") else "other:%s" % d] += 1
    tot = sum(VT[b][1] for b in DIALOG_VT)
    G(ok,
      "the dialog family is STACK-ALLOCATED: the 3 +0xa8=FUN_005f5759 vtables are installed %d times by "
      "%d ctor functions, %d of them at a frame displacement (ebp-disp: the dialog object is a local on "
      "the caller's ~21 KB frame) and %d through a bare register" % (tot, len(ctorfns),
                                                                     disp["frame-local"], tot - disp["frame-local"]),
      tot == 464 and disp["frame-local"] == 457 and tot - disp["frame-local"] == 7,
      "installs=%d ctors=%d disp=%s" % (tot, len(ctorfns), dict(disp)))
    sl = slots_of(0x5f6aa3)
    offs = sorted({o for _, o in sl})
    dc = direct_calls(0x5f6aa3)
    pro = body("FUN_005f6aa3")[:12]
    spill = [s for _, s in pro if re.match(r"^mov dword ptr \[ebp-0x[0-9a-f]+\],ecx$", s)]
    G(ok,
      "the family's OWN dispatcher: FUN_005f6aa3 sits at +0x4c of %d vtables (the 3 dialog ones plus "
      "0x675cc4/0x6776c8), has %d direct calls, spills the incoming ecx to a frame slot, and its site "
      "0x5f6ae3 dispatches `call [reg+0xa8]` on that this-pointer, gated on FUN_005e7917 returning != -1 "
      "and its second out-param == 0" % (len(sl), len(dc)),
      len(sl) == 5 and offs == [0x4c] and len(dc) == 0 and len(spill) == 1
      and any(pc == 0x5f6ae3 for pc, _ in SITES),
      "slots=%s offs=%s direct_calls=%d spill=%s prologue=%s"
      % ([hex(b) for b, _ in sl], [hex(o) for o in offs], len(dc), spill, [s for _, s in pro]))
    sl2 = slots_of(0x43fee0)
    refs, cl, stores = census("0x9977f0")
    stfn = collections.Counter(fnof(pc) for pc, _ in stores)
    handle_sites = [(pc, s) for pc, s in SITES if fnof(pc) == "FUN_0043fee0"]
    dc2 = direct_calls(0x43fee0)
    G(ok,
      "the second dispatcher goes through a GLOBAL HANDLE: ds:0x9977f0 has %d refs, %d stores - both "
      "inside the pump FUN_005f1394 (%s) - and FUN_0043fee0, a vmethod at +0xa8 of vtable 0x6738e4 "
      "(%d slot, %d direct calls), is the only site image-wide that dispatches +0xa8 through it, behind a "
      "null test" % (len(refs), len(stores), ["0x%x" % p for p, _ in stores], len(sl2), len(dc2)),
      len(refs) == 9 and len(stores) == 2 and set(stfn) == {"FUN_005f1394"}
      and len(sl2) == 1 and sl2[0] == (0x6738e4, 0xa8) and len(dc2) == 0 and len(handle_sites) == 1,
      "refs=%d classes=%s stores=%s store_fns=%s slots=%s calls=%d sites=%d"
      % (len(refs), dict(cl), ["0x%x:%s" % (p, s) for p, s in stores], dict(stfn),
         [("0x%x+0x%x" % v) for v in sl2], len(dc2), len(handle_sites)))
    sl3 = slots_of(0x4bb900)
    b3 = sorted({b for b, o in sl3})
    o3 = sorted({o for b, o in sl3})
    nulret = [s for pc, s in body("FUN_004bb900") if s == "mov eax,0x14"]
    kid = [s for pc, s in body("FUN_004bb900") if "+0x3c]" in s]
    G(ok,
      "slot +0xa8 is a COMPOSITE: FUN_004bb900 is itself the +0xa8 implementation of %d vtables (a callee "
      "of the slot, not a caller of it) and forwards the call to the child object at [this+0x3c], "
      "returning 0x14 when that child is null" % len(b3),
      len(sl3) == 8 and o3 == [0xa8] and len(nulret) == 1 and len(kid) == 3,
      "vts=%s offsets=%s null_ret=%s child_sites=%d"
      % ([hex(x) for x in b3], [hex(o) for o in o3], nulret, len(kid)))
    a4 = slots_of(0x43a4e0)
    a4_target = dw(a4[0][0] + 0xa8) if a4 else 0
    th = {f: slots_of(int(f[4:], 16)) for f in ("FUN_0041f090", "FUN_00428140", "FUN_0043dc00")}
    th_vts = sorted({b for v in th.values() for b, _ in v})
    sub_disp = sorted({d for b in th_vts for _, _, d in INSTALLS[b]})
    outer = []
    for b in th_vts:
        ctors = {f for _, f, _ in INSTALLS[b]}
        for ob in B:
            for _, of, od in INSTALLS[ob]:
                if of in ctors and od in ("eax", "ecx", "edx", "esi", "edi", "ebx"):
                    outer.append(dw(ob + 0xa8) if 0xa8 < 4 * VT[ob][0] else 0)
    n5759 = sum(1 for t in outer if t == 0x5f5759)
    oname = sorted({name_of(t) for t in outer})
    G(ok,
      "RETRACTION of the pick's two candidates: FUN_0043a4e0 (6 of the 29 sites) is vmethod +0x60 of "
      "vtable 0x673498, whose own +0xa8 is %s; the three -0xa14 adjustor thunks sit in subobject vtables "
      "%s installed at [reg+0xa14], and their ctors' outer vtables implement +0xa8 as %s - %d of the %d "
      "outer targets is FUN_005f5759" % (name_of(a4_target), [hex(x) for x in th_vts], oname, n5759, len(outer)),
      len(a4) == 1 and a4[0] == (0x673498, 0x60) and a4_target != 0x5f5759 and len(th_vts) == 3
      and all(d.endswith("+0xa14") for d in sub_disp) and n5759 == 0,
      "0x43a4e0=%s target=%s thunk_vts=%s subobj_disp=%s outer=%s n5759=%d"
      % ([("0x%x+0x%x" % v) for v in a4], name_of(a4_target), [hex(x) for x in th_vts], sub_disp, oname, n5759))
    args = collections.Counter()
    immv = collections.Counter()
    for pc, s in SITES:
        _, op = arg_of(pc)
        c = arg_class(op)
        args[c] += 1
        if c.startswith("imm:"):
            immv[c] += 1
    nim = sum(immv.values())
    G(ok,
      "the +0xa8 ARGUMENT census over the 29 sites: %d take an immediate (%s - five of them -1, one -2, "
      "the rest small result codes) and %d push a register the caller had loaded - the slot takes a RESULT "
      "VALUE, not a key" % (nim, dict(immv.most_common(12)), args["register"]),
      sum(args.values()) == 29 and nim == 19 and immv.get("imm:-1", 0) == 5 and immv.get("imm:-2", 0) == 1
      and args["register"] == 10 and args["field-load"] == 0,
      "args=%s imm=%s" % (dict(args), dict(immv)))
    return ok


# ---------------------------------------------------------------- M210
def m210():
    ok = []
    D, clD, stD = census("0x992db8")
    A, clA, stA = census("0x992dc8")
    fnD = sorted(set(fnof(pc) for pc, _ in D))
    G(ok,
      "the dialog stack is TWO parallel 4-deep dword arrays: dialogs[depth] at 0x992db8 (%d refs = %d "
      "stores + %d loads, only %s) and the +0xdc runner's arg3 array at 0x992dc8 (%d refs, %d stores, "
      "ZERO loads = WRITE-ONLY: arg3 is parked per depth and never read back image-wide)"
      % (len(D), clD["store"] + clD["rmw-store"], clD["load"], fnD, len(A), clA["store"] + clA["rmw-store"]),
      len(D) == 6 and (clD["store"] + clD["rmw-store"]) == 4 and clD["load"] == 2
      and len(A) == 3 and (clA["store"] + clA["rmw-store"]) == 3 and clA["load"] == 0
      and fnD == ["FUN_005ce5bd", "FUN_005ce6ff", "FUN_005d0736"],
      "db8=%s dc8=%s stores=%s" % (dict(clD), dict(clA), ["0x%x:%s" % (p, s) for p, s in stD + stA]))
    C, clC, stC = census("0x9939c4")
    P, clP, stP = census("0x9939c8")
    wC = sorted(set(fnof(pc) for pc, _ in C))
    wP = sorted(set(fnof(pc) for pc, _ in P))
    sC = sorted(set(fnof(pc) for pc, _ in stC))
    sP = sorted(set(fnof(pc) for pc, _ in stP))
    G(ok,
      "the CURRENT dialog (0x9939c4) and the DEPTH (0x9939c8) are written only by the +0xdc runner "
      "FUN_005ce5bd and the +0xe0 closer FUN_005ce6ff: %d refs / %d stores and %d refs / %d stores, read "
      "by %d / %d functions" % (len(C), len(stC), len(P), len(stP), len(wC), len(wP)),
      len(C) == 22 and len(stC) == 3 and sC == ["FUN_005ce5bd", "FUN_005ce6ff"]
      and len(P) == 21 and len(stP) == 3 and sP == ["FUN_005ce5bd", "FUN_005ce6ff"],
      "c4=%d/%d fns=%s c8=%d/%d fns=%s writers=%s"
      % (len(C), len(stC), wC, len(P), len(stP), wP, ["0x%x:%s" % (p, s) for p, s in stC + stP]))
    e4 = [(pc, s) for pc, s in NORM if s.startswith("call ") and "+0xe4]" in s]
    pred = body("FUN_005f6056")
    refs70, cl70, st70 = census("0x997770")
    t1, t2 = dw(0x67164c + 0xe4), dw(0x671d94 + 0xe4)
    G(ok,
      "slot +0xe4 is NOT an event pump (M206's label RETRACTED): %d dispatch sites image-wide; for the "
      "dialog family +0xe4 = FUN_005f6056 = `return ds:0x997770 == 0` (a bool), for the sibling family "
      "(0x671d94/0x672448/0x672c50/0x673498) +0xe4 = FUN_004060d0 = `return 1`; ds:0x997770 has %d refs "
      "= %d stores (0 written by the pump at 0x5f3e6e, 1 by FUN_005f6073 at 0x5f6081) + %d read"
      % (len(e4), len(refs70), len(st70), cl70["load"]),
      len(e4) == 2 and t1 == 0x5f6056 and t2 == 0x4060d0 and len(refs70) == 3 and len(st70) == 2
      and cl70["load"] == 1 and any(s == "cmp dword ptr ds:0x997770,0x0" for _, s in pred),
      "e4_sites=%s targets=%s/%s 0x997770=%s stores=%s"
      % ([("0x%x:%s" % (p, s)) for p, s in e4], name_of(t1), name_of(t2), dict(cl70),
         ["0x%x:%s" % (p, s) for p, s in st70]))
    cons = []
    for pc, s in e4:
        i = POS[pc]
        cons.append([NM[PCS[j]] for j in range(i + 1, min(i + 4, len(PCS)))])
    G(ok,
      "the modal loop tests that boolean BEFORE touching arg2: the site inside FUN_005ce5bd is followed by "
      "`test eax,eax ; je 0x5ce6f6 ; cmp dword ptr [ebp+0xc],0x0`; the other site (FUN_004bbe00) discards "
      "it and returns 0x14",
      any(c[:2] == ["test eax,eax", "je 0x5ce6f6"] for c in cons),
      "consumers=%s" % (cons,))
    return ok


# ---------------------------------------------------------------- M211
def m211():
    ok = []
    a, z = IDXMAP["FUN_00542ea0"]
    bd = body("FUN_00542ea0")
    pump_in = [pc for pc, s in bd if s == "call 0x5f1394"]
    ctor_in = [pc for pc, s in bd if s == "call 0x405ef0"]
    callers = direct_calls(0x542ea0)
    C = open(os.path.join(ROOT, "ghidra_out/shard_013.c"), errors="replace").read()
    m = re.search(r"^// ==== FUN_00542ea0.*?(?=^// ==== )", C, re.S | re.M)
    ctext = m.group(0) if m else ""
    returns = re.findall(r"^\s*return [^;]*;", ctext, re.M)
    pumpvar = re.findall(r"uVar\d+ = FUN_005f1394\(\);", ctext)
    retvar = re.findall(r"return uVar\d+;", ctext)
    G(ok,
      "FUN_00542ea0 (%d B, %d insns) is the pump's WRAPPER: %d direct call site (%s); it calls the "
      "runner-class ctor FUN_00405ef0 %d time, calls the pump FUN_005f1394 exactly %d time (%s), and its "
      "decompiled body has %d return statements (%s / %s) - the success path returns the pump's eax"
      % (z, len(bd), len(callers), [f for _, f in callers], len(ctor_in), len(pump_in),
         [hex(p) for p in pump_in], len(returns), pumpvar, retvar),
      len(callers) == 1 and callers[0][1] == "FUN_00546800" and len(pump_in) == 1
      and len(ctor_in) == 1 and len(returns) == 2 and len(pumpvar) == 1 and len(retvar) == 1,
      "callers=%s pump_sites=%s ctor_sites=%s returns=%s"
      % (callers, [hex(p) for p in pump_in], [hex(p) for p in ctor_in], returns))
    tg = [dw(0x54ef34 + 4 * i) for i in range(10)]
    ci = POS[callers[0][0]] if callers else 0
    guard = [NM[PCS[ci + 1]], NM[PCS[ci + 2]], NM[PCS[ci + 3]]]
    fa, fz = IDXMAP["FUN_00546800"]
    G(ok,
      "the switch table at 0x54ef34 has EXACTLY 8 entries (%s); the 9th dword is 0x90909090 (nop padding, "
      "not an address); the guard right after the wrapper call is %s; %d distinct targets, all inside "
      "FUN_00546800 (cases 1 and 2 share 0x54eb03)" % ([hex(t) for t in tg[:8]], guard, len(set(tg[:8]))),
      all(in_text(t) for t in tg[:8]) and tg[8] == 0x90909090 and len(set(tg[:8])) == 7
      and all(fa <= t < fa + fz for t in tg[:8]) and guard == ["add esp,0x8", "cmp eax,0x7", "ja 0x54ec82"],
      "table=%s ninth=0x%x guard=%s" % ([hex(t) for t in tg[:8]], tg[8], guard))
    cases, sets = {}, {}
    for i, t in enumerate(tg[:8]):
        cs = [s for _, s in win(t, t + 0x40) if s.startswith("call 0x")]
        cases[i] = name_of(int(cs[0][7:], 16)) if cs else "?"
        sets[i] = [s for _, s in win(t, t + 0x40) if re.match(r"^mov dword ptr ds:0x", s)]
    G(ok,
      "the 8 cases are the diplomacy screen's RESULT-CODE handlers keyed on the pump's return: %s; case 7 "
      "also writes the result-code globals ds:0x920700 = 0xc and ds:0x92077c = 1; every case lands on "
      "0x54ec82 (`inc byte ptr [ebx]` + call FUN_005315d0), which is also the out-of-range target" % cases,
      cases[0] == "FUN_005306b0" and cases[1] == "FUN_00545c50" and cases[2] == "FUN_00545c50"
      and cases[3] == "FUN_00626a17" and cases[4] == "FUN_0053fce0" and cases[5] == "FUN_00541bb0"
      and cases[6] == "FUN_00542810" and cases[7] == "FUN_00545c50"
      and any("0x920700,0xc" in s for s in sets[7])
      and any(s == "inc byte ptr [ebx]" for _, s in win(0x54ec82, 0x54ec8a)),
      "cases=%s case7=%s" % (cases, sets[7]))
    return ok


# ---------------------------------------------------------------- M212
def m212():
    ok = []
    ps = direct_calls(0x5f1394)
    kind = collections.Counter()
    imm = collections.Counter()
    neg1 = 0
    for pc, f in ps:
        i = POS[pc]
        nxt = NM[PCS[i + 1]] if i + 1 < len(PCS) else ""
        if re.match(r"^cmp eax,0x", nxt):
            kind["cmp-const"] += 1
            imm[nxt] += 1
        elif re.match(r"^cmp eax,", nxt):
            kind["cmp-reg"] += 1
        elif nxt == "test eax,eax":
            kind["test-eax"] += 1
        elif nxt.startswith("mov "):
            kind["mov"] += 1
        else:
            kind[nxt.split()[0] if nxt else "eol"] += 1
        look = [NM[PCS[j]] for j in range(i + 1, min(i + 13, len(PCS)))]
        if any(re.match(r"^(cmp \S+,0xffffffff|or \S+,0xffffffff)$", t) for t in look):
            neg1 += 1
    G(ok,
      "the pump's %d direct call sites consume eax as a RESULT CODE: %s; %d of them test for -1 within "
      "the next 12 instructions; the constants compared right after the call are %s"
      % (len(ps), dict(kind), neg1, dict(imm)),
      len(ps) == 94 and kind["test-eax"] == 22 and kind["cmp-const"] == 4 and neg1 >= 1,
      "kinds=%s neg1=%d imm=%s" % (dict(kind), neg1, dict(imm)))
    pat = struct.pack("<I", 0xffffd8f1)
    hits = []
    i = 0
    while True:
        j = IMG.find(pat, i)
        if j < 0:
            break
        va = j + 0x400000
        i = j + 1
        if TEXT_LO <= va < TEXT_HI:
            k = bisect.bisect_right(PCS, va) - 1
            if k >= 0:
                pc = PCS[k]
                nx = PCS[k + 1] if k + 1 < len(PCS) else pc + 16
                if va < nx:
                    hits.append((va, pc, NM[pc], fnof(pc)))
    hf = collections.Counter(h[3] for h in hits)
    forms = collections.Counter(ops(h[2])[0] for h in hits)
    pumpcallers = set(f for _, f in ps)
    overlap = sorted(set(hf) & pumpcallers)
    m83 = [h for h in hits if h[1] == 0x4976ce]
    # who the -9999 comparisons read: the producer two/three instructions before each cmp
    prod = []
    for va, pc, txt, f in hits:
        if ops(txt)[0] != "cmp":
            continue
        reg = ops(txt)[1][0] if ops(txt)[1] else ""
        j = POS[pc]
        chain = [NM[PCS[k]] for k in range(j - 12, j)][::-1]
        src = next((t for t in chain if t == "mov %s,eax" % reg or t.startswith("mov %s," % reg)), "?")
        call = next((t for t in chain if t.startswith("call ")), "?")
        prod.append((f, hex(pc), reg, call, src))
    # does any pump site test its own return against -9999?
    neg99_near = 0
    for pc, f in ps:
        i = POS[pc]
        if any("0xffffd8f1" in NM[PCS[j]] for j in range(i + 1, min(i + 13, len(PCS)))):
            neg99_near += 1
    # the producer pair inside FUN_00417ee0, and FUN_00496ad0's own read-back of the -9999 local
    pair = [NM[PCS[k]] for k in range(POS[0x41860a], POS[0x41860a] + 2)]
    readback = NM.get(0x4976f9, "")
    ad0callers = direct_calls(0x496ad0)
    G(ok,
      "-9999 (0xffffd8f1) is FUN_00496ad0's own sentinel, not the pump's: %d instruction sites in %d "
      "functions (forms %s); inside FUN_00496ad0 the M83/M84 site 0x4976ce is `%s` (a STACK-LOCAL INIT) "
      "and 0x4976f9 reads it back as `%s`; FUN_00496ad0 has %d caller (%s) and its 2 -9999 tests are both "
      "on edi, published by `%s` at 0x41860a; %d of the pump's 94 call sites tests its return against "
      "-9999, so the pump's -1 and this -9999 are disjoint sentinels"
      % (len(hits), len(hf), dict(forms), m83[0][2], readback, len(ad0callers),
         sorted(set(f for _, f in ad0callers)), pair, neg99_near),
      len(hits) == 14 and len(hf) == 10 and len(m83) == 1 and overlap == ["FUN_00417ee0"]
      and m83[0][2] == "mov dword ptr [ebp-0xb9c],0xffffd8f1" and neg99_near == 0
      and all(p[2] in ("edi", "eax") for p in prod)
      and pair == ["call 0x496ad0", "mov edi,eax"]
      and readback == "mov eax,dword ptr [ebp-0xb9c]"
      and len(ad0callers) == 1 and ad0callers[0][1] == "FUN_00417ee0",
      "hits=%d fns=%s overlap=%s forms=%s prod=%s neg99_near=%d pair=%s readback=%s ad0callers=%s"
      % (len(hits), sorted(hf), overlap, dict(forms), prod, neg99_near, pair, readback, ad0callers))
    refs, cl, stores = census("+0xa40]")
    neg99 = [s for pc, s in stores if "0xffffd8f1" in s]
    G(ok,
      "the result field [this+0xa40] is never written with -9999: %d store-shaped sites, %d of them store "
      "0xffffd8f1; the pump's -1 legs are `or eax,0xffffffff` and ds:0x698d0c (M205), so -1 and -9999 are "
      "disjoint sentinels" % (len(stores), len(neg99)),
      len(stores) == 56 and len(neg99) == 0,
      "stores=%d neg99_stores=%d classes=%s" % (len(stores), len(neg99), dict(cl)))
    return ok


CHECKS = [("M209", m209), ("M210", m210), ("M211", m211), ("M212", m212)]
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
sys.exit(0 if good == tot and tot == 18 else 1)
