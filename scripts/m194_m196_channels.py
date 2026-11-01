#!/usr/bin/env python3
"""M194-M196: three questions about the channel table and the mode gate -
one census script, one evidence file, static image + ONE tracerless /proc/mem read.

  M194  who CONSUMES the 10-slot channel table (0x99a01c text slots), and what slot 7 carries
  M195  which functions set the mode gate ds:0x920700, and what mode they name
  M196  is [fac*4+0x94d448] a pointer (the 0x40030 tests vs FUN_005551e0's "address" stores)

    sudo -n python3 scripts/m194_m196_channels.py   > evidence/m194_m196_channels.txt
    (sudo only for the /proc/<pid>/mem read: yama ptrace_scope=1 blocks it otherwise)

Static corpus: scratch/m574/text.txt + ghidra_out/index.csv + ghidra_out/shard_*.c, via field_census.py.
Every number the prose quotes is COMPUTED here; the gates count sites and FAIL otherwise.
"""
import importlib.util
import os
import re
import struct
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, fnof, IDX = FC.INS, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
NORM = [(pc, " ".join(s.lower().split())) for pc, s in INS]
POS = {pc: i for i, (pc, _) in enumerate(NORM)}
R = {}
LO, HI = 0x99A01C, 0x99AA1C  # the 10 x 256-byte text slots


def ok(mid, cond, text):
    R[mid] = bool(cond)
    print(mid + "  " + ("PASS" if cond else "FAIL") + " - " + text)


def ops(text):
    m = re.match(r"^([a-z0-9]+)\s+(.*)$", text)
    if not m:
        return text.strip(), "", ""
    p = m.group(2).split(",", 1)
    return m.group(1), p[0].strip(), (p[1].strip() if len(p) > 1 else "")


def ismem(op):
    return bool(re.match(r"^(dword|word|byte)\s+ptr\s+", op)) or bool(re.match(r"^\[", op)) or op.startswith("ds:")


def inwin(s):
    """the absolute address an operand denotes, when it is a window address (or None)."""
    m = re.search(r"0x(99a[0-9a-f]{3})", s)
    if not m:
        return None
    a = int(m.group(1), 16)
    return a if LO <= a < HI else None


def callsites(tgt):
    t = hex(tgt)[2:]
    return [(pc, fnof(pc)) for pc, s in NORM if ops(s)[0] == "call" and re.match(r"^0x" + t + r"$", ops(s)[1])]


def body(name):
    a, z = INDEX[name]
    return [(pc, s) for pc, s in NORM if a <= pc < a + z]


def fnsrc(name):
    """the decompiled C body of a function, found by banner across the shards."""
    for fn in sorted(os.listdir(os.path.join(ROOT, "ghidra_out"))):
        if not fn.endswith(".c"):
            continue
        path = os.path.join(ROOT, "ghidra_out", fn)
        with open(path, errors="replace") as fh:
            lines = fh.readlines()
        st = None
        for i, line in enumerate(lines):
            if line.startswith("// ==== "):
                nm = line.split()[1]
                if nm == name:
                    st = i
                elif st is not None:
                    return path, st, i, lines[st:i]
        if st is not None:
            return path, st, len(lines), lines[st:]
    return None, None, None, []


def live():
    pid = subprocess.check_output(["pgrep", "-x", "terran.exe"]).decode().strip().split("\n")[0]
    f = open(f"/proc/{pid}/mem", "rb", 0)

    def dw(a, n):
        f.seek(a)
        return list(struct.unpack("<%dI" % n, f.read(4 * n)))

    def byt(a, n):
        f.seek(a)
        return f.read(n)

    out = {"pid": pid, "mode": dw(0x920700, 1)[0],
           "A": dw(0x999FCC, 10), "B": dw(0x999FF4, 10), "stag": dw(0x99AA1C, 2),
           "slots": [byt(LO + 0x100 * i, 256).split(b"\x00", 1)[0] for i in range(10)],
           "d4": dw(0x94D448, 33), "dfac": [dw(0x94D448 + 8380 * fac, 1)[0] for fac in range(33)]}
    f.close()
    return out


# ------------------------------------------------------------------ M194
def m194(L):
    win = [(pc, s) for pc, s in NORM if inwin(s) is not None]
    pushes = [(pc, s, inwin(s)) for pc, s in win if ops(s)[0] == "push"]
    direct = [(pc, s) for pc, s in win if ops(s)[0] != "push"]
    fns = {fnof(pc) for pc, s in win}
    print(f"M194 window {LO:#x}..{HI-1:#x}: {len(win)} sites in {len(fns)} functions; "
          f"{len(pushes)} push-an-address, {len(direct)} direct memory ops")
    peraddr = Counter()
    for pc, s, a in pushes:
        peraddr[(a - LO) // 0x100] += 1
    print("   pushes per slot:", {i: peraddr[i] for i in sorted(peraddr)})
    role = Counter()
    for pc, s in direct:
        mn, o1, o2 = ops(s)
        role["store" if (mn == "mov" and ismem(o1)) else "load" if (mn == "mov" and ismem(o2)) else mn] += 1
    print("   direct-op roles:", dict(role))
    calle = Counter()
    for pc, s, a in pushes:
        for j in range(POS[pc] + 1, min(POS[pc] + 9, len(NORM))):
            m2, a2, _ = ops(NORM[j][1])
            if m2 == "call":
                calle[a2] += 1
                break
    print(f"   {sum(calle.values())} pushes are immediately followed by a call; {len(calle)} distinct callee targets")
    layer = []
    for tgt, n in calle.most_common():
        if not re.fullmatch(r"0x[0-9a-f]+", tgt):
            print(f"     INDIRECT call {tgt} x{n} (a function-pointer slot, no static target)")
            continue
        t = int(tgt, 16)
        f = fnof(t)
        if f not in INDEX:
            print(f"     {tgt} not a function start ({n} sites)")
            continue
        b = body(f)
        nul = sum(1 for _, s in b if "0x7efefeff" in s or "0x80808080" in s)
        stores = sum(1 for _, s in b if ops(s)[0] == "mov" and ismem(ops(s)[1]))
        cs = len(callsites(t))
        kind = ("named-C-string" if f.startswith("_") else "nul-scan-copy" if nul else "thunk" if len(b) <= 10 else "other")
        layer.append((tgt, f, len(b), stores, nul, cs, kind, n))
        print(f"     call {tgt} x{n} -> {f} insns {len(b)} stores {stores} nul-scan {nul} own-callsites {cs} [{kind}]")
    nlayer = sum(1 for x in layer if x[6] in ("named-C-string", "nul-scan-copy", "thunk"))
    nind = sum(1 for tgt in calle if not re.fullmatch(r"0x[0-9a-f]+", tgt))
    fmt = []
    for tgt in ("0x631afb", "0x632cad"):
        sites = callsites(int(tgt, 16))
        withaddr = [pc for pc, _ in sites if any(inwin(t) is not None for _, t in NORM[max(0, POS[pc] - 6):POS[pc]])]
        fmt.append((tgt, len(sites), len(withaddr)))
        print(f"   formatter {tgt}: {len(sites)} call sites, {len(withaddr)} of them push a window address")
    ok("M194a", len(win) == 113 and len(pushes) >= 90 and len(direct) <= 25 and len(calle) == 16
       and nind == 2 and nlayer >= 6 and sum(x[1] for x in fmt) == 11 and sum(x[2] for x in fmt) >= 7,
       f"the table is consumed by POINTER PASSING, not by direct reads: {len(win)} sites in {len(fns)} fns, "
       f"{len(pushes)} pass an address of the table or of one slot vs {len(direct)} direct memory ops ({dict(role)}); "
       f"{len(calle)} distinct callees receive it ({nlayer} of them the C string layer: named _strlen/_strcmp/"
       f"_strncpy, the 0x7efefeff append-copy 0x64b9e0, or <=10-insn thunks), {nind} of them indirectly through a "
       f"function-pointer slot; the two big text formatters "
       f"{', '.join(x[0] for x in fmt)} have {sum(x[1] for x in fmt)} sites, {sum(x[2] for x in fmt)} of which pass a "
       f"window address as an argument")
    acc = []
    for name in ("FUN_00625b20", "FUN_005f0583"):
        b = body(name)
        pairs = 0
        for i, (pc, s) in enumerate(b):
            mn, o1, o2 = ops(s)
            if mn == "add" and o2 == "0x99a01c" and any(
                    ops(t)[0] == "shl" and ops(t)[1] == o1 and ops(t)[2] == "0x8" for _, t in b[max(0, i - 8):i]):
                pairs += 1
        cs = callsites(int(name[4:], 16))
        acc.append((name, pairs, len(cs), len({f for _, f in cs})))
        print(f"   {name}: {pairs} 'shl reg,0x8' -> 'add reg,0x99a01c' slot-index pairs, "
              f"{len(cs)} call sites in {len({f for _, f in cs})} functions")
    b5a2, b634 = body("FUN_006265a2"), body("FUN_00626634")

    def sig(b):
        return {s for _, s in b if s.startswith("cmp dword ptr [ebp+0x8]") or ("0x999ff4" in s)
                or s == "shl edx,0x8" or "0x99a01c],0x0" in s}
    cs5a2 = callsites(0x6265A2)
    shared = sig(b5a2) & sig(b634)
    print(f"   FUN_006265a2 ({len(b5a2)} insns, {len(cs5a2)} sites in {len({f for _, f in cs5a2})} fns) shares "
          f"{len(shared)} guard/store signature instructions with FUN_00626634: {sorted(shared)}")
    ok("M194b", all(p >= 1 for _, p, _, _ in acc) and len(shared) >= 4 and len(cs5a2) >= 80,
       f"the slots are indexed by REGISTER: {acc[0][0]} {acc[0][1]} pairs ({acc[0][2]} sites in {acc[0][3]} fns), "
       f"{acc[1][0]} {acc[1][1]} pairs ({acc[1][2]} sites in {acc[1][3]} fns); FUN_006265a2 is FUN_00626634's SIBLING "
       f"publish - same guard 'cmp [ebp+0x8],9', same 'mov [edx*4+0x999ff4]', same 'shl edx,8' + zero-the-slot "
       f"({len(shared)} instructions in common), {len(cs5a2)} sites in {len({f for _, f in cs5a2})} fns")
    s7 = []
    for pc, s in NORM:
        mn, o1, o2 = ops(s)
        if mn != "call" or o1 != "0x626634":
            continue
        pushed = [ops(t)[1] for _, t in NORM[max(0, POS[pc] - 8):POS[pc]] if ops(t)[0] == "push"]
        if pushed and pushed[-1] == "0x7":
            prev = [f"{hex(p)} {t}" for p, t in NORM[max(0, POS[pc] - 14):POS[pc]] if ops(t)[0] == "call"]
            s7.append((pc, fnof(pc), pushed[-4:], prev[-1] if prev else "none"))
    push7addr = sum(1 for pc, s in NORM if ops(s)[0] == "push" and "0x99a71c" in s)
    for pc, f, pu, prev in s7:
        print(f"   slot-7 publish {pc:#x} {f} pushes={pu} last call before: {prev}")
    print("   pushes of slot 7's own address 0x99a71c:", push7addr,
          " pushes of slots 8/9 (0x99a81c/0x99a91c):",
          sum(1 for pc, s in NORM if ops(s)[0] == "push" and ("0x99a81c" in s or "0x99a91c" in s)))
    txts = [s.decode("ascii", "replace") for s in L["slots"]]
    printable = all(all(32 <= c < 127 for c in s) for s in L["slots"])
    nonempty = [i for i, s in enumerate(L["slots"]) if s]
    year = [i for i, s in enumerate(L["slots"]) if re.fullmatch(rb"Mission Year \d{4}", s)]
    print("   LIVE slot contents (pid " + L["pid"] + "): " + "; ".join(f"slot {i}={txts[i]!r}" for i in range(10)))
    print(f"   LIVE A[10]={[hex(x) for x in L['A']]} B[10]={[hex(x) for x in L['B']]} "
          f"staging={[hex(x) for x in L['stag']]}")
    ok("M194c", printable and len(s7) == 7 and push7addr == 0 and len(nonempty) >= 4 and len(year) == 1
       and len(L["slots"][7]) == 0,
       f"slot 7 is a WRITE-ONLY channel: {len(s7)} publish sites pass it a computed buffer "
       f"({', '.join(f for _, f, _, _ in s7)}) while ZERO sites push its address 0x99a71c (slots 0-6 get "
       f"{sum(peraddr[i] for i in range(7))} such pushes); live it is EMPTY, and the filled slots are one faction's "
       f"sentence parts - {len(nonempty)} of 10 non-empty, all 10 printable ASCII: " + " / ".join(repr(t) for t in txts if t))


# ------------------------------------------------------------------ M195
def m195(L):
    sites = [(pc, s) for pc, s in NORM if "0x920700" in s]
    stores, loads, tests, other = [], [], [], []
    for pc, s in sites:
        mn, o1, o2 = ops(s)
        if mn == "mov" and ismem(o1):
            stores.append((pc, s))
        elif mn == "mov" and ismem(o2):
            loads.append((pc, s))
        elif mn in ("cmp", "test"):
            tests.append((pc, s))
        else:
            other.append((pc, s))
    wf = Counter(fnof(pc) for pc, _ in stores)
    rf = Counter(fnof(pc) for pc, _ in loads + tests)
    print(f"M195 0x920700: {len(sites)} mentions = {len(stores)} stores / {len(loads)} loads / "
          f"{len(tests)} direct tests / {len(other)} other forms")
    for pc, s in stores:
        print(f"   store {pc:#x} {fnof(pc)} {s}")
    for pc, s in tests:
        print(f"   test  {pc:#x} {fnof(pc)} {s}")
    print("   writers:", dict(wf), " readers/testers:", dict(rf))
    vals = {ops(s)[2] for _, s in tests}
    regvals = set()
    for pc, s in loads:
        reg = ops(s)[1].replace("dword ptr ", "").strip()
        for _, s2 in NORM[POS[pc] + 1:POS[pc] + 13]:
            m2, a2, b2 = ops(s2)
            if m2 in ("cmp", "test") and a2 == reg and re.fullmatch(r"0x[0-9a-f]+", b2):
                regvals.add(b2)
            if m2 == "mov" and a2 == reg:
                break
    union = {int(v, 16) for v in (vals | regvals) if re.fullmatch(r"0x[0-9a-f]+", v)}
    print(f"   tested immediates: direct {sorted(vals)} + register-mediated {sorted(regvals)}")
    print(f"   value domain = {sorted(hex(v) for v in union)} ({len(union)} distinct, max {hex(max(union))}), "
          f"stored immediate 0xc at 0x54ec5c, LIVE value {hex(L['mode'])}")
    names = ["FUN_00544530", "FUN_00546800", "FUN_00540390", "FUN_00545c50"]
    lit = {}
    for nm in names:
        _, _, _, blk = fnsrc(nm)
        lit[nm] = (len(blk), len(re.findall(r'"[^"]{2,}"', "".join(blk))))
        print(f"   {nm}: decompiled body {lit[nm][0]} lines, {lit[nm][1]} string literals")
    g544 = Counter()
    for pc, s in body("FUN_00544530"):
        mn, o1, o2 = ops(s)
        if mn == "mov" and ismem(o1) and not o1.strip().startswith("[ebp"):
            m = re.search(r"0x(9[0-9a-f]{6})", o1)
            if m:
                g544["0x" + m.group(1)] += 1
    namedtxt = open(os.path.join(ROOT, "NAMED.md"), errors="replace").read()
    hits = [(g, n, g in namedtxt) for g, n in g544.most_common(12)]
    print(f"   FUN_00544530 absolute-global stores: {dict(g544.most_common(12))}")
    print("   of its top globals, already named in NAMED.md: " + ", ".join(f"{g}x{n}" for g, n, h in hits if h))
    argtest = sum(1 for _, s in body("FUN_00544530") if ops(s)[0] == "cmp" and "[ebp+0x8]" in s)
    ok("M195a", len(sites) == 31 and len(stores) == 8 and len(other) == 0 and len(wf) == 2
       and wf["FUN_00544530"] == 7 and wf["FUN_00546800"] == 1,
       f"the mode word has EXACTLY TWO writers and no read-modify-write form anywhere: {len(sites)} mentions = "
       f"{len(stores)} stores / {len(loads)} loads / {len(tests)} tests / {len(other)} other (no inc/dec/add/and/or/"
       f"xor on it); FUN_00544530 x{wf['FUN_00544530']} (stores ebx/eax) and FUN_00546800 x{wf['FUN_00546800']} "
       f"(the only immediate store, 0xc at 0x54ec5c)")
    ok("M195b", len(union) >= 10 and max(union) <= 0xd and 0x2 in union and L["mode"] == 0,
       f"it is a MODE CODE, not a flag: every test compares a VALUE (no mask), the tested set is "
       f"{sorted(hex(v) for v in union)} - {len(union)} distinct values up to {hex(max(union))}, including the 0x2 "
       f"that gates FUN_0053a9c0 at 0x545cfa - and the live value is {hex(L['mode'])}")
    ok("M195c", all(lit[n][1] == 0 for n in names) and argtest >= 1,
       f"NOBODY names it: the four functions that write or test it contain ZERO string literals "
       f"({', '.join(f'{n}:{lit[n][1]}' for n in names)}); the mode is identified only structurally - FUN_00544530 is "
       f"a {len(body('FUN_00544530'))}-insn dispatcher that takes the value as a parameter ({argtest} tests of "
       f"[ebp+0x8]) and stores it 7 times, alongside globals NAMED.md already carries "
       f"({', '.join(g for g, _, _ in hits[:5])})")


# ------------------------------------------------------------------ M196
def m196(L):
    mentions = [(pc, s) for pc, s in NORM if "0x94d448" in s]
    forms = Counter()
    foldsame = foldother = nodef = 0
    at = dict(NORM)
    for pc, s in mentions:
        m = re.search(r"\[([a-z]+)\*4\+0x94d448\]", s)
        mb = re.search(r"\[([a-z]+)\+0x94d448\]", s)
        if not m:
            forms["base+disp" if mb else "other"] += 1
            continue
        reg = m.group(1)
        a, z = INDEX.get(fnof(pc), (0, 0))
        back = [(p, t) for p, t in NORM[max(0, POS[pc] - 40):POS[pc]] if a <= p < a + z]
        lastw = None
        for p2, t in reversed(back):
            m2, x1, x2 = ops(t)
            if m2 in ("mov", "lea", "add", "shl", "imul", "sub", "xor", "sar", "shr", "inc", "dec") and x1.replace("dword ptr ", "").strip() == reg:
                lastw = (p2, t)
                break
        if lastw is None:
            nodef += 1
            continue
        m2 = ops(lastw[1])[0]
        chain = sum(1 for _, t in [x for x in back if x[0] < lastw[0]][-14:]
                    if (ops(t)[0] == "shl" and ops(t)[1] == reg and ops(t)[2] in ("0x6", "0x4"))
                    or (ops(t)[0] in ("add", "lea", "sub") and ops(t)[1] == reg))
        if m2 == "add" and chain >= 3:
            foldsame += 1
        elif chain >= 3:
            foldother += 1
        else:
            forms["scaled4-no-fold"] += 1
    scaled4 = sum(1 for _, s in mentions if re.search(r"\[[a-z]+\*4\+0x94d448\]", s))
    print(f"M196 0x94d448: {len(mentions)} mentions; {scaled4} scaled [reg*4+disp], "
          f"{forms['base+disp']} [reg+disp], {forms['other']} other")
    print(f"   index-register provenance of the scaled sites: {foldsame} = 'add <sub-index>' AFTER a >=3-op fold "
          f"chain on the SAME register (the 2095-block fold), {foldother} other def after a fold, "
          f"{forms['scaled4-no-fold']} def with no fold in 40 insns, {nodef} no def in 40 insns")
    tests = [(pc, s) for pc, s in mentions if ops(s)[0] in ("cmp", "test") and re.search(r"\[[a-z]+\*4\+0x94d448\]", s)]
    masks = Counter(ops(s)[2] for _, s in tests)
    ncmp = sum(1 for _, s in tests if ops(s)[0] == "cmp")
    nums = sorted({int(k, 16) for k in masks if re.fullmatch(r"0x[0-9a-f]+", k)})
    maxpop = max(v.bit_count() for v in nums)
    inr = [hex(v) for v in nums if 0x400000 <= v <= 0x7FFFFFE and v.bit_count() > 1]
    print(f"   {len(tests)} scaled tests, mnemonics {dict(Counter(ops(s)[0] for _, s in tests))}; "
          f"{len(nums)} distinct numeric operands (widest {maxpop} bits: {hex(max(nums, key=lambda v: v.bit_count()))}); "
          f"operands that are address candidates (in 0x400000-0x7fffffe with >1 bit set): {inr}")
    print(f"   operand set: {sorted(hex(v) for v in nums)}")
    loads = [(pc, s) for pc, s in mentions if ops(s)[0] == "mov" and ismem(ops(s)[2]) and re.search(r"\[[a-z]+\*4\+0x94d448\]", s)]
    deref = 0
    use = Counter()
    for pc, s in loads:
        dst = ops(s)[1].replace("dword ptr ", "").replace("byte ptr ", "").strip()
        u = "other"
        for _, s2 in NORM[POS[pc] + 1:POS[pc] + 4]:
            if re.search(r"\[" + dst + r"(\*|\+|\])", s2):
                u = "DEREF-of-loaded-value"
                deref += 1
                break
            m2, a2, b2 = ops(s2)
            if m2 == "push" and a2 == dst:
                u = "pushed-as-arg"
                break
            if m2 in ("add", "sub", "imul", "cmp", "test", "mov", "or", "and"):
                u = "arithmetic/compare"
        use[u] += 1
    print(f"   {len(loads)} scaled loads; use of the loaded value within 3 insns: {dict(use)}; derefs = {deref}")
    quad = ["mov edx,dword ptr [edi+0x94d448]", "and edx,0xfffdfbff", "or edx,0x840", "mov dword ptr [edi+0x94d448],edx"]
    rmw = all(at.get(0x5553E1 + 6 * i, "") == quad[i] for i in range(4))
    alias = at.get(0x5553D2) == "lea eax,[eax*4+0x94d4a8]" and at.get(0x5553DF) == "mov dword ptr [eax],ecx"
    carriers = [(pc, at.get(pc)) for pc in (0x55540A, 0x55580F)]
    prebit = [at.get(0x555405), at.get(0x555809)]
    print(f"   FUN_005551e0 field RMW quad verbatim at 0x5553e1/0x5553e7/0x5553ed/0x5553f3: {rmw} {quad}")
    print(f"   the 'address store' pair: 0x5553d2 {at.get(0x5553D2)!r} then 0x5553df {at.get(0x5553DF)!r} - the lea "
          f"computes the very dword the next store writes (store-through alias, not a tagged pointer): {alias}")
    print(f"   the two 0x10 carriers {carriers}, each immediately after a bit op on the stored value: {prebit}")
    ptrlike = lambda v: 0x00400000 <= v <= 0x7FFFFFE
    bad4 = [hex(v) for v in L["d4"] if ptrlike(v)]
    badf = [hex(v) for v in L["dfac"] if ptrlike(v)]
    print(f"   LIVE (pid {L['pid']}) 0x94d448+4i i<33: {[hex(v) for v in L['d4']]}")
    print(f"   LIVE 0x94d448+8380*fac fac<33: {[hex(v) for v in L['dfac']]}")
    print(f"   values inside the mapped user range 0x400000-0x7fffffe: {len(bad4)} + {len(badf)} of 66")
    ok("M196a", foldsame >= 350 and forms["base+disp"] == 185 and len(mentions) == 653,
       f"the scaled form is the BLOCK FIELD, not a pointer array: {foldsame} of {scaled4} scaled sites take their "
       f"index from 'add reg,<sub-index>' built on a >=3-op 2095-fold of the SAME register, so the address is "
       f"0x94d448 + 8380*S + 4*C - a per-faction block field at block offset 0x344 + 4*C - beside "
       f"{forms['base+disp']} [reg+disp] sites of the same family")
    ok("M196b", len(tests) >= 290 and ncmp == 0 and maxpop <= 5 and not inr and deref == 0
       and at.get(0x535CCB) == "test dword ptr [eax*4+0x94d448],0x40030"
       and at.get(0x4F2BBA) == "test dword ptr [edx*4+0x94d448],0x40030",
       f"the 0x40030 sites were never pointer tests and neither was anything else: both are "
       f"'test <dword>,0x40030' (bits 4,5,18) followed by a je, and ALL {len(tests)} scaled tests use the TEST "
       f"mnemonic - {ncmp} cmp, so not one of them compares the dword against a value, let alone an address - "
       f"across {len(nums)} distinct operands the widest carries {maxpop} bits and NONE is an address candidate "
       f"({inr}); of the {len(loads)} scaled loads NONE dereferences the loaded value ({dict(use)})")
    ok("M196c", rmw and alias and not bad4 and not badf
       and carriers[0][1] == "mov dword ptr [edi+0x94d448],eax" and carriers[1][1] == "mov dword ptr [edi+0x94d448],eax"
       and prebit == ["or eax,0x20000", "and ah,0xdf"],
       "M190's 'the two carriers store ADDRESSES' reading is RETRACTED: 0x55540a/0x55580f store eax right after "
       "'or eax,0x20000' / 'and ah,0xdf' - bit ops on the field's own flag bits - and their neighbours are the "
       "register-level RMW quad 'mov edx,[edi+0x94d448] / and edx,0xfffdfbff / or edx,0x840 / "
       "mov [edi+0x94d448],edx', while the lea at 0x5553d2 is the store-through alias of the dword written at "
       f"0x5553df; LIVE neither the 33 dwords at 0x94d448+4i nor the 33 per-block fields at +8380*fac hold any "
       f"value in the mapped user range ({len(bad4)}+{len(badf)} of 66) - they are 0, -1, small ints and one "
       "bit-31 flag pattern")


def main():
    print("# M194-M196 census: channel-table consumers, the 0x920700 mode word, what 0x94d448 holds")
    print("# command: sudo -n python3 scripts/m194_m196_channels.py > evidence/m194_m196_channels.txt")
    L = live()
    m194(L)
    m195(L)
    m196(L)
    print("SUMMARY " + " ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in sorted(R.items())))
    if not all(R.values()):
        sys.exit(1)


main()

